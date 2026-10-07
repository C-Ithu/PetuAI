from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse

app=FastAPI(title="PetuCV",version="1.0.0",description="CV builder and ATS analyzer without paid AI APIs")
WEB=Path(__file__).parent/"web"/"index.html"

@app.get("/",include_in_schema=False)
def web_app():
    return FileResponse(WEB)

@app.get("/health")
def health():
    return {"status":"ok","service":"PetuCV","version":"1.0.0","product":"cv-ats"}
