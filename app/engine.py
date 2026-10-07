import os
from io import BytesIO
class FreeTierImageGenerator:
    name="huggingface-flux-free-tier"
    def __init__(self):
        from huggingface_hub import InferenceClient
        token=os.getenv("HF_TOKEN")
        if not token: raise RuntimeError("HF_TOKEN is required")
        self.model=os.getenv("PETUAI_IMAGE_MODEL","black-forest-labs/FLUX.1-schnell")
        self.client=InferenceClient(provider="auto",api_key=token)
    def generate(self,prompt:str):
        prompt=" ".join((prompt or "").strip().split())
        if not prompt: raise ValueError("El prompt no puede estar vacío")
        instruction=f"{prompt}. Original composition, polished image, no watermark."
        image=self.client.text_to_image(instruction,model=self.model)
        out=BytesIO(); image.convert("RGB").save(out,format="JPEG",quality=92); return out.getvalue()
def build_engine(): return FreeTierImageGenerator()
engine=build_engine()
