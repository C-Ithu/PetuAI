from pathlib import Path
import json,re,urllib.request\nfrom datetime import datetime,timezone,timedelta
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field

app=FastAPI(title="PetuCV",version="2.0.0",description="Chile CV matching with Get on Board public API")
WEB=Path(__file__).parent/"web"/"index.html"

@app.get("/",include_in_schema=False)
def home(): return FileResponse(WEB)

@app.get("/health")
def health(): return {"status":"ok","service":"PetuCV","version":"2.0.0"}

class SearchRequest(BaseModel):
    keywords:list[str]=Field(min_length=1,max_length=20)
    recent_keywords:list[str]=Field(default_factory=list,max_length=12)

def clean(s):
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(s or ""))).strip()

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"PetuCV/2.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read())

def recent(date_value):
    if not date_value:
        return False
    try:
        if isinstance(date_value,(int,float)):
            dt=datetime.fromtimestamp(date_value,timezone.utc)
        else:
            s=str(date_value).replace("Z","+00:00")
            dt=datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt=dt.replace(tzinfo=timezone.utc)
        return dt>=datetime.now(timezone.utc)-timedelta(days=21)
    except Exception:
        return False

def summarize(text,limit):
    text=clean(text)
    if not text:return ""
    parts=re.split(r"(?<=[.!?])\\s+",text)
    out=""
    for p in parts:
        p=p.strip()
        if not p:continue
        candidate=(out+" "+p).strip()
        if len(candidate)>limit:break
        out=candidate
        if len(out)>=limit*0.55:break
    if not out:out=text[:limit].rsplit(" ",1)[0]
    return out.rstrip(" .")+"."

def parse(row,terms,recent_terms):
    a=row.get("attributes") or {}
    links=row.get("links") or {}
    title=clean(a.get("title") or "Empleo")
    description=clean(a.get("description") or a.get("description_headline") or "")
    functions=clean(a.get("functions") or a.get("projects") or "")
    countries=[str(x) for x in (a.get("countries") or [])]
    remote_modality=clean(a.get("remote_modality"))
    location=", ".join(countries) if countries else remote_modality or "Chile"
    url=links.get("public_url")
    published=a.get("published_at") or a.get("created_at")
    if not recent(published):
        return None
    if not url:
        return None
    searchable=" ".join([title,description,functions,clean(a.get("desirable"))]).lower()
    global_hits=sum(1 for t in terms if t.lower() in searchable)
    recent_hits=sum(1 for t in recent_terms if t.lower() in searchable)
    title_hits=sum(1 for t in recent_terms if t.lower() in title.lower())
    score=global_hits+(recent_hits*3)+(title_hits*2)
    return {
        "score":score,
        "title":title,
        "location":location,
        "company":"",
        "description":summarize(description,150),
        "functions":summarize(functions,220) or "Revisar funciones en el aviso.",
        "url":url
    }

@app.post("/jobs")
def jobs(item:SearchRequest):
    terms=[x.strip().lower() for x in item.keywords if x.strip()]
    recent_terms=[x.strip().lower() for x in item.recent_keywords if x.strip()]
    found=[]
    errors=[]
    try:
        cats=get_json("https://www.getonbrd.com/api/v0/categories?per_page=120")
        categories=cats.get("data",[])
    except Exception as e:
        categories=[]
        errors.append("categories")

    preferred=("program","product","operation","data","sysadmin","devops","machine","agil","project")
    selected=[]
    for cat in categories:
        a=cat.get("attributes") or {}
        label=(str(a.get("name",""))+" "+str(a.get("dimension",""))).lower()
        if any(p in label for p in preferred):
            selected.append(cat.get("id"))
    if not selected:
        selected=[cat.get("id") for cat in categories[:10] if cat.get("id")]

    for category_id in selected:
        try:
            url=f"https://www.getonbrd.com/api/v0/categories/{category_id}/jobs?country_code=cl&per_page=120"
            data=get_json(url)
            for row in data.get("data",[]):
                j=parse(row,terms,recent_terms)
                if j: found.append(j)
        except Exception:
            errors.append(str(category_id))

    # Remote OK: only jobs explicitly compatible with Chile/LATAM.
    try:
        data=get_json("https://remoteok.com/api")
        rows=data[1:] if isinstance(data,list) else []
        for r in rows:
            loc=clean(r.get("location") or "")
            geo=(loc+" "+clean(str(r.get("tags") or []))).lower()
            if not any(x in geo for x in ("chile","latam","latin america")):
                continue
            published=r.get("date") or r.get("epoch")
            if not recent(published):
                continue
            searchable=" ".join([clean(r.get("position")),clean(r.get("description"))]).lower()
            gh=sum(1 for t in terms if t in searchable)
            rh=sum(1 for t in recent_terms if t in searchable)
            job_url=r.get("url") or r.get("apply_url")
            if job_url:
                found.append({"score":gh+rh*3,"title":clean(r.get("position") or "Empleo remoto"),"location":loc or "LATAM / Chile compatible","company":clean(r.get("company")),"description":summarize(r.get("description"),150),"functions":"Revisar funciones en el aviso.","url":job_url,"source":"Remote OK","published_at":str(published)})
    except Exception:
        errors.append("remoteok")

    # Remotive: only jobs explicitly compatible with Chile/LATAM.
    try:
        data=get_json("https://remotive.com/api/remote-jobs")
        for r in data.get("jobs",[]):
            loc=clean(r.get("candidate_required_location") or "")
            if not any(x in loc.lower() for x in ("chile","latam","latin america")):
                continue
            published=r.get("publication_date")
            if not recent(published):
                continue
            searchable=" ".join([clean(r.get("title")),clean(r.get("description")),clean(r.get("category"))]).lower()
            gh=sum(1 for t in terms if t in searchable)
            rh=sum(1 for t in recent_terms if t in searchable)
            job_url=r.get("url")
            if job_url:
                found.append({"score":gh+rh*3,"title":clean(r.get("title") or "Empleo remoto"),"location":loc or "LATAM / Chile compatible","company":clean(r.get("company_name")),"description":summarize(r.get("description"),150),"functions":"Revisar funciones en el aviso.","url":job_url,"source":"Remotive","published_at":str(published)})
    except Exception:
        errors.append("remotive")

    unique=[]; seen=set()
    for j in sorted(found,key=lambda x:x["score"],reverse=True):
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)

    message=None
    if not unique:
        message="No encontramos ofertas compatibles con tu perfil en Chile en este momento. Puedes intentar nuevamente más tarde."
    return {"jobs":unique,"total":len(unique),"page_size":20,"market":"Chile","source":"Get on Board + Remote OK + Remotive","message":message,"source_errors":len(errors)}
