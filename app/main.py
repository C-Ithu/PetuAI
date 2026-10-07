from pathlib import Path
from urllib.parse import urlparse
import ipaddress, socket, urllib.request
from html.parser import HTMLParser
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

app=FastAPI(title="PetuCV",version="1.1.0",description="PDF CV and job URL ATS comparison")
WEB=Path(__file__).parent/"web"/"index.html"

@app.get("/",include_in_schema=False)
def web_app(): return FileResponse(WEB)
@app.get("/health")
def health(): return {"status":"ok","service":"PetuCV","version":"1.1.0","product":"pdf-url-ats"}

class JobURL(BaseModel): url: HttpUrl
class TextExtractor(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg"): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript","svg") and self.skip: self.skip-=1
    def handle_data(self,data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def public_host(host):
    try:
        for info in socket.getaddrinfo(host,None):
            ip=ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved: return False
        return True
    except Exception: return False

@app.post("/job-text")
def job_text(item:JobURL):
    url=str(item.url); p=urlparse(url)
    if p.scheme not in ("http","https") or not p.hostname or not public_host(p.hostname):
        raise HTTPException(400,"URL no permitida.")
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PetuCV/1.1","Accept":"text/html"})
    try:
        with urllib.request.urlopen(req,timeout=12) as res:
            if "text/html" not in res.headers.get("Content-Type",""):
                raise HTTPException(400,"La URL no corresponde a una página HTML.")
            raw=res.read(2_000_000).decode("utf-8","ignore")
    except HTTPException: raise
    except Exception:
        raise HTTPException(422,"El portal bloqueó o impidió leer el aviso automáticamente. Pega la descripción del cargo manualmente.")
    parser=TextExtractor(); parser.feed(raw)
    text=" ".join(parser.parts)
    if len(text)<150:
        raise HTTPException(422,"No fue posible extraer suficiente texto del aviso. Pega la descripción manualmente.")
    return {"text":text[:100000],"source":p.hostname}
