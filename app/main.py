from pathlib import Path
import json,re,urllib.request
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field

app=FastAPI(title="PetuCV",version="1.7.0",description="Chile CV matching with Get on Board public API")
WEB=Path(__file__).parent/"web"/"index.html"

@app.get("/",include_in_schema=False)
def home(): return FileResponse(WEB)

@app.get("/health")
def health(): return {"status":"ok","service":"PetuCV","version":"1.7.0"}

class SearchRequest(BaseModel):
    keywords:list[str]=Field(min_length=1,max_length=12)

def clean(s):
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(s or ""))).strip()

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"PetuCV/1.7","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read())

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

def parse(row,terms):
    a=row.get("attributes") or {}
    links=row.get("links") or {}
    title=clean(a.get("title") or "Empleo")
    description=clean(a.get("description") or a.get("description_headline") or "")
    functions=clean(a.get("functions") or a.get("projects") or "")
    countries=[str(x) for x in (a.get("countries") or [])]
    remote_modality=clean(a.get("remote_modality"))
    location=", ".join(countries) if countries else remote_modality or "Chile"
    url=links.get("public_url")
    if not url:
        return None
    searchable=" ".join([title,description,functions,clean(a.get("desirable"))]).lower()
    score=sum(1 for t in terms if t.lower() in searchable)
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
                j=parse(row,terms)
                if j: found.append(j)
        except Exception:
            errors.append(str(category_id))

    unique=[]; seen=set()
    for j in sorted(found,key=lambda x:x["score"],reverse=True):
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
        if len(unique)==10: break

    message=None
    if not unique:
        message="No encontramos ofertas compatibles con tu perfil en Chile en este momento. Puedes intentar nuevamente más tarde."
    return {"jobs":unique,"market":"Chile","source":"Get on Board","message":message,"source_errors":len(errors)}
