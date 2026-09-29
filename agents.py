"""Five agents, one shared memory brain."""
import re
from dataclasses import dataclass
from . import llm
from .memory_service import MemoryService

@dataclass
class Agent:
    key: str
    name: str
    system: str
    focus_tags: list
    generic_advice: str

AGENTS = {a.key: a for a in [
    Agent("sales", "Sales Agent",
          "You are the Sales Agent. Use remembered deals, pricing, competitors, negotiations and outcomes. Cite memory IDs.",
          ["deal", "pricing", "competitor", "negotiation"],
          "No prior deal history found. Suggest a standard discovery call and list pricing."),
    Agent("support", "Support Agent",
          "You are the Support Agent. Use customer history, tickets, environment, frustration level and past resolutions. Cite memory IDs.",
          ["ticket", "customer", "resolution", "environment"],
          "No prior history for this issue. Suggest standard troubleshooting: restart, clear cache, collect logs."),
    Agent("meeting", "Meeting Agent",
          "You are the Meeting Agent. Track summaries, promises, action items, deadlines and stakeholders. Cite memory IDs.",
          ["meeting", "promise", "action-item", "deadline"],
          "No earlier meetings found. Capture attendees, decisions and action items with owners."),
    Agent("devops", "DevOps Agent",
          "You are the DevOps Agent. Use incidents, deployments, logs, root causes and runbooks. Cite memory IDs.",
          ["incident", "deployment", "runbook", "root-cause"],
          "No similar incident on record. Suggest checking recent deploys, logs and resource metrics."),
    Agent("strategy", "Strategy Agent",
          "You are the Strategy Agent. Use customer feedback, roadmap, competitor intelligence and trends. Cite memory IDs.",
          ["feedback", "roadmap", "competitor", "trend"],
          "No trend data yet. Suggest collecting feedback themes and competitor moves."),
]}

_SKIP = {"The", "This", "That", "We", "Our", "Use", "How", "What", "Why", "When", "Customer"}

def extract_entities(text: str) -> list:
    caps = re.findall(r"\b[A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)*\b", text)
    return list(dict.fromkeys(c for c in caps if len(c) > 2 and c not in _SKIP))[:8]

class AgentRuntime:
    def __init__(self, memory: MemoryService):
        self.memory = memory

    def act(self, agent_key: str, query: str, entity=None) -> dict:
        ag = AGENTS[agent_key]
        mems = self.memory.recall(query, agent=agent_key, k=5, entity=entity)
        if mems:
            ctx = "\n".join(f"[{m['id']}] ({m['kind']}, confidence {m['confidence']:.2f}) {m['text']}" for m in mems)
            answer = llm.complete(ag.system, f"Question: {query}\n\nRelevant memories:\n{ctx}\n\n"
                                  "Answer using the memories. Prefer high-confidence successes; avoid repeating failures.")
            if not answer:
                wins = [m for m in mems if m["kind"] in ("success", "outcome")]
                fails = [m for m in mems if m["kind"] == "failure"]
                lines = []
                if wins: lines.append(f"Recommended (worked before, confidence {wins[0]['confidence']:.0%}): {wins[0]['text']} [{wins[0]['id']}]")
                if fails: lines.append(f"Avoid (failed before): {fails[0]['text']} [{fails[0]['id']}]")
                if not lines: lines.append(f"Relevant context: {mems[0]['text']} [{mems[0]['id']}]")
                answer = "\n".join(lines)
        else:
            answer = llm.complete(ag.system, query) or ag.generic_advice
        inter = self.memory.retain(agent_key, "episodic", f"{ag.name} was asked: {query}",
                                   tags=ag.focus_tags[:1], entities=extract_entities(query), confidence=0.4, importance=0.3)
        return {"agent": ag.name, "answer": answer, "used_memories": [m["id"] for m in mems],
                "sources": mems, "interaction_memory": inter["id"], "memory_used": bool(mems)}

    def learn(self, agent_key: str, action: str, success: bool, note: str = "", tags=None, entities=None) -> dict:
        """Learning loop: outcome -> new success/failure memory + reinforcement of related memories."""
        kind = "success" if success else "failure"
        text = f"{'Worked' if success else 'Failed'}: {action}" + (f" - {note}" if note else "")
        related = self.memory.recall(action, agent=agent_key, k=3)
        created = self.memory.retain(agent_key, kind, text, tags=(tags or []) + [kind],
                                     entities=entities or extract_entities(action + " " + note),
                                     confidence=0.7 if success else 0.6, importance=0.8)
        reinforced = [self.memory.reinforce(m["id"], success)["id"]
                      for m in related if m["kind"] in ("success", "failure", "outcome")]
        return {"memory": created, "reinforced": reinforced}
