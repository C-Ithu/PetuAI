from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from .security import require_api_key, require_owner
from .engine import engine
from .store import feedback_store, model_registry

app = FastAPI(title="PetuAI API", version="0.2.0", description="Adaptive Image Intelligence for developers")
WEB = Path(__file__).parent / "web" / "index.html"

@app.get("/", include_in_schema=False)
def web_app(): return FileResponse(WEB)

@app.get("/health")
def health(): return {"status":"ok","service":"PetuAI","version":"0.2.0"}

@app.post("/demo/edit", include_in_schema=False)
async def demo_edit(image: UploadFile=File(...), instruction: str=Form(...)):
    try: output=engine.edit(await image.read(), instruction)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))
    return Response(content=output, media_type="image/jpeg")

@app.post("/v1/edit", dependencies=[Depends(require_api_key)])
async def edit(image: UploadFile=File(...), instruction: str=Form(...)):
    try: output=engine.edit(await image.read(), instruction)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))
    return Response(content=output, media_type="image/jpeg", headers={"X-PetuAI-Backend":engine.name})

@app.post("/v1/enhance", dependencies=[Depends(require_api_key)])
async def enhance(image: UploadFile=File(...)):
    try: output=engine.enhance(await image.read())
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))
    return Response(content=output, media_type="image/jpeg")

class Feedback(BaseModel):
    request_id: str = Field(min_length=1,max_length=128)
    score: int = Field(ge=1,le=5)
    correction_note: str|None = Field(default=None,max_length=2000)
    consent_for_training: bool=False

@app.post("/v1/feedback", dependencies=[Depends(require_api_key)])
def feedback(item: Feedback): return feedback_store.add(item.model_dump())

@app.get("/v1/models", dependencies=[Depends(require_api_key)])
def models(): return model_registry.list()

@app.get("/v1/admin/feedback", dependencies=[Depends(require_owner)])
def admin_feedback(): return {"items":feedback_store.items}
