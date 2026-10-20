# Laboratory Work 1
## Secure REST API Development with CI/CD and Real CVE Vulnerability Analysis

**Variant:** N/A  
**Name:** Kong Mingzhe  
**HDU number:** 23320223  
**Course:** Information Security  
**Date:** 20 October 2026

## Purpose

To develop a small REST API with basic protections against injection, cross-site scripting, and broken authentication; configure automated static and dependency security checks; and study the root cause and remediation of CVE-2018-1000656 in a controlled Vulhub environment.

## 1. Stack and project

The application uses Python 3, Flask, SQLite, PyJWT, and Werkzeug's scrypt password hashing. GitHub Actions is configured for push and pull request events. The API code and workflow are in this submission folder.

## 2. API and security design

The service implements `POST /auth/login`, authenticated `GET /api/data`, authenticated `POST /api/posts`, and `GET /health`. SQLite statements bind all user-controlled values through placeholders. Passwords are stored as scrypt hashes. A successful login returns a short-lived HS256 JWT; middleware verifies signature, issuer, expiry, and required claims before protected handlers run. Returned post text is HTML-escaped. Input types and lengths are checked.

The seeded account (`student / ChangeMe123!`) is for local demonstration only. The app requires an environment-provided JWT secret and binds to loopback by default.

## 3. CI/CD and scanners

The workflow runs Bandit (SAST), pip-audit (SCA), and pytest on each push and pull request. It uploads JSON scanner reports as workflow artifacts. The workflow configuration is present at `.github/workflows/ci.yml`.

**Run result and screenshots:** Not available yet. The workflow has not been published or run remotely, so this report does not claim a passing pipeline or zero findings. Add actual GitHub Actions screenshots after running the workflow.

## 4. CVE analysis

Selected vulnerability: **CVE-2018-1000656**, affecting Flask before 0.12.3. Improper validation in JSON decoding can cause excessive memory consumption and denial of service when crafted JSON using a non-text-related encoding is handled. This is an input-validation flaw with an availability impact. The lab manual suggests a Vulhub Flask environment, but the exact directory and README should be checked against the current Vulhub revision before execution.

**Root cause:** a request body reaches the affected JSON decoding logic without adequate validation of the relevant encoding; processing can consume unusually large memory. This is not SQL injection or code execution. The principal impact described is denial of service.

**Fix:** use Flask 0.12.3 or later, preferably a currently supported release that remains compatible with the environment. This project uses Flask 3.1.3. For the isolated Vulhub reproduction, patch the environment's version pin and rebuild, then replay the identical documented request and verify that ordinary JSON still works.

## 5. Reproduction and verification record

The vulnerable and fixed Vulhub containers have **not** been run in this environment. Docker was unavailable in the current shell, and outbound GitHub access failed. Consequently, no attack commands, response captures, container logs, screenshots, or before/after claims are fabricated here.

Complete this section after running the selected environment according to its own README:

- Vulhub revision and directory: pending
- Exact documented request/command: pending
- Vulnerable version and observed result: pending
- Root cause evidence from source/configuration: pending
- Changed files and fixed version: pending
- Same request against fixed service: pending
- Regression request and result: pending
- Screenshots: pending

## 6. Deliverables

Included: API source, requirements, tests, GitHub Actions workflow, README, this report, and a Vulhub fix-folder placeholder. Public repository URL and successful workflow URL remain pending publication and execution.

## 7. Control questions

1. **Why bcrypt/scrypt rather than SHA-256?** Password hashing should be intentionally slow and salted. Fast SHA-256 supports far more guesses per second; a password hashing algorithm raises the cost of offline brute force and unique salts prevent equal passwords from producing equal stored values.
2. **SAST and DAST:** SAST analyzes code without executing the service. DAST probes a running service and evaluates its observable responses.
3. **JWT:** The header describes the token and algorithm, the payload contains claims such as subject and expiry, and a signature protects integrity/authenticity. A server checks the signature and relevant claims. Ordinary signed JWT payloads are readable, not encrypted.
4. **Dependency audit risks:** A project can silently inherit known vulnerabilities, compromised or abandoned packages, and risky transitive dependencies. Auditing makes those risks visible for remediation.
5. **Docker and Vulhub:** They package known vulnerable versions in reproducible environments that can be started, compared, and removed. This limits host modification and improves repeatability, provided the lab remains isolated.
