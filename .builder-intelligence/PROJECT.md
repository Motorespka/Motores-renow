# Moto-Renow

Canonical identity: industrial/technical management and assistance system for electric-motor rewinding. It is separate from the newer second rewinding app.

Durable direction: evolve from workshop tooling toward industrial technical intelligence while preserving stability, history and validation.

Historical stack includes Python/Streamlit, OCR and SQLite/Supabase phases. The actual repository state always outranks this summary.

Core guardrails:
- stability > intelligence > features;
- incremental, testable changes;
- migrations/backups/rollback when database or auth is affected;
- calculation logic separated from UI and validated against known cases;
- preserve raw OCR evidence separately from corrected/validated data;
- never promote uncertain image-derived hypotheses into final technical facts without sufficient validation.