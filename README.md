# Capability Lab

**Evidence-grounded human capability modeling with explicit governance boundaries.**

Capability Lab is an experimental Python framework for representing what has been observed, what the
evidence can support, what remains uncertain, and what development paths may be worth considering —
without turning a model, score, recommendation, or product view into authority over the person.

> **Observation is not evidence. Evidence is not a claim. Supported is not mastery. Current is not permission.**

[Documentation](https://kymuco.github.io/capability_lab/) ·
[Architecture](docs/architecture.md) ·
[Constitution](docs/constitution.md) ·
[Consumer boundary](docs/consumer-boundary.md) ·
[Reference map](docs/reference/archive.md)

> **Source-available licensing:** the current distribution is offered under the
> [PolyForm Noncommercial License 1.0.0](LICENSE). Commercial use that requires rights beyond that public
> grant requires a [separate commercial license](COMMERCIAL-LICENSING.md), subject to fair use and other
> rights provided by applicable law. Historical Apache-2.0 releases keep the rights already granted for those
> versions; see [License history](LICENSE-HISTORY.md).

## Why Capability Lab

Most learning and professional systems lean on proxies: courses, titles, credentials, tests, or self-reported
skills. Capability Lab explores a different architecture built around provenance, explicit uncertainty,
append-only evaluation history, human review, and governed state transitions.

The system deliberately preserves distinctions that are easy to collapse:

```text
observation
!= evidence
!= interpretation
!= claim
!= evaluation
!= derived state
!= persisted state
!= accepted state
!= current state
!= progression advice
!= product/read projection
!= permission or authority
```

It does **not** attempt to compute a person's value, intelligence, destiny, professional license, or right to act.

## Current architecture

The generic public path now composes end to end:

```text
external observation
→ HUMAN-reviewed neutral evidence
→ governed interpretation and claim
→ conservative + domain-sufficient evaluation
→ complete-history capability state
→ persistence
→ explicit acceptance
→ explicit current-state selection
→ advisory progression + complete current profile
→ governed product/read snapshot
```

PR12.13 executably proves the generic observation path reaches governed current state through the public APIs.
PR12.14 extends that proof through PR11.9 progression, PR11.10 complete current profile, and the PR11.11
product/read boundary.

The product surface still has no capability write-back authority, and automatic closed-loop capability updates
remain **not authorized**.

## Stable consumer boundary

The current consumer contract is PR11.11 `CurrentStateGovernedPlayerWindow`.

A consumer may present governed current state and advisory progression. It does not choose the current state,
grant readiness or mastery, or turn a serialized snapshot into live authority.

Start with [Consume the governed read boundary](docs/consumer-boundary.md).

## Research lineage

Capability Lab began with Civilization Bootstrap Engineering as a demanding domain stress test. The repository
retains that research and Pilot history, while the generic PR12 path is deliberately independent of the
Pilot-specific production path.

See [Publication lineage](PUBLICATION.md) and the [reference/archive map](docs/reference/archive.md).

## Development

Requires Python 3.11+.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

Documentation development:

```bash
python -m pip install -e ".[docs]"
zensical build --clean --strict
```

Security and privacy-sensitive reports should follow [SECURITY.md](SECURITY.md).
Contribution guidance lives in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Capability Lab is **source-available**, not OSI open source, under the
[PolyForm Noncommercial License 1.0.0](LICENSE) (`PolyForm-Noncommercial-1.0.0`).

Commercial rights are available separately where a license from the project is required; see
[Commercial licensing](COMMERCIAL-LICENSING.md). The historical Apache-2.0 licensing era and exact final
Apache checkpoint are recorded in [LICENSE-HISTORY.md](LICENSE-HISTORY.md).
