# Work 1 — Secure REST API Development with CI/CD and Real CVE Analysis

**Student:** Kong Mingzhe · **HDU number:** 23320223 · **Variant:** N/A

## Project

A small Python 3 / Flask REST API with SQLite, signed JWT bearer tokens, scrypt password hashes, parameterized SQL, and output escaping. It is an educational example and is not production-hardened.

### Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python app.py
```

The first run creates `app.db` and a lab-only account: `student / ChangeMe123!`. The API binds to loopback (127.0.0.1) by default; do not expose the sample account or service to a shared network.

### API

| Method | Path | Authentication | Description |
| --- | --- | --- | --- |
| POST | `/auth/login` | None | JSON `{"login":"student","password":"ChangeMe123!"}`; returns a short-lived JWT on success |
| GET | `/api/data` | Bearer JWT | Returns posts; responds 401 without a valid token |
| POST | `/api/posts` | Bearer JWT | Creates a post from `{"title":"…","body":"…"}` |
| GET | `/health` | None | Liveness response |

Example:

```sh
curl -i http://127.0.0.1:5000/api/data
curl -sS -X POST http://127.0.0.1:5000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"student","password":"ChangeMe123!"}'
# Copy access_token from the JSON response into TOKEN before the next request.
curl -i http://127.0.0.1:5000/api/data -H "Authorization: Bearer $TOKEN"
```

## Security controls

- **SQL injection:** SQLite statements bind values with `?` placeholders. User-controlled values never become SQL syntax.
- **XSS:** API responses are JSON; `title` and `body` are also HTML-escaped before return so a client that renders them as markup receives inert text. Clients should still use safe text APIs and apply context-appropriate encoding.
- **Authentication:** Passwords are stored as Werkzeug scrypt hashes, never plaintext. Login verifies the hash and issues an HS256 JWT with issuer, subject, issue time, and expiration. Middleware requires a Bearer token and verifies signature, issuer, and required claims. JWT secret is read from the environment and startup fails if absent.
- **Input handling:** JSON types and lengths are checked. Debug mode is disabled.

## CI security scanning

GitHub Actions runs Bandit (SAST), pip-audit (SCA), and pytest on every push and pull request. It uploads scanner JSON reports as the `security-reports` artifact. The first successful run for this update is [Actions run 40181922796](https://github.com/Fredy0102/Information-Security_23320223/actions/runs/40181922796). The local scan results for this checkout are in `evidence/`.

## CVE study: CVE-2018-10933

The practical comparison uses libssh 0.8.1 (vulnerable) and 0.8.4 (fixed). The flaw is an SSH server authentication bypass: a vulnerable server may accept a client-sent authentication-success message before credentials are checked. In the isolated local lab, the vulnerable instance allowed the proof to run the harmless `id` command as container root; the 0.8.4 instance rejected the bypass before a command channel opened. Both ports bind only to `127.0.0.1`. See the [official libssh advisory](https://www.libssh.org/security/advisories/CVE-2018-10933.txt) and [Vulhub's reproduction](https://github.com/vulhub/vulhub/tree/master/libssh/CVE-2018-10933).

Exact setup and observations are in [`cve-lab/CVE-2018-10933/README.md`](cve-lab/CVE-2018-10933/README.md) and [`evidence/CVE-2018-10933-results.md`](evidence/CVE-2018-10933-results.md).

## Local verification

Run from the repository root:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
bandit -r app.py -f json -o evidence/bandit-report.json
pip-audit -r requirements.txt --format json --output evidence/pip-audit-report.json
python -m pip check
```

On 2026-10-25: 4 pytest tests passed; Bandit reported zero unsuppressed findings (the standard `Bearer` auth-scheme label is explicitly suppressed as a B105 false positive); pip-audit found no known vulnerabilities in the three pinned runtime dependencies; `pip check` found no broken requirements. These are local results, not a claim about the GitHub-hosted workflow.

## Control questions

1. **Why bcrypt/scrypt rather than SHA-256?** Password hashing should be intentionally slow and salted. Fast SHA-256 supports far more guesses per second; a password hashing algorithm raises the cost of offline brute force and unique salts prevent equal passwords from producing equal stored values.
2. **SAST vs DAST?** SAST examines source or bytecode without running the application and can locate risky code paths early. DAST sends requests to a running system and observes externally visible behavior; it can find runtime issues but does not directly identify every root cause.
3. **How does JWT work?** A JWT carries claims in a header and payload, plus a signature over the encoded parts. The server validates the signature with its configured key and checks claims such as issuer and expiry. A signed JWT is not automatically encrypted, so secrets must not be placed in its payload.
4. **Risks of not auditing dependencies?** Known vulnerable or abandoned packages can introduce exploitable flaws, license or supply-chain risk, and hidden transitive dependencies. An inventory and timely update process help identify and prioritize these issues.
5. **Why Docker and Vulhub?** Containers make vulnerable versions reproducible and easier to reset, while Vulhub supplies documented, isolated compose environments. This reduces host changes and supports before/after comparison, though network isolation and cleanup are still necessary.

## Submission note

The linked Actions run completed successfully, including the tests, SAST, SCA, and report upload. The course manual's preferred SCA tool should be confirmed with the instructor; this Python project uses pip-audit for its pinned dependencies.
