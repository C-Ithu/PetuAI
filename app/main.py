from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import re
import urllib.request
import urllib.parse

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="PetuCV", version="2.2.2")
WEB = Path(__file__).parent / "web" / "index.html"

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB)

@app.get("/health")
def health():
    return {"status": "ok", "service": "PetuCV", "version": "2.2.2"}

class SearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1, max_length=20)
    recent_keywords: list[str] = Field(default_factory=list, max_length=12)

def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PetuCV/2.2.2", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read())

def is_recent(value):
    if not value:
        return False
    try:
        if isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value, timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt >= datetime.now(timezone.utc) - timedelta(days=5)
    except (ValueError, TypeError, OSError):
        return False

def summarize(value, limit):
    text = clean(value)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    result = ""
    for part in parts:
        candidate = (result + " " + part.strip()).strip()
        if len(candidate) > limit:
            break
        result = candidate
        if len(result) >= limit * 0.55:
            break
    if not result:
        result = text[:limit].rsplit(" ", 1)[0]
    return result.rstrip(" .") + "."

def score_job(searchable, title, terms, recent_terms):
    searchable = searchable.lower()
    title = title.lower()
    all_terms = list(dict.fromkeys(terms))
    recent = list(dict.fromkeys(recent_terms))
    if not all_terms:
        return 0
    whole_hits = sum(1 for term in all_terms if term in searchable)
    recent_hits = sum(1 for term in recent if term in searchable)
    title_hits = sum(1 for term in recent if term in title)
    role_terms = ("project manager","jefe de proyecto","pmo","scrum","product manager","sap","software","devops")
    role_hits = sum(1 for term in role_terms if term in all_terms and term in searchable)
    raw = (whole_hits / len(all_terms)) * 45
    if recent:
        raw += (recent_hits / len(recent)) * 30
        raw += (title_hits / len(recent)) * 15
    raw += min(role_hits * 5, 10)
    return min(100, round(raw))

def parse_getonbrd(row, terms, recent_terms):
    attrs = row.get("attributes") or {}
    links = row.get("links") or {}
    published = attrs.get("published_at") or attrs.get("created_at")
    if not is_recent(published):
        return None
    url = links.get("public_url")
    if not url:
        return None
    title = clean(attrs.get("title") or "Empleo")
    description = clean(attrs.get("description") or attrs.get("description_headline"))
    functions = clean(attrs.get("functions") or attrs.get("projects"))
    countries = [str(x) for x in (attrs.get("countries") or [])]
    location = ", ".join(countries) or clean(attrs.get("remote_modality")) or "Chile"
    searchable = " ".join([title, description, functions, clean(attrs.get("desirable"))])
    return {
        "score": score_job(searchable, title, terms, recent_terms),
        "compatibility": score_job(searchable, title, terms, recent_terms),
        "title": title,
        "location": location,
        "company": "",
        "description": summarize(description, 150),
        "functions": summarize(functions, 220) or "Revisar funciones en el aviso.",
        "url": url,
        "source": "Get on Board",
        "published_at": str(published),
    }

@app.post("/jobs")
def jobs(item: SearchRequest):
    terms = [x.strip().lower() for x in item.keywords if x.strip()]
    recent_terms = [x.strip().lower() for x in item.recent_keywords if x.strip()]
    found, errors = [], []

    try:
        categories = get_json("https://www.getonbrd.com/api/v0/categories?per_page=120").get("data", [])
        selected = [c.get("id") for c in categories if c.get("id")]
        for category_id in selected:
            try:
                data = get_json(f"https://www.getonbrd.com/api/v0/categories/{category_id}/jobs?country_code=cl&per_page=120")
                for row in data.get("data", []):
                    job = parse_getonbrd(row, terms, recent_terms)
                    if job and job["score"] >= 20:
                        found.append(job)
            except Exception:
                errors.append(f"getonbrd:{category_id}")
    except Exception:
        errors.append("getonbrd")

    try:
        data = get_json("https://remoteok.com/api")
        for row in data[1:] if isinstance(data, list) else []:
            location = clean(row.get("location"))
            geo = (location + " " + clean(row.get("tags"))).lower()
            if not any(x in geo for x in ("chile", "latam", "latin america")):
                continue
            published = row.get("date") or row.get("epoch")
            if not is_recent(published):
                continue
            url = row.get("url") or row.get("apply_url")
            if not url:
                continue
            title = clean(row.get("position") or "Empleo remoto")
            description = clean(row.get("description"))
            found.append({
                "score": score_job(title + " " + description, title, terms, recent_terms),
                "compatibility": score_job(title + " " + description, title, terms, recent_terms),
                "title": title, "location": location or "LATAM / Chile compatible",
                "company": clean(row.get("company")), "description": summarize(description, 150),
                "functions": "Revisar funciones en el aviso.", "url": url,
                "source": "Remote OK", "published_at": str(published),
            })
    except Exception:
        errors.append("remoteok")

    try:
        for row in get_json("https://remotive.com/api/remote-jobs").get("jobs", []):
            location = clean(row.get("candidate_required_location"))
            if not any(x in location.lower() for x in ("chile", "latam", "latin america")):
                continue
            published = row.get("publication_date")
            if not is_recent(published):
                continue
            url = row.get("url")
            if not url:
                continue
            title = clean(row.get("title") or "Empleo remoto")
            description = clean(row.get("description"))
            searchable = title + " " + description + " " + clean(row.get("category"))
            found.append({
                "score": score_job(searchable, title, terms, recent_terms),
                "compatibility": score_job(searchable, title, terms, recent_terms),
                "title": title, "location": location or "LATAM / Chile compatible",
                "company": clean(row.get("company_name")), "description": summarize(description, 150),
                "functions": "Revisar funciones en el aviso.", "url": url,
                "source": "Remotive", "published_at": str(published),
            })
    except Exception:
        errors.append("remotive")

    try:
        data = get_json("https://himalayas.app/jobs/api/search?country=CL&sort=recent&page=1")
        rows = data.get("jobs") or data.get("data") or []
        for row in rows:
            published = row.get("pubDate")
            if not is_recent(published):
                continue
            restrictions = clean(row.get("locationRestrictions"))
            location = restrictions or "Remoto compatible con Chile"
            url = row.get("applicationLink")
            if not url:
                continue
            title = clean(row.get("title") or "Empleo remoto")
            description = clean(row.get("description") or row.get("excerpt"))
            searchable = " ".join([title, description, clean(row.get("category")), clean(row.get("parentCategories"))])
            match = score_job(searchable, title, terms, recent_terms)
            found.append({"score":match,"compatibility":match,"title":title,"location":location,"company":clean(row.get("companyName")),"description":summarize(description,150),"functions":"Revisar funciones en el aviso.","url":url,"source":"Himalayas","published_at":str(published)})
    except Exception:
        errors.append("himalayas")

    try:
        data = get_json("https://jobicy.com/api/v2/remote-jobs?geo=latam&count=200")
        for row in data.get("jobs", []):
            published = row.get("pubDate")
            if not is_recent(published):
                continue
            url = row.get("url")
            if not url:
                continue
            title = clean(row.get("jobTitle") or "Empleo remoto")
            description = clean(row.get("jobDescription") or row.get("jobExcerpt"))
            location = clean(row.get("jobGeo")) or "LATAM / Chile compatible"
            searchable = " ".join([title,description,clean(row.get("jobIndustry")),clean(row.get("jobType"))])
            match = score_job(searchable,title,terms,recent_terms)
            found.append({"score":match,"compatibility":match,"title":title,"location":location,"company":clean(row.get("companyName")),"description":summarize(description,150),"functions":"Revisar funciones en el aviso.","url":url,"source":"Jobicy","published_at":str(published)})
    except Exception:
        errors.append("jobicy")

    try:
        for page in (1, 2):
            data = get_json(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
            for row in data.get("data", []):
                published = row.get("created_at")
                if not is_recent(published):
                    continue
                location = clean(row.get("location"))
                geo = (location + " " + clean(row.get("tags"))).lower()
                if not (row.get("remote") and any(x in geo for x in ("chile","latam","latin america","worldwide","remote"))):
                    continue
                url = row.get("url")
                if not url:
                    continue
                title = clean(row.get("title") or "Empleo")
                description = clean(row.get("description"))
                searchable = " ".join([title,description,clean(row.get("tags")),clean(row.get("job_types"))])
                match = score_job(searchable,title,terms,recent_terms)
                found.append({"score":match,"compatibility":match,"title":title,"location":location or "Remoto","company":clean(row.get("company_name")),"description":summarize(description,150),"functions":"Revisar funciones en el aviso.","url":url,"source":"Arbeitnow","published_at":str(published)})
    except Exception:
        errors.append("arbeitnow")

    # Bolsa Nacional de Empleo (BNE): public search pages, queried with CV role terms.
    # BNE has no documented public JSON API, so only public result pages are used.
    try:
        bne_terms = list(dict.fromkeys(recent_terms + terms))[:8]
        for term in bne_terms:
            query = urllib.parse.urlencode({
                "clasificarYPaginar": "true",
                "mostrar": "empleo",
                "numPaginaRecuperar": 1,
                "numResultadosPorPagina": 50,
                "textoLibre": term,
            })
            url = "https://www.bne.cl/ofertas?" + query
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PetuCV/2.2"})
            with urllib.request.urlopen(req, timeout=20) as response:
                html = response.read().decode("utf-8", errors="ignore")
            # Capture public offer links and nearby visible card text.
            matches = list(re.finditer(r'href=["\\\'](/oferta/[^"\\\']+)["\\\']', html, re.I))
            for match in matches:
                offer_url = "https://www.bne.cl" + match.group(1)
                start = max(0, match.start() - 1800)
                end = min(len(html), match.end() + 600)
                card = clean(html[start:end])
                age = re.search(r"Hace\\s+(\\d+)\\s+d[ií]as?", card, re.I)
                if age and int(age.group(1)) > 5:
                    continue
                if not age and not re.search(r"\\bHoy\\b|Hace\\s+[1-5]\\s+d[ií]as?", card, re.I):
                    continue
                text = clean(re.sub(r"<[^>]+>", " ", html[start:end]))
                title_match = re.findall(r">\\s*([^<>]{8,120})\\s*<", html[start:match.start()])
                title = clean(title_match[-1]) if title_match else "Oferta BNE"
                match_score = score_job(text, title, terms, recent_terms)
                found.append({
                    "score": match_score, "compatibility": match_score,
                    "title": title, "location": "Chile",
                    "company": "", "description": summarize(text, 150),
                    "functions": "Revisar funciones y requisitos en BNE.",
                    "url": offer_url, "source": "Bolsa Nacional de Empleo (BNE)",
                    "published_at": "Últimos 5 días",
                })
    except Exception:
        errors.append("bne")

    unique, seen = [], set()
    for job in sorted(found, key=lambda x: x["score"], reverse=True):
        if job["score"] < 20:
            continue
        if job["url"] not in seen:
            seen.add(job["url"])
            unique.append(job)

    message = None if unique else "No encontramos ofertas compatibles con tu perfil en Chile publicadas durante los últimos 5 días."
    payload = {
        "jobs": unique, "total": len(unique), "page_size": 20, "market": "Chile",
        "source": "Get on Board + Remote OK + Remotive + Himalayas + Jobicy + Arbeitnow + BNE", "message": message,
        "source_errors": len(errors),
    }
    return JSONResponse(payload, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})
