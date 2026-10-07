import base64, json, os, urllib.request, urllib.error
class LocalImageGenerator:
    name="local-stable-diffusion"
    def __init__(self):
        self.url=os.getenv("PETUAI_LOCAL_IMAGE_API_URL","").rstrip("/")
        self.token=os.getenv("PETUAI_LOCAL_IMAGE_API_TOKEN","")
    def generate(self,prompt:str):
        prompt=" ".join((prompt or "").strip().split())
        if not prompt: raise ValueError("El prompt no puede estar vacío")
        if not self.url: raise RuntimeError("LOCAL_IMAGE_ENGINE_NOT_CONFIGURED")
        body=json.dumps({"prompt":f"{prompt}, original composition, polished image, no watermark","negative_prompt":"watermark, signature, logo, low quality","steps":20,"width":768,"height":768}).encode()
        headers={"Content-Type":"application/json"}
        if self.token: headers["Authorization"]=f"Bearer {self.token}"
        req=urllib.request.Request(self.url+"/sdapi/v1/txt2img",data=body,headers=headers,method="POST")
        try:
            with urllib.request.urlopen(req,timeout=180) as res: data=json.loads(res.read())
        except urllib.error.HTTPError as exc: raise RuntimeError(f"LOCAL_ENGINE_HTTP_{exc.code}") from exc
        except urllib.error.URLError as exc: raise RuntimeError("LOCAL_ENGINE_UNREACHABLE") from exc
        images=data.get("images") or []
        if not images: raise RuntimeError("LOCAL_ENGINE_NO_IMAGE")
        return base64.b64decode(images[0].split(",",1)[-1])
engine=LocalImageGenerator()
