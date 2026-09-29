"""Local persistent memory store (SQLite, stdlib only).

Every memory has confidence, importance, reinforcement count and a decay score.
MemoryService mirrors writes to Hindsight when credentials exist, and always keeps
this store so scoring, graphing and the learning loop work with or without the cloud.
"""
import json, math, re, sqlite3, threading, time, uuid
from typing import Any

KINDS = {"episodic", "outcome", "preference", "relationship", "failure", "success", "semantic"}
STOP = set("the a an and or of to in on for with is are was were be it this that at by from as we our you your i".split())

def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]

class MemoryStore:
    def __init__(self, path: str = "memoryos.db", half_life_days: float = 60.0):
        self.half_life = half_life_days
        self._lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS memories(
            id TEXT PRIMARY KEY, agent TEXT, kind TEXT, text TEXT, tags TEXT, entities TEXT,
            confidence REAL, importance REAL, reinforcements INTEGER, created REAL, last_used REAL,
            metadata TEXT)""")
        self.db.commit()

    def add(self, agent, kind, text, tags=None, entities=None, confidence=0.5, importance=0.5,
            metadata=None, created=None) -> dict:
        if kind not in KINDS:
            raise ValueError(f"unknown memory kind: {kind}")
        now = created or time.time()
        mid = uuid.uuid4().hex[:12]
        with self._lock:
            self.db.execute("INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (mid, agent, kind, text, json.dumps(tags or []), json.dumps(entities or []),
                 confidence, importance, 0, now, now, json.dumps(metadata or {})))
            self.db.commit()
        return self.get(mid)

    def _row(self, r) -> dict:
        d = dict(r)
        for k in ("tags", "entities", "metadata"):
            d[k] = json.loads(d[k])
        d["decay"] = self.decay(d)
        return d

    def get(self, mid):
        r = self.db.execute("SELECT * FROM memories WHERE id=?", (mid,)).fetchone()
        return self._row(r) if r else None

    def delete(self, mid) -> bool:
        with self._lock:
            c = self.db.execute("DELETE FROM memories WHERE id=?", (mid,))
            self.db.commit()
        return c.rowcount > 0

    def all(self, agent=None, kind=None, limit=500) -> list[dict]:
        q, a = "SELECT * FROM memories WHERE 1=1", []
        if agent: q += " AND agent=?"; a.append(agent)
        if kind: q += " AND kind=?"; a.append(kind)
        q += " ORDER BY created DESC LIMIT ?"; a.append(limit)
        return [self._row(r) for r in self.db.execute(q, a)]

    def decay(self, m, now=None) -> float:
        """Exponential forgetting; reinforcement slows decay."""
        age_days = max(((now or time.time()) - m["last_used"]) / 86400, 0)
        half = self.half_life * (1 + 0.5 * m["reinforcements"])
        return round(0.5 ** (age_days / half), 4)

    def reinforce(self, mid, success: bool):
        m = self.get(mid)
        if not m: return None
        conf = m["confidence"]
        conf = conf + (1 - conf) * 0.25 if success else conf * 0.6
        with self._lock:
            self.db.execute("UPDATE memories SET confidence=?, reinforcements=reinforcements+1, last_used=? WHERE id=?",
                            (round(conf, 4), time.time(), mid))
            self.db.commit()
        return self.get(mid)

    def search(self, query, agent=None, kinds=None, tag=None, entity=None, k=5, touch=False) -> list[dict]:
        q = tokens(query)
        if not q and not entity and not tag: return []
        docs = self.all(limit=5000)
        df: dict[str, int] = {}
        for d in docs:
            for t in set(tokens(d["text"] + " " + " ".join(d["tags"] + d["entities"]))):
                df[t] = df.get(t, 0) + 1
        n = max(len(docs), 1)
        norm = sum(math.log(1 + n / df.get(t, 1)) for t in q) or 1
        scored = []
        for d in docs:
            if kinds and d["kind"] not in kinds: continue
            if tag and tag not in d["tags"]: continue
            if entity and entity.lower() not in [e.lower() for e in d["entities"]]: continue
            dt = set(tokens(d["text"] + " " + " ".join(d["tags"] + d["entities"])))
            rel = sum(math.log(1 + n / df[t]) for t in q if t in dt) / norm
            if q and rel == 0: continue
            rel = rel or 0.5
            own = 1.0 if (not agent or d["agent"] == agent) else 0.75  # shared brain, own-agent bias
            boost = 1.15 if d["kind"] in ("failure", "success", "outcome") else 1.0
            d["score"] = round(rel * (0.4 + 0.6 * d["confidence"]) * (0.5 + 0.5 * d["decay"])
                               * (0.6 + 0.4 * d["importance"]) * own * boost, 4)
            scored.append(d)
        scored.sort(key=lambda x: -x["score"])
        top = scored[:k]
        if touch and top:
            with self._lock:
                for d in top:
                    self.db.execute("UPDATE memories SET last_used=? WHERE id=?", (time.time(), d["id"]))
                self.db.commit()
        return top

    def stats(self) -> dict[str, Any]:
        ms = self.all(limit=100000)
        by_kind: dict[str, int] = {}; by_agent: dict[str, int] = {}
        for m in ms:
            by_kind[m["kind"]] = by_kind.get(m["kind"], 0) + 1
            by_agent[m["agent"]] = by_agent.get(m["agent"], 0) + 1
        n = len(ms)
        return {"total": n, "by_kind": by_kind, "by_agent": by_agent,
                "avg_confidence": round(sum(m["confidence"] for m in ms) / n, 3) if n else 0,
                "avg_decay": round(sum(m["decay"] for m in ms) / n, 3) if n else 0}

    def graph(self, limit=500) -> dict:
        nodes: dict[str, dict] = {}; edges: dict[tuple, int] = {}
        for m in self.all(limit=limit):
            ents = list(dict.fromkeys(m["entities"]))
            for e in ents:
                nodes.setdefault(e, {"id": e, "label": e, "weight": 0})["weight"] += 1
            for i in range(len(ents)):
                for j in range(i + 1, len(ents)):
                    key = tuple(sorted((ents[i], ents[j])))
                    edges[key] = edges.get(key, 0) + 1
        return {"nodes": list(nodes.values()),
                "edges": [{"source": a, "target": b, "weight": w} for (a, b), w in edges.items()]}
