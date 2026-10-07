# PetuCV v1.4 — Chile
PetuCV now uses the public Get on Board job API as its primary job source. The public API requires no paid AI service or private API key for published job data.

## Flow
- PDF CV is read locally with PDF.js.
- Professional terms are extracted in the browser.
- PetuCV searches Get on Board's public job search endpoint using several of those terms.
- Only records whose returned data explicitly references Chile or a Chilean city are retained.
- Up to 10 unique matches are shown with role, location, description, functions and job URL.

No international fallback is used in this Chile-first MVP.
