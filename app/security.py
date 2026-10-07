import os, secrets
from fastapi import Header, HTTPException

def _check(provided, expected, label):
    if not provided or not secrets.compare_digest(provided, expected): raise HTTPException(status_code=401,detail=f"Invalid {label}")

def require_api_key(x_api_key: str|None=Header(default=None)): _check(x_api_key,os.getenv("PETUAI_API_KEY","change-me"),"API key")
def require_owner(x_owner_key: str|None=Header(default=None)): _check(x_owner_key,os.getenv("PETUAI_OWNER_KEY","owner-change-me"),"owner key")
