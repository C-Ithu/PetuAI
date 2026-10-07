# PetuCV v1.2
PetuCV reads a PDF CV locally, extracts professional keywords and searches public job feeds for matching opportunities.

## User flow
1. Upload PDF CV.
2. Browser extracts CV text with PDF.js.
3. Browser derives professional search terms without paid AI.
4. PetuCV queries public job feeds and ranks results by term overlap.
5. Up to 10 real job listings are displayed in a table: role, short description, main functions and job URL.

## Sources
The MVP uses publicly accessible job feeds such as Arbeitnow and Remotive. Availability, geographic coverage and individual listings depend on those external sources.

## Cost architecture
No paid AI API is used. The CV PDF stays in the browser; only selected search keywords are sent to the PetuCV backend.
