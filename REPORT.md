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

The application uses Python 3, Flask, SQLite, PyJWT, and Werkzeug's scrypt password hashing. The GitHub Actions workflow runs tests, Bandit SAST, and pip-audit SCA on push and pull request events. The API source is `app.py`; the workflow is `.github/workflows/ci.yml`.

## 2. API and security design

The service implements `POST /auth/login`, authenticated `GET /api/data`, authenticated `POST /api/posts`, and `GET /health`. SQLite statements bind user-controlled values through placeholders. Passwords are stored as salted scrypt hashes. A successful login returns a short-lived HS256 JWT; middleware verifies the signature, issuer, expiry, and required claims before protected handlers run. Returned post text is HTML-escaped. Input types and lengths are checked.

The seeded account (`student / ChangeMe123!`) is for the loopback-only educational demonstration; it must not be exposed to a shared network. The app requires an environment-provided JWT secret and binds to 127.0.0.1 by default.

## 3. CI/CD and scanners

The workflow runs Bandit (SAST), pip-audit (SCA), and pytest on pushes and pull requests. It uploads JSON scanner reports as the `security-reports` artifact. The Bandit B105 alert on the literal `Bearer` is a false positive: this is the standard HTTP authentication scheme label, not a credential; the source documents that narrow suppression.

### Local results

On 2026-10-25, the local checks completed with:

- pytest: **4 passed**.
- Bandit: **0 unsuppressed findings**.
- pip-audit: **no known vulnerabilities** in the 3 pinned runtime dependencies.
- `pip check`: **no broken requirements**.

JSON outputs are in `evidence/`. These results were produced locally. The first successful GitHub Actions run for this update is [run 40181922796](https://github.com/Fredy0102/Information-Security_23320223/actions/runs/40181922796); its test, SAST, SCA, and artifact-upload steps all completed successfully.

## 4. CVE analysis: CVE-2021-41773

Apache HTTP Server 2.4.49 introduced a path-normalization flaw. Under vulnerable access-control configuration, encoded dot segments can traverse outside the intended document root. Apache 2.4.50's fix was incomplete for the related CVE-2021-42013; 2.4.51 contains the fix. References: [Apache HTTP Server security advisories](https://httpd.apache.org/security/vulnerabilities_24.html) and [Vulhub CVE-2021-41773 lab](https://github.com/vulhub/vulhub/tree/master/httpd/CVE-2021-41773).

The impact demonstrated here is file disclosure from the disposable container. CGI was not enabled and no command execution was attempted. Real impact depends on the server version and access-control configuration.

## 5. Reproduction and verification record

The local Docker comparison used loopback-only port mappings: vulnerable Apache 2.4.49 at `127.0.0.1:8181`, fixed Apache 2.4.51 at `127.0.0.1:8182`.

The documented traversal request was sent using curl's `--path-as-is` option to preserve encoded dot segments:

```sh
curl -i --path-as-is 'http://127.0.0.1:8181/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd'
curl -i --path-as-is 'http://127.0.0.1:8182/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd'
```

| Test | Observed response | Result |
|---|---|---|
| Apache 2.4.49 vulnerable configuration | HTTP 200; body contained a `root:` entry from the container `/etc/passwd` | File disclosure reproduced |
| Apache 2.4.51 fixed version | HTTP 400 Bad Request; body contained no `root:` entry | Same file disclosure was blocked |

The complete safe excerpt and lab setup are recorded in `evidence/CVE-2021-41773-results.md` and `cve-lab/CVE-2021-41773/README.md`. After the comparison, `docker compose --profile vulnerable --profile fixed down --rmi local` stopped and removed the containers, network, and locally built image.

## 6. Deliverables

Included: API source, pinned runtime and development requirements, tests, GitHub Actions workflow, this report, local scanner JSON reports, and the vulnerable/fixed CVE lab instructions and observations. The repository is public at [Information-Security_23320223](https://github.com/Fredy0102/Information-Security_23320223). The successful Actions run and downloadable `security-reports` artifact are available at [run 40181922796](https://github.com/Fredy0102/Information-Security_23320223/actions/runs/40181922796).

## 7. Control questions

1. **Why bcrypt/scrypt rather than SHA-256?** Password hashing should be intentionally slow and salted. Fast SHA-256 supports far more guesses per second; a password hashing algorithm raises the cost of offline brute force, and unique salts prevent equal passwords from producing equal stored values.
2. **SAST and DAST:** SAST analyzes code without executing the service. DAST probes a running service and evaluates its observable responses.
3. **JWT:** The header describes the token and algorithm, the payload contains claims such as subject and expiry, and a signature protects integrity and authenticity. A server checks the signature and relevant claims. Ordinary signed JWT payloads are readable, not encrypted.
4. **Dependency audit risks:** A project can silently inherit known vulnerabilities, compromised or abandoned packages, and risky transitive dependencies. Auditing makes those risks visible for remediation.
5. **Docker and Vulhub:** They package known vulnerable versions in reproducible environments that can be started, compared, and removed. This limits host modification and improves repeatability, provided the lab remains isolated.
