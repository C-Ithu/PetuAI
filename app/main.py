from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import re
import urllib.request

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="PetuCV", version="2.0.1")
WEB = Path(__file__).parent / "web" / "index.html"

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB)

@app.get("/health")
def health():
    return {"status": "ok", "service": "PetuCV", "version": "2.0.1"}

class SearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1, max_length=20)
    recent_keywords: list[str] = Field(default_factory=list, max_length=12)

def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PetuCV/2.0.1", "Accept": "application/json"})
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
        return dt >= datetime.now(timezone.utc) - timedelta(days=21)
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
    return (
        sum(1 for term in terms if term in searchable)
        + 3 * sum(1 for term in recent_terms if term in searchable)
        + 2 * sum(1 for term in recent_terms if term in title)
    )

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
        preferred = ("program", "product", "operation", "data", "sysadmin", "devops", "machine", "agil", "project")
        selected = []
        for category in categories:
            attrs = category.get("attributes") or {}
            label = (str(attrs.get("name", "")) + " " + str(attrs.get("dimension", ""))).lower()
            if any(word in label for word in preferred):
                selected.append(category.get("id"))
        if not selected:
            selected = [c.get("id") for c in categories[:10] if c.get("id")]
        for category_id in selected:
            try:
                data = get_json(f"https://www.getonbrd.com/api/v0/categories/{category_id}/jobs?country_code=cl&per_page=120")
                for row in data.get("data", []):
                    job = parse_getonbrd(row, terms, recent_terms)
                    if job:
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
                "title": title, "location": location or "LATAM / Chile compatible",
                "company": clean(row.get("company_name")), "description": summarize(description, 150),
                "functions": "Revisar funciones en el aviso.", "url": url,
                "source": "Remotive", "published_at": str(published),
            })
    except Exception:
        errors.append("remotive")

    unique, seen = [], set()
    for job in sorted(found, key=lambda x: x["score"], reverse=True):
        if job["url"] not in seen:
            seen.add(job["url"])
            unique.append(job)

    message = None if unique else "No encontramos ofertas compatibles con tu perfil en Chile publicadas durante los últimos 21 días."
    return {
        "jobs": unique, "total": len(unique), "page_size": 20, "market": "Chile",
        "source": "Get on Board + Remote OK + Remotive", "message": message,
        "source_errors": len(errors),
    }
