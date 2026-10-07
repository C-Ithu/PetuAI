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
    except Exception as exc:
        message=str(exc)
        low=message.lower()
        if "hf_token_not_configured" in low:
            detail="HF_TOKEN no está configurado en el servidor."
        elif "401" in low or "unauthorized" in low or "authentication" in low:
            detail="Hugging Face rechazó el token. Revisa HF_TOKEN y sus permisos de Inference Providers."
        elif "403" in low or "gated" in low or "access" in low or "permission" in low:
            detail="La cuenta de Hugging Face no tiene acceso al modelo. Acepta las condiciones de FLUX.1-schnell y revisa los permisos del token."
        elif "402" in low or "credits" in low or "quota" in low or "billing" in low:
            detail="La cuota gratuita de Hugging Face no está disponible o se agotó."
        elif "429" in low or "rate limit" in low:
            detail="Hugging Face alcanzó temporalmente el límite de solicitudes. Intenta nuevamente más tarde."
        elif "503" in low or "timeout" in low or "unavailable" in low:
            detail="El proveedor de generación está temporalmente no disponible. Intenta nuevamente."
        else:
            detail=f"Error de Hugging Face: {message[:300]}"
        raise HTTPException(status_code=502,detail=detail)
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
