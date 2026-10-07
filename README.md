# PetuAI
**Imagina. Crea.**

## v1.2 — owner-hosted image generation
PetuAI no longer depends on OpenAI or Hugging Face hosted inference.

Architecture: Browser -> PetuAI on Render -> secure public endpoint -> owner-hosted Stable Diffusion-compatible API -> image preview.

Render variables:
- PETUAI_LOCAL_IMAGE_API_URL
- PETUAI_LOCAL_IMAGE_API_TOKEN

The local engine must expose a compatible /sdapi/v1/txt2img endpoint. No paid image API or per-image cloud credits are required by PetuAI. The owner-hosted computer supplies the compute and electricity.

Do not expose an unauthenticated image-generation API to the public internet.

## Monetization roadmap
A later release can provide a protected preview and use Mercado Pago to unlock the original download.

## Rights
PetuAI can request original compositions but cannot guarantee copyright status or absence of third-party rights in every output.

## License
Apache-2.0.
