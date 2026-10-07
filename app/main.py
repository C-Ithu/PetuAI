from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field, EmailStr
from .security import require_api_key, require_owner
from .engine import engine
from .store import feedback_store, model_registry
from .billing import create_subscription, get_subscription

app=FastAPI(title="PetuAI API",version="0.3.0",description="Adaptive Image Intelligence for developers")
WEB=Path(__file__).parent/"web"/"index.html"
@app.get("/",include_in_schema=False)
def web_app(): return FileResponse(WEB)
@app.get("/health")
def health(): return {"status":"ok","service":"PetuAI","version":"0.3.0","billing":"mercadopago"}
class SubscribeRequest(BaseModel):
    email: EmailStr
@app.post("/billing/subscribe",include_in_schema=False)
def subscribe(item:SubscribeRequest):
    try: return create_subscription(str(item.email),"https://petuai.onrender.com/?payment=return")
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc))
@app.get("/billing/subscription/{subscription_id}",include_in_schema=False)
def subscription_status(subscription_id:str):
    try: return get_subscription(subscription_id)
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc))
@app.post("/demo/edit",include_in_schema=False)
async def demo_edit(image:UploadFile=File(...),instruction:str=Form(...)):
    try: output=engine.edit(await image.read(),instruction)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
    return Response(content=output,media_type="image/jpeg")
@app.post("/v1/edit",dependencies=[Depends(require_api_key)])
async def edit(image:UploadFile=File(...),instruction:str=Form(...)):
    try: output=engine.edit(await image.read(),instruction)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
    return Response(content=output,media_type="image/jpeg",headers={"X-PetuAI-Backend":engine.name})
@app.post("/v1/enhance",dependencies=[Depends(require_api_key)])
async def enhance(image:UploadFile=File(...)):
    try: output=engine.enhance(await image.read())
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
    return Response(content=output,media_type="image/jpeg")
class Feedback(BaseModel):
    request_id:str=Field(min_length=1,max_length=128)
    score:int=Field(ge=1,le=5)
    correction_note:str|None=Field(default=None,max_length=2000)
    consent_for_training:bool=False
@app.post("/v1/feedback",dependencies=[Depends(require_api_key)])
def feedback(item:Feedback): return feedback_store.add(item.model_dump())
@app.get("/v1/models",dependencies=[Depends(require_api_key)])
def models(): return model_registry.list()
@app.get("/v1/admin/feedback",dependencies=[Depends(require_owner)])
def admin_feedback(): return {"items":feedback_store.items}
