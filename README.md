# PetuCV

PetuCV compares an existing PDF CV with a public job-ad URL using a lightweight ATS-style keyword analysis.

## Flow
1. User uploads a PDF CV.
2. PDF.js extracts text locally in the browser; the CV file is not uploaded for analysis.
3. User supplies a public job-ad URL.
4. PetuCV attempts to retrieve visible HTML text from the job page. Sites that block automated retrieval require manual job-description paste.
5. Browser computes keyword overlap, score, matches and missing terms.

## Cost architecture
No paid AI API is used per analysis. PDF parsing and ATS comparison run client-side. The server only serves the app and retrieves publicly accessible job HTML.

## Limitations
Scanned/image-only PDFs need OCR and are not supported in this MVP. LinkedIn and other protected/dynamic job sites may prevent automatic URL extraction. ATS score is an estimate and does not reproduce any specific employer ATS.
