import os
from io import BytesIO

class FreeTierImageGenerator:
    name="huggingface-flux-free-tier"
    def __init__(self):
        self.model=os.getenv("PETUAI_IMAGE_MODEL","black-forest-labs/FLUX.1-schnell")
    def generate(self,prompt:str):
        from huggingface_hub import InferenceClient
        token=os.getenv("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN_NOT_CONFIGURED")
        prompt=" ".join((prompt or "").strip().split())
        if not prompt:
            raise ValueError("El prompt no puede estar vacío")
        client=InferenceClient(provider="auto",api_key=token)
        image=client.text_to_image(f"{prompt}. Original composition, polished image, no watermark.",model=self.model)
        out=BytesIO()
        image.convert("RGB").save(out,format="JPEG",quality=92)
        return out.getvalue()

engine=FreeTierImageGenerator()
