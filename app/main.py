from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from .security import require_api_key, require_owner
from .engine import engine
from .store import feedback_store, model_registry
app=FastAPI(title="PetuAI API",version="1.0.0",description="Text-to-image generation from PetuAI")
WEB=Path(__file__).parent/"web"/"index.html"
@app.get("/",include_in_schema=False)
def web_app(): return FileResponse(WEB)
@app.get("/health")
def health(): return {"status":"ok","service":"PetuAI","version":"1.0.0","product":"text-to-image"}
class GenerateRequest(BaseModel):
    prompt:str=Field(min_length=1,max_length=32000)
@app.post("/generate",include_in_schema=False)
def generate_public(item:GenerateRequest):
    try: output=engine.generate(item.prompt)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
    return Response(content=output,media_type="image/jpeg",headers={"Cache-Control":"no-store","X-PetuAI-Backend":engine.name})
@app.post("/v1/generate",dependencies=[Depends(require_api_key)])
def generate_api(item:GenerateRequest):
    try: output=engine.generate(item.prompt)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
    return Response(content=output,media_type="image/jpeg",headers={"Cache-Control":"no-store","X-PetuAI-Backend":engine.name})
class Feedback(BaseModel):
    request_id:str=Field(min_length=1,max_length=128)
    score:int=Field(ge=1,le=5)
    correction_note:str|None=Field(default=None,max_length=2000)
    consent_for_training:bool=False
@app.post("/v1/feedback",dependencies=[Depends(require_api_key)])
def feedback(item:Feedback): return feedback_store.add(item.model_dump())
@app.get("/v1/admin/feedback",dependencies=[Depends(require_owner)])
def admin_feedback(): return {"items":feedback_store.items}
