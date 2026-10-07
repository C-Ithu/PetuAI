from pathlib import Path
import json,re,urllib.request,urllib.parse
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
app=FastAPI(title="PetuCV",version="1.5.0",description="Chile CV job matching by role families")
WEB=Path(__file__).parent/"web"/"index.html"
@app.get("/",include_in_schema=False)
def web_app():return FileResponse(WEB)
@app.get("/health")
def health():return {"status":"ok","service":"PetuCV","version":"1.5.0","product":"chile-job-matching"}
class SearchRequest(BaseModel):keywords:list[str]=Field(min_length=1,max_length=12)
def clean(s):return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(s or ""))).strip()
CHILE=("chile","santiago","valparaiso","valparaíso","concepcion","concepción","antofagasta","temuco","rancagua","vina del mar","viña del mar","chillan","chillán","puerto montt","la serena","iquique","talca","copiapo","copiapó","calama","osorno")
def flat(v):
    if isinstance(v,str):return v
    if isinstance(v,dict):return " ".join(flat(x) for x in v.values())
    if isinstance(v,list):return " ".join(flat(x) for x in v)
    return str(v or "")
def normalize(row,terms):
    a=row.get("attributes",row);blob=flat(a);low=blob.lower()
    if not any(x in low for x in CHILE):return None
    title=a.get("title") or a.get("name") or "Empleo"
    desc=clean(a.get("description") or a.get("description_headline") or a.get("functions") or blob)
    url=a.get("public_url") or a.get("url") or a.get("apply_url")
    if not url:
        slug=a.get("slug")
        if slug:url="https://www.getonbrd.com/jobs/"+str(slug)
    loc=clean(a.get("location") or a.get("candidate_required_location") or a.get("remote_modality") or "Chile")
    company=clean(a.get("company_name") or flat(a.get("company","")))
    score=sum(1 for t in terms if t.lower() in low)
    if not score or not url:return None
    return {"score":score,"title":clean(title),"description":desc[:240],"functions":desc[240:600] or "Revisar detalle completo del aviso.","url":url,"company":company[:100],"location":loc[:120] or "Chile"}
@app.post("/jobs")
def jobs(item:SearchRequest):
    terms=[re.sub(r"[^\w+#. -]","",x).strip() for x in item.keywords if x.strip()]
    found=[];queries=[]
    for t in terms[:6]:
        if len(t)>=3 and t not in queries:queries.append(t)
    for q in queries:
        try:
            url="https://www.getonbrd.com/api/v0/search/jobs?query="+urllib.parse.quote(q)+"&expand[]=company"
            req=urllib.request.Request(url,headers={"User-Agent":"PetuCV/1.5","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=15) as r:data=json.loads(r.read())
            for row in data.get("data",[]):
                j=normalize(row,terms)
                if j:found.append(j)
        except Exception:pass
    unique=[];seen=set()
    for j in sorted(found,key=lambda x:x["score"],reverse=True):
        key=j["url"]
        if key not in seen:seen.add(key);unique.append(j)
        if len(unique)==10:break
    if not unique:raise HTTPException(503,"No encontramos coincidencias en Chile con los términos detectados. Prueba con un CV que contenga un cargo o habilidades claramente identificables.")
    return {"jobs":unique,"market":"Chile","source":"Get on Board"}
