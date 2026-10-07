from datetime import datetime, timezone
from threading import Lock
import uuid
class FeedbackStore:
    def __init__(self): self.items=[]; self.lock=Lock()
    def add(self,payload):
        record={"id":str(uuid.uuid4()),"created_at":datetime.now(timezone.utc).isoformat(),**payload}
        with self.lock: self.items.append(record)
        return {"accepted":True,"feedback_id":record["id"],"eligible_for_training":bool(record["consent_for_training"])}
class ModelRegistry:
    def list(self): return {"models":[{"id":"local-enhance-v0","status":"production","semantic_editing":False}],"policy":"validated-promotion-only"}
feedback_store=FeedbackStore(); model_registry=ModelRegistry()
