from dataclasses import dataclass
@dataclass(frozen=True)
class PromptProfile:
    name: str
    preserve: str
PROFILES={
 "faithful":PromptProfile("faithful","Preserve every element not explicitly requested to change."),
 "creative":PromptProfile("creative","Preserve the main subject and explicit user constraints; allow creative interpretation only where required."),
 "product":PromptProfile("product","Preserve product geometry, labels, proportions, branding, materials and camera perspective unless targeted."),
 "interior":PromptProfile("interior","Preserve architecture, room geometry, camera angle, furniture and objects unless explicitly targeted.")
}
def compile_edit_prompt(user_instruction:str,profile:str="faithful")->str:
    instruction=" ".join((user_instruction or "").strip().split())
    if not instruction: raise ValueError("Instruction cannot be empty")
    if len(instruction)>8000: raise ValueError("Instruction is too long")
    p=PROFILES.get(profile,PROFILES["faithful"])
    return f"""PETUAI IMAGE EDIT — PROMPT CONTRACT v1
USER REQUEST: {instruction}
OBJECTIVE: Apply the requested visual change accurately to the supplied image.
PRESERVATION CONTRACT:
- {p.preserve}
- Change only what is necessary to satisfy the request.
- Preserve subject identity, facial characteristics and body proportions unless explicitly targeted.
- Preserve framing, perspective, crop and aspect ratio unless the request requires a change.
- Preserve lighting direction and plausible shadows unless lighting is the requested edit.
- Do not add unrelated objects, text, logos, watermarks or decorative elements.
- For enhancement-only requests, do not redesign or replace existing content.
- Keep boundaries, reflections, contact shadows, textures and occlusion realistic.
SUCCESS: The requested change is clearly visible while non-targeted content stays as close as possible to the source."""
