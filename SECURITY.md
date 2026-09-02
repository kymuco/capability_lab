# Security and Privacy Reporting

Capability Lab handles models and records that may describe a person's capabilities, evidence, development history, or observed activity. Privacy failures therefore belong in the project's security boundary even when they are not conventional remote-code-execution vulnerabilities.

## What to report privately

Please use a private reporting channel for issues involving:

- credentials, tokens, keys, or secrets;
- accidental publication of person-scoped records or Pilot participant data;
- paths that allow private `.local/` data to enter tracked repository content;
- provenance or identity-binding failures that could silently rewrite governed records;
- authorization or authority-boundary bypasses;
- security-sensitive dependency or CI issues;
- any vulnerability whose public disclosure would expose users before a fix is available.

## Reporting

When the repository's GitHub private vulnerability reporting / Security Advisory flow is available, use **Report a vulnerability** rather than a public issue.

If private vulnerability reporting is unavailable, open a public issue containing only a request for a private contact channel. Do **not** include exploit details, credentials, personal data, private payloads, or other sensitive information in that issue.

A useful private report includes:

- affected revision or version;
- affected component;
- reproduction steps using synthetic data where possible;
- impact and violated boundary;
- whether any real sensitive data was exposed;
- suggested remediation, if known.

## Public research issues

Ordinary correctness bugs, reproducibility problems, documentation errors, and non-sensitive architecture questions may be reported publicly.

## Scope note

Capability Lab is experimental research software. Its epistemic and governance checks are not a substitute for application-level authentication, operating-system security, legal authorization, professional licensing, or human review where those are required.
