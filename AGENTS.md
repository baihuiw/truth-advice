# Working in this repository

- Paid runs only after the owner approves the scope and the cap in their own words; `scripts/run.py prepare` records
  that in `runs/<name>/approval.json` before any billed call. Every model call goes through `ta.client.Client` (ledger,
  cache, cap).
- The API key comes from the environment and is never printed, logged or written to a file.
- Worlds are fictional: invented people, organisations and places; structures may borrow from fiction, surfaces may not.
  Every world passes `ta.world.validate`; generated worlds also pass the author's gates.
- A simulated user only ever sees its own view (`ta.world.fact_lines`); partially known facts are written as the party's
  own version (`known_by`: "yes", "full: ...", "partial: ..."). The target sees only the deployment prompt, the memory
  file and the conversation.
- Commit only when the owner asks; no co-author or tool attribution lines in commits.
- Report measurement changes as corrections in the run's approval file and re-code from the cache rather than re-running
  the models.
