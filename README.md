# PetuCV v1.3 — Chile
PetuCV reads a PDF CV locally, extracts professional keywords and searches for matching job opportunities limited to Chile.

## Scope
This first market version only returns listings whose location indicates Chile/a Chilean city, or remote listings whose stated eligibility includes Latin America, South America, the Americas or worldwide availability compatible with candidates in Chile.

## User flow
1. Upload PDF CV.
2. PDF.js extracts CV text locally in the browser.
3. PetuCV derives professional search terms without paid AI.
4. Public job feeds are queried and non-Chile-compatible listings are discarded.
5. Up to 10 matching jobs are shown with role, description, main functions and URL.

## Cost architecture
No paid AI API is used. The PDF remains in the browser; only selected professional keywords are sent to the backend.

## Coverage limitation
Results depend on the geographic coverage of the public job feeds used by the MVP. PetuCV does not invent jobs when fewer than 10 compatible Chile listings are available.
