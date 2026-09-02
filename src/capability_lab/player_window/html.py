"""Dependency-free, self-contained HTML renderer for PR9 Player Window."""

from __future__ import annotations

from html import escape

from capability_lab.state import DimensionConflictStatus, DimensionStanding

from .core import PlayerWindow


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _standing_text(standing: DimensionStanding, conflict: DimensionConflictStatus) -> str:
    base = {
        DimensionStanding.SUPPORTED: "Supported — scoped",
        DimensionStanding.INSUFFICIENT: "Insufficient represented support",
        DimensionStanding.UNKNOWN: "Unknown",
    }[standing]
    if conflict is DimensionConflictStatus.UNRESOLVED:
        return f"{base} — unresolved conflict"
    if conflict is DimensionConflictStatus.RESOLVED_BY_POLICY:
        return f"{base} — conflict resolved by policy"
    return base


def _meta(label: str, value: object) -> str:
    return f'<div class="meta-row"><span>{_e(label)}</span><code>{_e(value)}</code></div>'


def _capabilities(window: PlayerWindow) -> str:
    if not window.capabilities:
        return ""
    cards = []
    for capability in window.capabilities:
        dimensions = []
        for dimension in capability.dimensions:
            claims = ""
            if dimension.claims:
                claim_items = []
                for claim in dimension.claims:
                    tags = f"<div class=\"tags\">{_e(', '.join(claim.scope_tags))}</div>" if claim.scope_tags else ""
                    claim_items.append(
                        '<div class="source-block"><div class="eyebrow">Supported claim</div>'
                        f'<div class="source-title">{_e(claim.statement)}</div>'
                        f'<div class="muted">Scope: {_e(claim.scope_description)}</div>{tags}'
                        f'<div class="tiny">claim {_e(claim.claim_id)}</div></div>'
                    )
                claims = "".join(claim_items)
            evaluations = ""
            if dimension.evaluations:
                evaluations = '<details><summary>Basis evaluations</summary>' + "".join(
                    '<div class="tiny source-line">'
                    f'{_e(item.evaluation_id)} · {_e(item.conclusion.value)} · conflict={_e(item.conflict_status.value)} · '
                    f'policy={_e(item.policy_ref)} · evaluator={_e(item.evaluator_kind)}:{_e(item.evaluator_ref)}'
                    '</div>'
                    for item in dimension.evaluations
                ) + '</details>'
            dimensions.append(
                '<article class="dimension">'
                f'<div class="dimension-head"><div><div class="eyebrow">{_e(dimension.dimension_key)}</div>'
                f'<h3>{_e(dimension.name)}</h3></div><div class="status">{_e(_standing_text(dimension.standing, dimension.conflict_status))}</div></div>'
                f'<p class="muted">{_e(dimension.description)}</p>'
                f'<p>{_e(dimension.rationale)}</p>{claims}{evaluations}</article>'
            )
        cards.append(
            '<section class="card capability">'
            '<div class="eyebrow">Capability state</div>'
            f'<h2>{_e(capability.concept_name)}</h2><p>{_e(capability.concept_definition)}</p>'
            f'{_meta("Exact concept", capability.concept_ref)}{_meta("Source state", capability.state_id)}'
            f'{_meta("Frame", f"{capability.frame_name} · {capability.frame_ref}")}'
            f'{_meta("State as of", capability.as_of.isoformat())}{_meta("Derived at", capability.derived_at.isoformat())}'
            '<details><summary>State provenance</summary>'
            f'{_meta("Policy", capability.state_policy_ref)}{_meta("Deriver", f"{capability.state_deriver_kind}:{capability.state_deriver_ref}")}'
            '</details><div class="dimension-grid">' + "".join(dimensions) + '</div></section>'
        )
    return '<section><div class="section-title"><span>Capability state</span><small>Selected state records · complete frame dimensions</small></div>' + "".join(cards) + '</section>'


def _history(window: PlayerWindow) -> str:
    if not window.achievements and not window.milestones:
        return ""
    items = []
    for achievement in window.achievements:
        note = f'<p class="muted">Record note: {_e(achievement.record_note)}</p>' if achievement.record_note else ""
        variant = f'<div class="pill">Variant · {_e(achievement.variant)}</div>' if achievement.variant else ""
        items.append(
            '<article class="timeline-item"><div class="dot"></div><div class="eyebrow">Achievement · historical accomplishment</div>'
            f'<h3>{_e(achievement.family_name)}</h3>{variant}<p>{_e(achievement.context)}</p>{note}'
            f'{_meta("Achieved", achievement.achieved_at.isoformat())}{_meta("Recorded", achievement.recorded_at.isoformat())}'
            f'{_meta("Family", achievement.family_ref)}'
            '<details><summary>Qualification context</summary>'
            f'{_meta("Policy", achievement.qualification_policy_ref)}{_meta("Qualifier", f"{achievement.qualifier_kind}:{achievement.qualifier_ref}")}</details></article>'
        )
    for milestone in window.milestones:
        items.append(
            '<article class="timeline-item"><div class="dot"></div><div class="eyebrow">Personal milestone · recorded history</div>'
            f'<h3>{_e(milestone.title)}</h3><p>{_e(milestone.description)}</p>'
            f'<div class="source-block"><div class="eyebrow">Recorded significance note</div><div>{_e(milestone.significance_note)}</div></div>'
            f'{_meta("Occurred", milestone.occurred_at.isoformat())}{_meta("Recorded", milestone.recorded_at.isoformat())}'
            '<details><summary>Recorder context</summary>'
            f'{_meta("Policy", milestone.recording_policy_ref)}{_meta("Recorder", f"{milestone.recorder_kind}:{milestone.recorder_ref}")}</details></article>'
        )
    return '<section><div class="section-title"><span>History</span><small>Historical records · not current readiness</small></div><div class="timeline">' + "".join(items) + '</div></section>'


def _legend(window: PlayerWindow) -> str:
    legend = window.legend
    if legend is None:
        return ""
    entries = "".join(
        '<article class="legend-entry">'
        f'<div class="eyebrow">Sources · {_e(", ".join(entry.source_refs))}</div>'
        f'<h3>{_e(entry.heading)}</h3><p>{_e(entry.narrative)}</p></article>'
        for entry in legend.entries
    )
    return (
        '<section><div class="section-title"><span>Narrative projection</span><small>Selected Legend · not identity or source history</small></div>'
        '<section class="card legend"><div class="eyebrow">Personal Legend</div>'
        f'<h2>{_e(legend.title)}</h2><p>{_e(legend.summary)}</p>'
        f'{_meta("Legend", legend.legend_id)}{_meta("As of", legend.as_of.isoformat())}{_meta("Generated", legend.generated_at.isoformat())}'
        '<details><summary>Projection provenance</summary>'
        f'{_meta("Policy", legend.policy_ref)}{_meta("Generator", f"{legend.generator_kind}:{legend.generator_ref}")}</details>'
        f'<div class="legend-grid">{entries}</div></section></section>'
    )


def _frontier(window: PlayerWindow) -> str:
    frontier = window.frontier
    if frontier is None:
        return ""
    candidates = []
    for candidate in frontier.candidates:
        focus = '<div class="pill">Explicit focus in this projection request</div>' if candidate.explicit_focus else ""
        reasons = "".join(f'<li>{_e(item)}</li>' for item in candidate.adjacency_reasons)
        assessed = "".join(f'<li>{_e(item)}</li>' for item in candidate.assessed_prerequisites)
        unassessed = "".join(f'<li>{_e(item)}</li>' for item in candidate.unassessed_prerequisites)
        details = ""
        if reasons or assessed or unassessed:
            details = '<details><summary>Why this is visible</summary>'
            if reasons:
                details += f'<div class="eyebrow">Direct adjacency</div><ul>{reasons}</ul>'
            if assessed:
                details += f'<div class="eyebrow">Assessed categorical prerequisites</div><ul>{assessed}</ul>'
            if unassessed:
                details += f'<div class="eyebrow">Not assessed in this projection</div><ul>{unassessed}</ul>'
            details += '</details>'
        candidates.append(
            '<article class="frontier-item"><div class="eyebrow">Could be considered</div>'
            f'<h3>{_e(candidate.concept_name)}</h3><div class="tiny">{_e(candidate.concept_ref)}</div>{focus}{details}</article>'
        )
    gaps = []
    for gap in frontier.prerequisite_gaps:
        dims = "".join(
            '<div class="gap-dim"><strong>' + _e(item.dimension_key) + '</strong><span>' +
            _e(item.kind.value.replace('_', ' ')) +
            (f' · conflict={_e(item.conflict_status.value)}' if item.conflict_status else '') + '</span></div>'
            for item in gap.dimension_gaps
        )
        gaps.append(
            '<article class="gap"><div class="eyebrow">Prerequisite evidence gap</div>'
            f'<h3>{_e(gap.target_name)} ↔ {_e(gap.prerequisite_name)}</h3><p class="muted">{_e(gap.relation_description)}</p>'
            f'<div>{dims}</div><p class="notice">Evidence gap does not mean capability absence, prohibition, readiness, safety, or permission.</p>'
            f'{_meta("Frame", gap.frame_ref)}{_meta("Selected prerequisite state", gap.state_id or "none")}</article>'
        )
    exploration = "".join(
        '<article class="exploration"><div class="eyebrow">Explicit exploration</div>'
        f'<h3>{_e(item.concept_name)}</h3><div class="tiny">{_e(item.concept_ref)}</div><p>{_e(item.rationale)}</p></article>'
        for item in frontier.exploration
    )
    return (
        '<section><div class="section-title"><span>Frontier</span><small>Advisory projection · not recommendation or permission</small></div>'
        '<section class="card"><div class="eyebrow">Could be considered</div>'
        f'{_meta("Frontier", frontier.frontier_id)}<p class="muted">{_e(frontier.rationale)}</p>'
        '<div class="frontier-grid">' + "".join(candidates) + '</div>'
        + (f'<div class="subsection"><h3>Prerequisite evidence gaps</h3>{"".join(gaps)}</div>' if gaps else '')
        + (f'<div class="subsection"><h3>Explicit exploration</h3><div class="frontier-grid">{exploration}</div></div>' if exploration else '')
        + '<details><summary>Frontier provenance</summary>'
        f'{_meta("Policy", frontier.policy_ref)}{_meta("Deriver", f"{frontier.deriver_kind}:{frontier.deriver_ref}")}{_meta("Requester", f"{frontier.requester_kind}:{frontier.requester_ref}")}</details></section></section>'
    )


def render_player_window_html_v1(window: PlayerWindow) -> str:
    """Render a self-contained read-only local HTML document.

    The renderer accepts only PlayerWindow. It cannot select source records or derive
    state/frontier/history meaning. All source text is escaped before insertion.
    """
    if not isinstance(window, PlayerWindow):
        raise TypeError("window must be PlayerWindow")
    body = _capabilities(window) + _history(window) + _legend(window) + _frontier(window)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
<title>Capability Lab · Player Window</title><style>
:root{{--bg:#0b0d10;--panel:#12161c;--soft:#171d25;--line:#29313d;--text:#eef2f7;--muted:#9aa7b6;--accent:#d9e4f0}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1120px;margin:auto;padding:48px 22px 80px}}h1{{font-size:38px;margin:0 0 8px}}h2{{font-size:24px;margin:5px 0 10px}}h3{{font-size:16px;margin:3px 0 8px}}p{{margin:8px 0 13px}}code{{font-size:12px;color:#cdd8e5;overflow-wrap:anywhere}}.hero{{padding:28px 0 38px;border-bottom:1px solid var(--line);margin-bottom:34px}}.eyebrow{{font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:var(--muted);font-weight:700}}.muted,.tiny{{color:var(--muted)}}.tiny{{font-size:12px}}.section-title{{display:flex;justify-content:space-between;align-items:end;margin:36px 0 12px;font-size:20px;font-weight:700}}.section-title small{{font-size:12px;color:var(--muted);font-weight:500}}.card,.timeline-item,.frontier-item,.gap,.exploration{{border:1px solid var(--line);background:var(--panel);border-radius:16px;padding:20px;margin-bottom:12px}}.dimension-grid,.frontier-grid,.legend-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:18px}}.dimension,.legend-entry{{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:15px}}.dimension-head{{display:flex;justify-content:space-between;gap:15px}}.status,.pill{{font-size:12px;padding:5px 9px;border:1px solid var(--line);border-radius:999px;height:max-content}}.source-block{{border-left:2px solid #566579;padding:9px 12px;margin:10px 0;background:#10141a}}.source-title{{font-weight:650}}.meta-row{{display:flex;gap:12px;justify-content:space-between;border-top:1px solid var(--line);padding:7px 0}}.meta-row span{{color:var(--muted);font-size:12px}}details{{margin-top:12px}}summary{{cursor:pointer;color:#cbd7e4}}.timeline{{border-left:1px solid var(--line);padding-left:18px}}.timeline-item{{position:relative}}.dot{{position:absolute;width:8px;height:8px;border-radius:50%;background:var(--accent);left:-23px;top:26px}}.notice{{font-size:12px;color:#cbd7e4;border-left:2px solid #718399;padding-left:10px}}.gap-dim{{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding:7px 0}}.subsection{{margin-top:24px}}ul{{padding-left:20px}}@media(max-width:640px){{.section-title,.dimension-head,.meta-row{{align-items:flex-start;flex-direction:column}}h1{{font-size:30px}}}}
</style></head><body><main><header class="hero"><div class="eyebrow">Private local read model · not a person score</div><h1>Player Window</h1>
<p>What is represented as supported, unknown, insufficient, historical, narrative, frontier, or explicit exploration in this selected projection.</p>
{_meta("Subject", window.subject_ref)}{_meta("As of", window.as_of.isoformat())}{_meta("Generated", window.generated_at.isoformat())}
<details><summary>Window provenance</summary>{_meta("Window", window.window_id)}{_meta("Policy", window.policy_ref)}{_meta("Generator", f"{window.generator_ref.kind.value}:{window.generator_ref.ref}")}{_meta("Requester", f"{window.requester_ref.kind.value}:{window.requester_ref.ref}")}{_meta("Viewer", f"{window.viewer_ref.kind.value}:{window.viewer_ref.ref}")}</details></header>{body}
<footer class="tiny">Player Window is a selected read model. Displayed does not mean canonical; omitted does not mean absent. Local HTML is not publication or authorization.</footer></main></body></html>'''
