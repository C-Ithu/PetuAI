import base64, os
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from .prompting import compile_edit_prompt
class LocalEnhanceBackend:
    name="local-enhance-v0"
    def _load(self,data):
        try: return Image.open(BytesIO(data)).convert("RGB")
        except Exception as exc: raise ValueError("Unsupported or invalid image") from exc
    def enhance(self,data):
        image=self._load(data); image=ImageEnhance.Contrast(image).enhance(1.05); image=ImageEnhance.Sharpness(image).enhance(1.12); image=image.filter(ImageFilter.UnsharpMask(radius=1.2,percent=110,threshold=3)); out=BytesIO(); image.save(out,format="JPEG",quality=94,optimize=True); return out.getvalue()
    def edit(self,data,instruction,profile="faithful"):
        compile_edit_prompt(instruction,profile)
        return self.enhance(data)
class OpenAIImageBackend(LocalEnhanceBackend):
    name="openai-image"
    def __init__(self):
        from openai import OpenAI
        self.client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model=os.getenv("PETUAI_IMAGE_MODEL","gpt-image-2.5-sunburst")
    def edit(self,data,instruction,profile="faithful"):
        prompt=compile_edit_prompt(instruction,profile)
        image=BytesIO(data); image.name="input.png"
        result=self.client.images.edit(model=self.model,image=image,prompt=prompt,output_format="jpeg",quality="medium")
        return base64.b64decode(result.data[0].b64_json)
def build_engine():
    if os.getenv("OPENAI_API_KEY"): return OpenAIImageBackend()
    return LocalEnhanceBackend()
engine=build_engine()
