from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter

class LocalEnhanceBackend:
    name="local-enhance-v0"
    def _load(self,data):
        try: return Image.open(BytesIO(data)).convert("RGB")
        except Exception as exc: raise ValueError("Unsupported or invalid image") from exc
    def enhance(self,data):
        image=self._load(data); image=ImageEnhance.Contrast(image).enhance(1.05); image=ImageEnhance.Sharpness(image).enhance(1.12); image=image.filter(ImageFilter.UnsharpMask(radius=1.2,percent=110,threshold=3)); out=BytesIO(); image.save(out,format="JPEG",quality=94,optimize=True); return out.getvalue()
    def edit(self,data,instruction):
        if not instruction.strip(): raise ValueError("Instruction cannot be empty")
        return self.enhance(data)
engine=LocalEnhanceBackend()
