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

The first run creates `app.db` and an educational account: `student / ChangeMe123!`. Change this seed credential before any shared deployment. The server binds to loopback (127.0.0.1) by default.

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
curl -i http://127.0.0.1:5000/api/data -H "Authorization: Bearer $TOKEN"
```

## Security controls

- **SQL injection:** SQLite statements bind values with `?` placeholders. User-controlled values never become SQL syntax.
- **XSS:** API responses are JSON; `title` and `body` are also HTML-escaped before return so a client that renders them as markup receives inert text. Clients should still use safe text APIs and apply context-appropriate encoding.
- **Authentication:** Passwords are stored as Werkzeug scrypt hashes, never plaintext. Login verifies the hash and issues an HS256 JWT with issuer, subject, issue time, and expiration. Middleware requires a Bearer token and verifies signature, issuer, and required claims. JWT secret is read from the environment and startup fails if absent.
- **Input handling:** JSON type and length checks bound credential and post input. Debug mode is disabled.

## CI security scanning

GitHub Actions is configured in `.github/workflows/ci.yml` for every push and pull request. Bandit provides SAST; pip-audit checks pinned runtime dependencies for known advisories (SCA); JSON reports are uploaded as workflow artifacts; pytest then runs API checks.

**Evidence to add after publishing:** insert screenshots of a successful Actions run showing the Bandit and pip-audit steps and the uploaded reports. No remote run or scan screenshot is claimed in this local copy.

## Vulnerability study: CVE-2018-1000656

The manual recommends Flask CVE-2018-1000656. It affects Flask versions before 0.12.3: improper validation in JSON decoding can cause excessive memory use and denial of service when specially encoded JSON is processed. The remediation is to upgrade to Flask 0.12.3 or later; this project pins Flask 3.1.3. Sources: [NVD record](https://nvd.nist.gov/vuln/detail/CVE-2018-1000656), [Vulhub repository](https://github.com/vulhub/vulhub).

The lab manual suggests a Vulhub directory named `flask/CVE-2018-1000656`; that path and its README must be confirmed against the checked-out Vulhub revision before reproducing. The vulnerable service must only be exposed on an isolated local lab network. Do not expose it to a public interface.

### Reproduction and remediation evidence

**Status:** not yet executed. Docker was not available in the current shell and GitHub could not be reached from this environment; therefore no vulnerable-service output, fixed-service output, screenshots, public repository URL, or successful pipeline URL is asserted.

After confirming the environment README and image architecture:

1. Clone Vulhub and inspect the selected directory's README and compose file.
2. Start only the selected lab on an isolated local machine. Record the exact commands, requests, response, and container logs specified by that README. Do not improvise a payload; use only the documented request.
3. Record the root cause: affected Flask JSON decoding does not properly validate the relevant non-text encoding path, allowing excessive memory consumption (availability impact).
4. Apply the documented version fix in a copy of the environment: use Flask 0.12.3 or a supported patched release compatible with the sample app. Pin the fixed version; rebuild.
5. Replay the exact same documented request. Capture the safe response and a normal JSON request succeeding as regression evidence.
6. Add dated screenshots and exact commands to this section, then push to a public GitHub/GitLab repository and link the successful CI run here.

Do not describe the CVE as reproduced or fixed until those observations are captured. If the suggested Vulhub directory is absent, select an existing environment only after checking its README and adjust the report's CVE and fix analysis.

## Deliverables checklist

- [x] API source, dependency files, workflow, and local tests
- [x] README description, API usage, security controls, and CVE analysis
- [ ] Public Git repository URL: pending publication
- [ ] Successful CI run URL and actual SAST/SCA screenshots: pending execution
- [ ] Vulnerable and fixed Vulhub screenshots and exact observations: pending Docker lab execution
- [ ] Attach the selected Vulhub fix files if the environment was modified

## Control questions

1. **Why bcrypt instead of SHA-256 for passwords?** SHA-256 is designed to be fast, so attackers can try guesses at high rates, often with GPUs. bcrypt (and scrypt/Argon2) is deliberately costly and salts each password, making offline guessing more expensive and preventing identical passwords from having identical stored hashes.
2. **SAST vs DAST?** SAST examines source or bytecode without running the application and can locate risky code paths early. DAST sends requests to a running system and observes externally visible behavior; it can find runtime issues but does not directly identify every root cause.
3. **How does JWT work?** A JWT carries claims in a header and payload, plus a signature over the encoded parts. The server validates the signature with its configured key and checks claims such as issuer and expiry. A signed JWT is not automatically encrypted, so secrets must not be placed in its payload.
4. **Risks of not auditing dependencies?** Known vulnerable or abandoned packages can introduce exploitable flaws, license or supply-chain risk, and hidden transitive dependencies. An inventory and timely update process help identify and prioritize these issues.
5. **Why Docker and Vulhub?** Containers make vulnerable versions reproducible and easier to reset, while Vulhub supplies documented, isolated compose environments. This reduces host changes and supports before/after comparison, though network isolation and cleanup are still necessary.
