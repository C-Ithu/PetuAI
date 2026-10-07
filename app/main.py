from pathlib import Path
import json, re, urllib.request, urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
app=FastAPI(title="PetuCV",version="1.3.1",description="Strict Chile-only CV job matching")
WEB=Path(__file__).parent/"web"/"index.html"
@app.get("/",include_in_schema=False)
def web_app(): return FileResponse(WEB)
@app.get("/health")
def health(): return {"status":"ok","service":"PetuCV","version":"1.3.1","product":"cv-job-matching-chile-strict"}
class SearchRequest(BaseModel): keywords:list[str]=Field(min_length=1,max_length=12)
def clean_html(s): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()
CHILE=("chile","santiago","región metropolitana","region metropolitana","valparaiso","valparaíso","concepcion","concepción","antofagasta","temuco","rancagua","vina del mar","viña del mar","chillan","chillán","puerto montt","la serena","iquique","talca","copiapo","copiapó","calama","osorno","los angeles","los ángeles")
def chile_ok(location):
    s=str(location or "").lower().strip()
    return bool(s) and any(x in s for x in CHILE)
@app.post("/jobs")
def jobs(item:SearchRequest):
    terms=[re.sub(r"[^\w+#. -]","",x).strip() for x in item.keywords if x.strip()];query=" ".join(terms[:5]);found=[]
    try:
        req=urllib.request.Request("https://www.arbeitnow.com/api/job-board-api",headers={"User-Agent":"PetuCV/1.3.1"})
        with urllib.request.urlopen(req,timeout=15) as r:data=json.loads(r.read())
        for j in data.get("data",[]):
            loc=j.get("location","")
            if not chile_ok(loc):continue
            desc=clean_html(j.get("description",""));text=" ".join([j.get("title",""),desc," ".join(j.get("tags") or [])]).lower();score=sum(1 for t in terms if t.lower() in text)
            if score:found.append({"score":score,"title":j.get("title") or "Empleo","description":desc[:220],"functions":desc[220:520] or ", ".join(j.get("tags") or [])[:300],"url":j.get("url"),"company":j.get("company_name",""),"location":loc})
    except Exception:pass
    try:
        url="https://remotive.com/api/remote-jobs?search="+urllib.parse.quote(query);req=urllib.request.Request(url,headers={"User-Agent":"PetuCV/1.3.1"})
        with urllib.request.urlopen(req,timeout=15) as r:data=json.loads(r.read())
        for j in data.get("jobs",[]):
            loc=j.get("candidate_required_location","")
            if not chile_ok(loc):continue
            desc=clean_html(j.get("description",""));text=" ".join([j.get("title",""),desc,j.get("category","")]).lower();score=sum(1 for t in terms if t.lower() in text)
            if score:found.append({"score":score,"title":j.get("title") or "Empleo","description":desc[:220],"functions":desc[220:520],"url":j.get("url"),"company":j.get("company_name",""),"location":loc})
    except Exception:pass
    unique=[];seen=set()
    for j in sorted(found,key=lambda x:x["score"],reverse=True):
        key=(j["title"],j["url"])
        if key not in seen and j["url"]:seen.add(key);unique.append(j)
        if len(unique)==10:break
    if not unique:raise HTTPException(503,"No encontramos avisos cuya ubicación indique explícitamente Chile en las fuentes actuales.")
    return {"jobs":unique,"query":query,"market":"Chile","strict_location":True}
