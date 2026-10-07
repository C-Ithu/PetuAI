# PetuCV

PetuCV is a zero-paid-AI-consumption MVP for creating CVs and estimating ATS keyword compatibility.

## Features
- CV form and live document preview.
- Job-description keyword analysis in the browser.
- Estimated ATS compatibility score.
- Matching and missing keyword suggestions.
- Local browser storage.
- PDF export through the browser print/PDF function.

## Cost architecture
The CV builder, ATS analysis and document preparation run client-side. No OpenAI, Hugging Face or paid generative API is called per user action.

## Deployment
FastAPI serves the static application. Render only hosts the lightweight web service.

## Disclaimer
ATS scoring is an estimate based on textual keyword matching and does not guarantee performance in any particular applicant tracking system or hiring process.

## License
Apache-2.0.
