import base64, os
class OpenAIImageGenerator:
    name="openai-text-to-image"
    def __init__(self):
        from openai import OpenAI
        self.client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model=os.getenv("PETUAI_IMAGE_MODEL","gpt-image-2")
    def generate(self,prompt:str):
        prompt=" ".join((prompt or "").strip().split())
        if not prompt: raise ValueError("El prompt no puede estar vacío")
        instruction=f"Create one original polished image from this request:\n{prompt}\nCreate a fresh composition. Do not add watermarks, logos, trademarks or text unless explicitly requested."
        result=self.client.images.generate(model=self.model,prompt=instruction,size="1024x1024",quality="medium",output_format="jpeg",moderation="auto")
        return base64.b64decode(result.data[0].b64_json)
def build_engine():
    if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("OPENAI_API_KEY is required")
    return OpenAIImageGenerator()
engine=build_engine()
