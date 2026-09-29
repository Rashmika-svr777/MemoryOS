from . import config
from .memory_store import MemoryStore
from .hindsight_client import HindsightAdapter

class MemoryService:
    """One memory brain shared by all agents: local scored store + Hindsight mirror."""
    def __init__(self, path=None):
        self.store = MemoryStore(path or config.DB_PATH, config.DECAY_HALF_LIFE_DAYS)
        self.hindsight = HindsightAdapter()

    def retain(self, agent, kind, text, tags=None, entities=None, confidence=0.5, importance=0.5, metadata=None):
        m = self.store.add(agent, kind, text, tags, entities, confidence, importance, metadata)
        m["hindsight_synced"] = self.hindsight.retain(text, context=f"{agent}/{kind}")
        return m

    def recall(self, query, agent=None, k=5, entity=None, tag=None, kinds=None):
        return self.store.search(query, agent=agent, k=k, entity=entity, tag=tag, kinds=kinds, touch=True)

    def reinforce(self, mid, success):
        return self.store.reinforce(mid, success)

    def status(self):
        return {"local": self.store.stats(), "hindsight_enabled": self.hindsight.enabled,
                "hindsight_error": self.hindsight.error}
