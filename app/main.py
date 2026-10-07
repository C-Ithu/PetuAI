from pathlib import Path
import json,re,urllib.request
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
app=FastAPI(title="PetuCV",version="1.6.0",description="Chile CV matching from job category feeds")
WEB=Path(__file__).parent/"web"/"index.html"
@app.get("/",include_in_schema=False)
def home():return FileResponse(WEB)
@app.get("/health")
def health():return {"status":"ok","service":"PetuCV","version":"1.6.0"}
class SearchRequest(BaseModel):keywords:list[str]=Field(min_length=1,max_length=12)
def flat(v):
    if isinstance(v,str):return v
    if isinstance(v,dict):return " ".join(flat(x) for x in v.values())
    if isinstance(v,list):return " ".join(flat(x) for x in v)
    return str(v or "")
def clean(s):return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(s or ""))).strip()
def chile(blob):
    s=blob.lower()
    return any(x in s for x in ("chile","santiago","valparaiso","valparaíso","concepcion","concepción","antofagasta","temuco","rancagua","puerto montt","la serena","remote (chile)"))
def parse(row,terms):
    a=row.get("attributes",row); blob=flat(a)
    if not chile(blob):return None
    low=blob.lower(); score=sum(1 for t in terms if t.lower() in low)
    title=clean(a.get("title") or a.get("name") or "Empleo")
    desc=clean(a.get("description") or a.get("description_headline") or blob)
    url=a.get("public_url") or a.get("url")
    if not url and a.get("slug"):url="https://www.getonbrd.com/jobs/"+str(a["slug"])
    if not url:return None
    loc=clean(a.get("location") or a.get("remote_modality") or "Chile")
    company=clean(a.get("company_name") or flat(a.get("company","")))
    return {"score":score,"title":title,"location":loc[:120] or "Chile","company":company[:100],"description":desc[:240],"functions":desc[240:600] or "Revisar detalle completo del aviso.","url":url}
@app.post("/jobs")
def jobs(item:SearchRequest):
    terms=[x.strip().lower() for x in item.keywords if x.strip()]
    categories=("programming","operations-management","product-management","machine-learning-ai","data-science-analytics","sysadmin-devops-qa","customer-support")
    found=[]
    for cat in categories:
        for page in (1,2,3):
            try:
                url=f"https://www.getonbrd.com/api/v0/categories/{cat}/jobs?page={page}&expand[]=company"
                req=urllib.request.Request(url,headers={"User-Agent":"PetuCV/1.6","Accept":"application/json"})
                with urllib.request.urlopen(req,timeout=15) as r:data=json.loads(r.read())
                for row in data.get("data",[]):
                    j=parse(row,terms)
                    if j:found.append(j)
            except Exception:continue
    unique=[];seen=set()
    for j in sorted(found,key=lambda x:(x["score"],"chile" in x["location"].lower(),"santiago" in x["location"].lower()),reverse=True):
        if j["url"] not in seen:
            seen.add(j["url"]);unique.append(j)
        if len(unique)==10:break
    if not unique:raise HTTPException(503,"La fuente no devolvió avisos chilenos en las categorías consultadas. Intenta nuevamente más tarde.")
    return {"jobs":unique,"market":"Chile","source":"Get on Board category feeds"}
