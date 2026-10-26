# Laboratory Work 1
## Secure REST API Development with CI/CD and Real CVE Vulnerability Analysis

**Variant:** N/A  
**Name:** Kong Mingzhe  
**HDU number:** 23320223  
**Course:** Information Security  
**Date:** 25 October 2026

## Purpose

Develop a small REST API with protections against SQL injection, cross-site scripting, and broken authentication; configure automated static and dependency security checks; and reproduce and analyze a real CVE in a controlled local container lab.

## 1. Stack and project

The application uses Python 3, Flask, SQLite, PyJWT, and Werkzeug's scrypt password hashing. The GitHub Actions workflow runs tests, Bandit SAST, OWASP Dependency-Check, and pip-audit SCA on push and pull request events. The API source is `app.py`; the workflow is `.github/workflows/ci.yml`.

## 2. API and security design

The service implements `POST /auth/login`, authenticated `GET /api/data`, authenticated `POST /api/posts`, and `GET /health`. SQLite statements bind user-controlled values through placeholders. Passwords are stored as salted scrypt hashes. A successful login returns a short-lived HS256 JWT; middleware verifies the signature, issuer, expiry, and required claims before protected handlers run. Returned post text is HTML-escaped. Input types and lengths are checked.

The seeded account (`student / ChangeMe123!`) is for the loopback-only educational demonstration; it must not be exposed to a shared network. The app requires an environment-provided JWT secret and binds to 127.0.0.1 by default.

## 3. CI/CD and scanners

The workflow runs Bandit (SAST), OWASP Dependency-Check and pip-audit (SCA), and pytest on pushes and pull requests. It uploads scanner reports as the `security-reports` artifact. Dependency-Check scans the pinned `requirements.txt` with its experimental Python analyzer enabled and writes an HTML report; pip-audit is retained as an additional Python-focused check. The Bandit B105 alert on the literal `Bearer` is a false positive: this is the standard HTTP authentication scheme label, not a credential; the source documents that narrow suppression.

### Local results

On 2026-10-25, the local checks completed with:

- pytest: **4 passed**.
- Bandit: **0 unsuppressed findings**.
- pip-audit: **no known vulnerabilities** in the 3 pinned runtime dependencies.
- `pip check`: **no broken requirements**.

JSON outputs are in `evidence/`. These results were produced locally. The earlier workflow was verified by [GitHub Actions run 40263674907](https://github.com/Fredy0102/Information-Security_23320223/actions/runs/40263674907), commit `c747841`. That job completed successfully in 29 seconds, but it predates the OWASP Dependency-Check step and therefore is not evidence that the new scan ran. Verify the latest run after this change; the `security-reports` artifact should include the HTML Dependency-Check report. The earlier run showed the expected Bandit B105 suppression notice, no known vulnerabilities from pip-audit, **4 passed** API tests, and a successful artifact upload.

Screenshots from the run:

![GitHub Actions Bandit, pip-audit, and artifact upload results](evidence/github-actions-c747841-security-scans.png)

![GitHub Actions pytest result and successful job cleanup](evidence/github-actions-c747841-tests-and-cleanup.png)

## 4. CVE analysis: CVE-2018-10933

CVE-2018-10933 is an authentication-bypass flaw in the libssh server implementation. Affected servers could accept an SSH2_MSG_USERAUTH_SUCCESS message sent by the client before a valid authentication request, incorrectly treating the client as authenticated. This can expose server resources available to the resulting session. The official advisory identifies libssh 0.8.4 and 0.7.6 as fixed releases. References: [libssh security advisory](https://www.libssh.org/security/advisories/CVE-2018-10933.txt) and [Vulhub CVE-2018-10933 lab](https://github.com/vulhub/vulhub/tree/master/libssh/CVE-2018-10933).

The demonstration used disposable local containers and ran only `id` after the bypass, confirming the session's container identity. It did not access host files or run arbitrary commands. Real impact depends on server version, configuration, and the privileges of the server process.

## 5. Reproduction and verification record

The local Docker comparison used loopback-only port mappings: vulnerable libssh 0.8.1 at `127.0.0.1:2222` and fixed libssh 0.8.4 at `127.0.0.1:2223`. The same localhost-only proof sent the authentication-success protocol message and attempted to open a session that runs `id`.

| Test | Observed response | Result |
|---|---|---|
| libssh 0.8.1 vulnerable service | `uid=0(root) gid=0(root) groups=0(root)` without supplying credentials | Authentication bypass reproduced in the container |
| libssh 0.8.4 fixed service | The server did not open a command channel; the proof timed out opening it | The same bypass did not succeed |

The lab steps are: change to `cve-lab/CVE-2018-10933`; run `docker compose up --build -d`; create a Python virtual environment and install `requirements.txt`; run `python verify_local.py --port 2222` against vulnerable 0.8.1; run the same proof with `--port 2223` against fixed 0.8.4; then clean up with `docker compose down --rmi local`. The proof is hardcoded to loopback and only runs `id`. Detailed instructions and recorded outputs are in `README.md`, `cve-lab/CVE-2018-10933/README.md`, and `evidence/CVE-2018-10933-results.md`. The results file records the observed fixed result (channel timeout/closure), rather than assuming a particular protocol error code. Actual terminal screenshots for these two CVE results still need to be captured during a run; the checked-in record is text, not a screenshot.

## 6. Deliverables

Included: API source, pinned runtime and development requirements, tests, GitHub Actions workflow, this report, API/CI screenshots, local scanner JSON reports, and the vulnerable/fixed CVE lab instructions and text observations. The repository is public at [Information-Security_23320223](https://github.com/Fredy0102/Information-Security_23320223). The latest Actions run and `security-reports` artifact must be checked after the new Dependency-Check step is pushed. CVE terminal screenshots are not yet included.

## 7. Control questions

1. **Why bcrypt/scrypt rather than SHA-256?** Password hashing should be intentionally slow and salted. Fast SHA-256 supports far more guesses per second; a password hashing algorithm raises the cost of offline brute force, and unique salts prevent equal passwords from producing equal stored values.
2. **SAST and DAST:** SAST analyzes code without executing the service. DAST probes a running service and evaluates its observable responses.
3. **JWT:** The header describes the token and algorithm, the payload contains claims such as subject and expiry, and a signature protects integrity and authenticity. A server checks the signature and relevant claims. Ordinary signed JWT payloads are readable, not encrypted.
4. **Dependency audit risks:** A project can silently inherit known vulnerabilities, compromised or abandoned packages, and risky transitive dependencies. Auditing makes those risks visible for remediation.
5. **Docker and Vulhub:** They package known vulnerable versions in reproducible environments that can be started, compared, and removed. This limits host modification and improves repeatability, provided the lab remains isolated.
