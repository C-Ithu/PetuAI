# PetuAI Prompt Training Protocol

PetuAI uses a prompt compiler and evaluation loop before any fine-tuning.

## Profiles
- faithful: minimal, surgical edits.
- creative: controlled creative interpretation.
- product: protects geometry, labels, branding and proportions.
- interior: protects architecture, perspective and untargeted objects.

## Regression evaluation
Test object removal, recoloring, lighting-only enhancement, interiors, products, portraits, exact text and multi-step edits.

Score 1–5 for instruction following, non-target preservation, realism, identity/geometry consistency and unwanted additions.

## Continual-learning gate
Only examples with explicit training consent are eligible. Human-reviewed examples may later become a preference or adapter-training dataset. Production weights are never modified directly from a single upload.

## Promotion and rollback
Promote a prompt/model candidate only after regression tests improve acceptance without materially reducing preservation. Keep the prior production version for rollback.
