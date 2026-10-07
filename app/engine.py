import base64, os
class OpenAIImageGenerator:
    name="openai-text-to-image"
    def __init__(self):
        from openai import OpenAI
        self.client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model=os.getenv("PETUAI_IMAGE_MODEL","gpt-image-2.5-flare")
    def generate(self,prompt:str):
        prompt=" ".join((prompt or "").strip().split())
        if not prompt: raise ValueError("El prompt no puede estar vacío")
        if len(prompt)>32000: raise ValueError("El prompt es demasiado largo")
        instruction=f"""Create one original image from this request:
{prompt}
Create a fresh composition rather than intentionally reproducing a known copyrighted work. Do not add watermarks. Do not add logos, trademarks or text unless explicitly requested. Do not intentionally imitate a living artist's distinctive style. Return a polished standalone image."""
        result=self.client.images.generate(model=self.model,prompt=instruction,size="1024x1024",quality="medium",output_format="jpeg",moderation="auto")
        return base64.b64decode(result.data[0].b64_json)
def build_engine():
    if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("OPENAI_API_KEY is required")
    return OpenAIImageGenerator()
engine=build_engine()
