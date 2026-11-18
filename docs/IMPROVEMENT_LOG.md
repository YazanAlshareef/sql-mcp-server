# Improvement log

## 2026-11-15, cycle 1

Baseline: 39 tests pass. ruff and mypy are not installed here, so there is no lint or type result.

### Done this cycle (branches awaiting review, not merged)

| Item | Branch | Result |
|---|---|---|
| Refuse single values over 1 MB (861b43d). Behaviour change: a string or blob over 1 MB now fails with "string or blob too big". The 500 row cap still applies, so one result can reach about 500 MB in total. Needs Python 3.11+ for `setlimit`. | fix/cap-value-length | Review passed |
| List up to 500 tables instead of cutting off at 100 (2d2472a). Behaviour change: databases with more than 500 tables were silently cut, and a real table could then be reported as unknown. | fix/list-tables-limit | Review passed |
| Make the client script fail when an attack is not rejected (5e4ba10). Script and CI only, server behaviour is unchanged. | fix/client-assert-attacks | Review passed |

Each branch was reviewed on its own against main (3e877a2).

### Not verified

- Test counts after each branch were not recorded for this log.
- `scripts/test_client.py` was not run during the audit.
- Memory use above 200 MB was not tested.
- Lint and type checks.

### Open issues for the owner

- README line 124 says who wrote the first draft. That conflicts with the rule of not mentioning it. It needs its own docs branch and an owner decision on the wording.
- Python 3.11+ is not declared anywhere in the repo, and the value cap now depends on it.

### Backlog, top 5 not yet done

1. Guard rejects valid read-only forms such as `SELECT(1)` and `(SELECT 1)` (sql_guard.py:61-63). Fails closed. Effort S, risk low. Changes behaviour: more queries accepted.
2. Row limit is silently clamped, and a bad type escapes as a raw error (db.py:59, server.py:19). Effort S, risk low.
3. Thin tests for the business tools: `monthly_sales` and `low_stock` have none (tests/test_business.py:32-52, server.py:46-55, 70-78). Effort M, risk low.
4. No direct tests for the guard edge cases such as unterminated quotes and bracket identifiers (sql_guard.py:26, 34, 44). Effort S, risk low.
5. No lint or type check, and none in CI (.github/workflows/ci.yml:19-21, requirements.txt:1-2). Effort M, risk low.

### Lessons

- A per-value cap is not a total cap. With 500 rows of 1 MB each, one result can still reach about 500 MB.
- The attack loop in the client script only printed results (scripts/test_client.py:40-42), so CI stayed green whatever the server did.
- The `list_tables` cut at 100 was not hit on the sample data, which has 8 tables. Only a test with a larger database shows it.

### Diagrams

Diagrams live on the docs/diagrams branch, in docs/diagrams/ (architecture.md, data-model.md, run-select-flow.md).

### Status

All branches are local and await the owner's approval. Nothing is pushed or merged.
