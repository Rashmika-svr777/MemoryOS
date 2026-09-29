"""Adapter over the official `hindsight-client` SDK (retain / recall / reflect).
Never raises: if credentials/SDK are missing or a call fails, it records why and
the local store keeps working."""
import logging
from . import config

log = logging.getLogger("memoryos.hindsight")

class HindsightAdapter:
    def __init__(self):
        self.client = None
        self.error = None
        if not config.HINDSIGHT_API_KEY and "localhost" not in config.HINDSIGHT_BASE_URL:
            self.error = "HINDSIGHT_API_KEY not set (running on local memory store)"
            return
        try:
            from hindsight_client import Hindsight
            self.client = Hindsight(base_url=config.HINDSIGHT_BASE_URL, api_key=config.HINDSIGHT_API_KEY or None)
            try:
                self.client.create_bank(bank_id=config.HINDSIGHT_BANK_ID, name="MemoryOS Company Brain")
            except Exception:  # bank may already exist
                pass
        except Exception as e:
            self.client = None
            self.error = f"Hindsight unavailable: {e}"
            log.warning(self.error)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def retain(self, content, context="") -> bool:
        if not self.enabled: return False
        try:
            self.client.retain(bank_id=config.HINDSIGHT_BANK_ID, content=content, context=context)
            return True
        except Exception as e:
            log.warning("retain failed: %s", e); return False

    def reflect(self, query):
        if not self.enabled: return None
        try:
            return self.client.reflect(bank_id=config.HINDSIGHT_BANK_ID, query=query).text
        except Exception as e:
            log.warning("reflect failed: %s", e); return None
