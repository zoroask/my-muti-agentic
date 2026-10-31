# Requirement Audit — reference lists

## Vague words (check A)
fast, easy, secure, user-friendly, etc., and/or, as appropriate, support, handle

## Coverage checklist (check B)
- data: sources, formats, volume, retention, privacy
- users and roles
- error and edge cases: empty, invalid, duplicate, large, interrupted
- data lifecycle: for every thing the system stores, who can create, read, update and delete it; a missing edit, delete or undo is a gap
- quality: performance, security, accessibility, language, logging, backup
- environment: OS, install, update, run schedule, offline
- integrations and interfaces
- out of scope
- success measure

## Conflict types (check C)
- direct contradiction
- implicit dependency — a requirement needs something no requirement provides, e.g. a trend over months needs stored history
- quality trade-off — e.g. security vs convenience
- constraint clash — e.g. offline vs cloud sync, scope vs deadline
- overlap or duplicate
- same term with different meanings
