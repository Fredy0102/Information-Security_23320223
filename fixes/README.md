# CVE fix artifacts

The coursework CVE comparison is CVE-2018-10933. The lab builds libssh 0.8.4
for the fixed comparison service, while the vulnerable service uses the
Vulhub-provided libssh 0.8.1 image. See
[`../cve-lab/CVE-2018-10933/Dockerfile.fixed`](../cve-lab/CVE-2018-10933/Dockerfile.fixed)
for the fixed build and
[`../evidence/CVE-2018-10933-results.md`](../evidence/CVE-2018-10933-results.md)
for observed verification results. The vulnerable and fixed tests were run
against localhost-only Docker ports.
