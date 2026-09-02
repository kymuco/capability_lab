# Contributing to Capability Lab

Capability Lab is experimental research software for evidence-grounded human
capability modeling. Research discussion, bug reports, architecture ideas, and
documentation feedback are welcome when they preserve the project's epistemic,
privacy, human-agency, and licensing boundaries.

## Before contributing

Please read:

- `README.md`
- `docs/constitution.md`
- `docs/architecture.md`
- `docs/vocabulary.md`
- `LICENSE`
- `LICENSE-HISTORY.md`
- `COMMERCIAL-LICENSING.md`

The following distinctions are foundational and must not be collapsed for
convenience:

```text
observation != evidence
EvidenceRecord != capability
claim != capability
accepted/current state != the person
progression != prescription
capability != permission or authority
```

A proposal that weakens one of these boundaries should explicitly identify the
changed invariant, why it is necessary, what new failure modes appear, and how
migration/governance should work.

## Privacy

Do not commit or attach real person-scoped capability records, private Pilot
workspaces, participant captures, credentials, tokens, private conversation
exports, or other sensitive payloads.

The `.local/` boundary is intentionally excluded from version control. Tests and
examples should use synthetic data unless a separate, explicit publication
policy says otherwise.

If you discover sensitive information in repository content, do not open a
public issue containing the information. Follow `SECURITY.md`.

## Development

Capability Lab requires Python 3.11 or newer.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

Changes should include focused tests for their contract and adversarial tests
for authority, mutation, serialization, provenance, replay, or privacy failure
modes where relevant.

## Pull requests

A good pull request should state:

- the problem and intended boundary;
- the exact authority the new code does and does not receive;
- compatibility or schema implications;
- tests added or changed;
- relevant adversarial cases;
- documentation changes for new normative terms or invariants.

Prefer narrow, reviewable changes over broad refactors that mix architecture
changes with unrelated cleanup.

Do not describe local tests or hosted CI as passing unless they were actually
observed on the stated source revision.

## Third-party contribution policy

Capability Lab uses a source-available public license together with separate
commercial licensing. Maintaining the ability to grant commercial licenses
requires a clear rights chain for copyrightable material included in the
project.

Until a dedicated Contributor License Agreement or equivalent
contributor-rights process is published, **substantive third-party
contributions are not accepted for inclusion**. This includes substantive code,
tests, documentation, examples, and other authored project material.

```text
PUBLIC SOURCE ACCESS
!= RIGHT TO RELICENSE A THIRD-PARTY CONTRIBUTION

COMMERCIAL LICENSING
=> CLEAR CONTRIBUTOR RIGHTS CHAIN
```

You are still welcome to:

- report bugs;
- propose architecture or research ideas;
- identify documentation errors;
- suggest tests or adversarial cases conceptually;
- discuss interoperability or use cases;
- submit a pull request for review when explicitly coordinated with the
  repository owner, understanding that substantive authored material cannot be
  merged until the required contributor-rights terms are in place.

Do not assume that the repository's PolyForm Noncommercial license is itself a
contributor agreement or that submitting a pull request automatically gives the
project owner rights to commercially relicense your contribution.

## Historical licensing note

Earlier distributed versions of Capability Lab may be governed by different
license terms. The current contribution policy applies to this public lineage
and does not claim to rewrite rights already granted for earlier copies.

See `LICENSE-HISTORY.md` for the concise licensing transition record.
