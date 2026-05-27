# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | Yes       |
| < 0.3   | No        |

## Reporting a vulnerability

If you discover a security vulnerability in soyuz-catalog, please
report it responsibly. **Do not open a public GitHub issue.**

Email **flo.max.hofstetter@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Affected version(s)
- Impact assessment (if known)

You will receive an acknowledgement within **48 hours** and a detailed
response within **7 days** outlining next steps.

## Disclosure policy

- Confirmed vulnerabilities will be fixed in a patch release as soon as
  possible.
- A security advisory will be published via GitHub Security Advisories
  once a fix is available.
- Credit will be given to the reporter unless they prefer to remain
  anonymous.

## Scope

The following are in scope:

- soyuz-catalog server code (`soyuz_catalog/`)
- The generated typed client (`soyuz-catalog-client/`)
- Docker images published to `ghcr.io/flohofstetter/soyuz-catalog`
- Python packages published to PyPI (`soyuz-catalog`, when published)

The following are **out of scope**:

- The infrastructure hosting your soyuz-catalog deployment
- The upstream Unity Catalog Java reference implementation (report
  to <https://github.com/unitycatalog/unitycatalog>)
- Third-party dependencies (report to the upstream maintainer)
- Compute engines (Spark, Trino, delta-rs) talking to soyuz
