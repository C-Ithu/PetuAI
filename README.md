# PetuAI

**Imagina. Crea.**

PetuAI is a text-to-image web application. A user writes a prompt and PetuAI generates a new image from that text.

## Product direction — v1.0

- Text prompt only: no source-image upload is required.
- One generated image per request.
- Browser preview.
- Download monetization is intentionally reserved for a future release.
- Public browser endpoint: `POST /generate`.
- Developer endpoint: `POST /v1/generate`.
- GPT Image backend selected through `PETUAI_IMAGE_MODEL`.
- Owner-only administration remains protected by `PETUAI_OWNER_KEY`.

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000`.

## Rights and originality

PetuAI instructs the generation backend to create fresh compositions and not intentionally reproduce known copyrighted works. This is a product safeguard, not a legal guarantee. AI-generated output may raise copyright, trademark, publicity and other third-party-rights questions depending on the prompt, output and jurisdiction. Ownership/licensing of downloads should be defined in PetuAI's Terms of Use before paid downloads launch.

## Monetization roadmap

The current product validates text-to-image generation. A later release can add Mercado Pago checkout to unlock a specific generated asset/download rather than charging a monthly subscription.

## License

Repository source code: Apache-2.0. See `LICENSE`.
