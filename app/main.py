from pathlib import Path
import json, re, urllib.request, urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app=FastAPI(title="PetuCV",version="1.3.0",description="PDF CV to matching jobs in Chile")
WEB=Path(__file__).parent/"web"/"index.html"
@app.get("/",include_in_schema=False)
def web_app(): return FileResponse(WEB)
@app.get("/health")
def health(): return {"status":"ok","service":"PetuCV","version":"1.3.0","product":"cv-job-matching-chile"}

class SearchRequest(BaseModel): keywords:list[str]=Field(min_length=1,max_length=12)
def clean_html(s):
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()
def chile_ok(location,text=""):
    s=(str(location or "")+" "+str(text or "")).lower()
    chile=("chile","santiago","metropolitana","valparaiso","valparaíso","concepcion","concepción","antofagasta","temuco","rancagua","vina del mar","viña del mar","chillan","chillán","puerto montt")
    remote_ok=("latin america","latam","south america","americas","worldwide","anywhere")
    return any(x in s for x in chile) or ("remote" in s and any(x in s for x in remote_ok))

@app.post("/jobs")
def jobs(item:SearchRequest):
    terms=[re.sub(r"[^\w+#. -]","",x).strip() for x in item.keywords if x.strip()]
    query=" ".join(terms[:5]); found=[]
    try:
        req=urllib.request.Request("https://www.arbeitnow.com/api/job-board-api",headers={"User-Agent":"PetuCV/1.3"})
        with urllib.request.urlopen(req,timeout=15) as r: data=json.loads(r.read())
        for j in data.get("data",[]):
            desc=clean_html(j.get("description","")); loc=j.get("location","")
            if not chile_ok(loc,desc): continue
            text=" ".join([j.get("title",""),desc," ".join(j.get("tags") or [])]).lower()
            score=sum(1 for t in terms if t.lower() in text)
            if score: found.append({"score":score,"title":j.get("title") or "Empleo","description":desc[:220],"functions":desc[220:520] or ", ".join(j.get("tags") or [])[:300],"url":j.get("url"),"company":j.get("company_name",""),"location":loc})
    except Exception: pass
    try:
        url="https://remotive.com/api/remote-jobs?search="+urllib.parse.quote(query)
        req=urllib.request.Request(url,headers={"User-Agent":"PetuCV/1.3"})
        with urllib.request.urlopen(req,timeout=15) as r: data=json.loads(r.read())
        for j in data.get("jobs",[]):
            desc=clean_html(j.get("description","")); loc=j.get("candidate_required_location","")
            if not chile_ok(loc,desc): continue
            text=" ".join([j.get("title",""),desc,j.get("category","")]).lower()
            score=sum(1 for t in terms if t.lower() in text)
            if score: found.append({"score":score,"title":j.get("title") or "Empleo","description":desc[:220],"functions":desc[220:520],"url":j.get("url"),"company":j.get("company_name",""),"location":loc})
    except Exception: pass
    unique=[];seen=set()
    for j in sorted(found,key=lambda x:x["score"],reverse=True):
        key=(j["title"],j["url"])
        if key not in seen and j["url"]: seen.add(key);unique.append(j)
        if len(unique)==10: break
    if not unique: raise HTTPException(503,"No encontramos avisos compatibles para Chile en las fuentes disponibles en este momento.")
    return {"jobs":unique,"query":query,"market":"Chile"}
