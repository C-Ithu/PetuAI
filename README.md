# PetuAI
**Imagina. Crea.**

PetuAI is a text-to-image application using an open image model through Hugging Face Inference Providers.

## v1.1 architecture
Prompt -> PetuAI -> Hugging Face Inference -> FLUX.1-schnell -> preview.

OpenAI and OPENAI_API_KEY are no longer required. The default model is `black-forest-labs/FLUX.1-schnell`.

Hugging Face Free accounts include a limited monthly inference credit. PetuAI does not enable paid usage automatically; free cloud inference is quota-limited and is not unlimited compute.

## Environment
```
HF_TOKEN=...
PETUAI_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
```

The Hugging Face token needs inference permissions and must remain server-side.

## Monetization roadmap
Generation/preview is the validation experience. A later release can use Mercado Pago to unlock downloads.

## Rights
PetuAI requests original compositions, but cannot guarantee copyright status or absence of third-party rights in every generated output.

## License
Repository source code: Apache-2.0.
