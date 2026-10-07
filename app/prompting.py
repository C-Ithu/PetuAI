from dataclasses import dataclass

@dataclass(frozen=True)
class PromptProfile:
    name: str
    preserve: str
    quality: str

PROFILES = {
    "faithful": PromptProfile("faithful", "Preserve identity, geometry, composition, camera angle, perspective, proportions, text, logos and every element not explicitly requested to change.", "Photorealistic, coherent lighting, natural textures, clean edges, no artifacts."),
    "creative": PromptProfile("creative", "Preserve the main subject and all constraints explicitly stated by the user.", "Visually coherent, high quality, intentional details, no accidental text or artifacts."),
}

def compile_edit_prompt(user_instruction: str, profile: str = "faithful") -> str:
    instruction = " ".join(user_instruction.strip().split())
    if not instruction:
        raise ValueError("Instruction cannot be empty")
    if len(instruction) > 3000:
        raise ValueError("Instruction is too long")
    p = PROFILES.get(profile, PROFILES["faithful"])
    return f"""You are PetuAI, a precision image-editing system.
EDIT REQUEST: {instruction}
PRESERVATION RULE: {p.preserve}
QUALITY RULE: {p.quality}
Execute only the requested visual changes. Do not add unrelated objects or redesign untouched areas. If the request is ambiguous, prefer the smallest reasonable change. Keep the output suitable as a direct edited replacement of the input image."""
