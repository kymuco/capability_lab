"""Cross-record validation for immutable PR7 history and legend snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from capability_lab.epistemics import EpistemicRecordSet

from .core import (
    AchievementBasisKind,
    AchievementFamilyCatalog,
    AchievementInstance,
    HistoryError,
    LegendSourceKind,
    MilestoneSourceKind,
    PersonalLegend,
    PersonalMilestoneEvent,
)


class InvalidHistoryRecordSet(HistoryError):
    pass


class InvalidLegendSet(HistoryError):
    pass


@dataclass(frozen=True, slots=True)
class PersonalHistoryRecordSet:
    """Private deterministic one-subject source-of-history snapshot."""

    subject_ref: object
    achievement_instances: tuple[AchievementInstance, ...] = ()
    milestone_events: tuple[PersonalMilestoneEvent, ...] = ()

    def __post_init__(self) -> None:
        from capability_lab.epistemics import CapabilitySubjectRef

        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidHistoryRecordSet("subject_ref must be CapabilitySubjectRef")
        achievements = _validated_tuple(
            self.achievement_instances,
            AchievementInstance,
            "achievement_instances",
        )
        milestones = _validated_tuple(
            self.milestone_events,
            PersonalMilestoneEvent,
            "milestone_events",
        )
        achievements = tuple(sorted(achievements, key=lambda item: item.achievement_id))
        milestones = tuple(sorted(milestones, key=lambda item: item.milestone_id))
        _reject_duplicates(
            (item.achievement_id for item in achievements),
            "achievement instance id",
        )
        _reject_duplicates(
            (item.milestone_id for item in milestones),
            "milestone event id",
        )
        achievement_ids = {str(item.achievement_id) for item in achievements}
        milestone_ids = {str(item.milestone_id) for item in milestones}
        cross_type_ids = achievement_ids.intersection(milestone_ids)
        if cross_type_ids:
            raise InvalidHistoryRecordSet(
                "achievement and milestone ids must not collide within one personal-history snapshot: "
                f"{sorted(cross_type_ids)}"
            )
        for item in achievements:
            if item.subject_ref != self.subject_ref:
                raise InvalidHistoryRecordSet(
                    "achievement instance subject must match history-set subject"
                )
        for item in milestones:
            if item.subject_ref != self.subject_ref:
                raise InvalidHistoryRecordSet(
                    "milestone event subject must match history-set subject"
                )

        # A repeatable family may have many genuine instances, but the same exact
        # event-bearing basis cannot be replayed as a second instance of the same
        # stable family identity inside one snapshot. If one evidence/artifact ref
        # covers several real events, PR7 v1 has no per-event disambiguator and
        # therefore fails closed rather than manufacturing countable history.
        event_basis_by_family: dict[object, set[tuple[AchievementBasisKind, str]]] = {}
        for achievement in achievements:
            family_key = achievement.family_ref.family_id
            event_basis = {
                (basis.kind, basis.ref)
                for basis in achievement.basis_refs
                if basis.kind
                in {
                    AchievementBasisKind.EVIDENCE_RECORD,
                    AchievementBasisKind.EXTERNAL_ARTIFACT,
                }
            }
            used = event_basis_by_family.setdefault(family_key, set())
            overlap = used.intersection(event_basis)
            if overlap:
                repeated = sorted(f"{kind.value}:{ref}" for kind, ref in overlap)
                raise InvalidHistoryRecordSet(
                    "same event-bearing basis may not be replayed as multiple achievement "
                    f"instances of one stable family: {repeated}"
                )
            used.update(event_basis)

        for milestone in milestones:
            for source in milestone.source_refs:
                if source.kind is MilestoneSourceKind.ACHIEVEMENT_INSTANCE:
                    if source.ref not in achievement_ids:
                        raise InvalidHistoryRecordSet(
                            f"milestone references missing achievement instance: {source.ref}"
                        )
        object.__setattr__(self, "achievement_instances", achievements)
        object.__setattr__(self, "milestone_events", milestones)

    def validate_against_family_catalog(self, catalog: AchievementFamilyCatalog) -> None:
        if not isinstance(catalog, AchievementFamilyCatalog):
            raise InvalidHistoryRecordSet("catalog must be AchievementFamilyCatalog")
        by_id = {item.family_id: item for item in catalog.families}
        for achievement in self.achievement_instances:
            family = by_id.get(achievement.family_ref.family_id)
            if family is None:
                raise InvalidHistoryRecordSet(
                    f"achievement references family absent from catalog: {achievement.family_ref}"
                )
            if family.revision != achievement.family_ref.revision:
                raise InvalidHistoryRecordSet(
                    "family validation requires exact revision; silent latest-revision substitution is forbidden: "
                    f"achievement={achievement.family_ref}, catalog={family.ref}"
                )

    def validate_against_epistemics(self, records: EpistemicRecordSet) -> None:
        if not isinstance(records, EpistemicRecordSet):
            raise InvalidHistoryRecordSet("records must be EpistemicRecordSet")

        evidence = {str(item.evidence_id): item for item in records.evidence_records}
        claims = {str(item.claim_id): item for item in records.claims}
        evaluations = {str(item.evaluation_id): item for item in records.evaluations}
        internal_ids = set(evidence) | set(claims) | set(evaluations)

        achievements = {str(item.achievement_id): item for item in self.achievement_instances}
        milestones = {str(item.milestone_id): item for item in self.milestone_events}
        history_ids = set(achievements) | set(milestones)

        # PR7 history records are not PR2 evidence/provenance primitives. Within
        # one supplied cross-layer snapshot, exact history ids may not be relabeled
        # as generic artifact/system/external refs or payload refs to manufacture a
        # history -> epistemics -> history feedback cycle.
        for record in records.evidence_records:
            for source in record.provenance.sources:
                if source.ref in history_ids:
                    raise InvalidHistoryRecordSet(
                        "history record id may not be used as evidence provenance source; "
                        "history-to-evidence conversion requires a future explicit governed transformation"
                    )
            if any(ref in history_ids for ref in record.payload_refs):
                raise InvalidHistoryRecordSet(
                    "history record id may not be used as evidence payload ref within PR7 cross-validation"
                )
        for claim in records.claims:
            for source in claim.provenance.sources:
                if source.ref in history_ids:
                    raise InvalidHistoryRecordSet(
                        "history record id may not be relabeled as claim provenance source"
                    )

        for achievement in self.achievement_instances:
            for basis in achievement.basis_refs:
                if basis.kind is AchievementBasisKind.EVIDENCE_RECORD:
                    record = evidence.get(basis.ref)
                    if record is None:
                        raise InvalidHistoryRecordSet(
                            f"achievement references missing evidence: {basis.ref}"
                        )
                    if record.subject_ref != self.subject_ref:
                        raise InvalidHistoryRecordSet(
                            "achievement evidence subject must match history-set subject"
                        )
                    if record.observed_at > achievement.achieved_at:
                        raise InvalidHistoryRecordSet(
                            "event-bearing achievement evidence observed_at must not follow achieved_at"
                        )
                    if record.recorded_at > achievement.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "achievement evidence record must exist by achievement recorded_at"
                        )
                elif basis.kind is AchievementBasisKind.CAPABILITY_CLAIM:
                    claim = claims.get(basis.ref)
                    if claim is None:
                        raise InvalidHistoryRecordSet(
                            f"achievement references missing claim: {basis.ref}"
                        )
                    if claim.subject_ref != self.subject_ref:
                        raise InvalidHistoryRecordSet(
                            "achievement claim subject must match history-set subject"
                        )
                    if claim.created_at > achievement.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "achievement claim must exist by achievement recorded_at"
                        )
                elif basis.kind is AchievementBasisKind.CLAIM_EVALUATION:
                    evaluation = evaluations.get(basis.ref)
                    if evaluation is None:
                        raise InvalidHistoryRecordSet(
                            f"achievement references missing claim evaluation: {basis.ref}"
                        )
                    claim = claims.get(str(evaluation.claim_id))
                    if claim is None or claim.subject_ref != self.subject_ref:
                        raise InvalidHistoryRecordSet(
                            "achievement evaluation must belong to a claim for the history-set subject"
                        )
                    if evaluation.evaluated_at > achievement.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "achievement evaluation must exist by achievement recorded_at"
                        )
                elif basis.kind in {
                    AchievementBasisKind.EXTERNAL_ARTIFACT,
                    AchievementBasisKind.OTHER,
                } and basis.ref in internal_ids:
                    raise InvalidHistoryRecordSet(
                        "known internal epistemic record may not be relabeled as external/other achievement basis"
                    )

        for milestone in self.milestone_events:
            for source in milestone.source_refs:
                if source.kind is MilestoneSourceKind.EVIDENCE_RECORD:
                    record = evidence.get(source.ref)
                    if record is None:
                        raise InvalidHistoryRecordSet(
                            f"milestone references missing evidence: {source.ref}"
                        )
                    if record.subject_ref != self.subject_ref:
                        raise InvalidHistoryRecordSet(
                            "milestone evidence subject must match history-set subject"
                        )
                    if record.observed_at > milestone.occurred_at:
                        raise InvalidHistoryRecordSet(
                            "milestone evidence observed_at must not follow milestone occurred_at"
                        )
                    if record.recorded_at > milestone.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "milestone evidence record must exist by milestone recorded_at"
                        )
                elif source.kind is MilestoneSourceKind.CAPABILITY_CLAIM:
                    claim = claims.get(source.ref)
                    if claim is None:
                        raise InvalidHistoryRecordSet(
                            f"milestone references missing claim: {source.ref}"
                        )
                    if claim.subject_ref != self.subject_ref:
                        raise InvalidHistoryRecordSet(
                            "milestone claim subject must match history-set subject"
                        )
                    if claim.created_at > milestone.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "milestone claim must exist by milestone recorded_at"
                        )
                elif source.kind is MilestoneSourceKind.CLAIM_EVALUATION:
                    evaluation = evaluations.get(source.ref)
                    if evaluation is None:
                        raise InvalidHistoryRecordSet(
                            f"milestone references missing evaluation: {source.ref}"
                        )
                    claim = claims.get(str(evaluation.claim_id))
                    if claim is None or claim.subject_ref != self.subject_ref:
                        raise InvalidHistoryRecordSet(
                            "milestone evaluation must belong to a claim for the history-set subject"
                        )
                    if evaluation.evaluated_at > milestone.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "milestone evaluation must exist by milestone recorded_at"
                        )
                elif source.kind is MilestoneSourceKind.ACHIEVEMENT_INSTANCE:
                    achievement = achievements.get(source.ref)
                    if achievement is None:
                        raise InvalidHistoryRecordSet(
                            f"milestone references missing achievement: {source.ref}"
                        )
                    if achievement.achieved_at > milestone.occurred_at:
                        raise InvalidHistoryRecordSet(
                            "source achievement achieved_at must not follow milestone occurred_at"
                        )
                    if achievement.recorded_at > milestone.recorded_at:
                        raise InvalidHistoryRecordSet(
                            "source achievement record must exist by milestone recorded_at"
                        )
                elif source.kind in {
                    MilestoneSourceKind.EXTERNAL_ARTIFACT,
                    MilestoneSourceKind.OTHER,
                } and source.ref in internal_ids:
                    raise InvalidHistoryRecordSet(
                        "known internal epistemic record may not be relabeled as external/other milestone source"
                    )

    def to_dict(self) -> dict:
        from .serialization import history_set_to_dict
        return history_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "PersonalHistoryRecordSet":
        from .serialization import history_set_from_dict
        return history_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import history_set_to_json
        return history_set_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "PersonalHistoryRecordSet":
        from .serialization import history_set_from_json
        return history_set_from_json(payload)


@dataclass(frozen=True, slots=True)
class PersonalLegendSet:
    """Private one-subject collection of alternative legend projections."""

    subject_ref: object
    legends: tuple[PersonalLegend, ...] = ()

    def __post_init__(self) -> None:
        from capability_lab.epistemics import CapabilitySubjectRef

        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidLegendSet("subject_ref must be CapabilitySubjectRef")
        legends = _validated_tuple(self.legends, PersonalLegend, "legends", InvalidLegendSet)
        legends = tuple(sorted(legends, key=lambda item: item.legend_id))
        _reject_duplicates((item.legend_id for item in legends), "personal legend id", InvalidLegendSet)
        for legend in legends:
            if legend.subject_ref != self.subject_ref:
                raise InvalidLegendSet("legend subject must match legend-set subject")
        object.__setattr__(self, "legends", legends)

    def validate_against_history(self, history: PersonalHistoryRecordSet) -> None:
        if not isinstance(history, PersonalHistoryRecordSet):
            raise InvalidLegendSet("history must be PersonalHistoryRecordSet")
        if history.subject_ref != self.subject_ref:
            raise InvalidLegendSet("legend-set subject must match history subject")
        achievements = {
            str(item.achievement_id): item for item in history.achievement_instances
        }
        milestones = {str(item.milestone_id): item for item in history.milestone_events}
        history_ids = set(achievements) | set(milestones)
        legend_ids = {str(item.legend_id) for item in self.legends}
        cross_type_ids = history_ids.intersection(legend_ids)
        if cross_type_ids:
            raise InvalidLegendSet(
                "legend ids must not collide with achievement/milestone ids in the validated personal snapshot: "
                f"{sorted(cross_type_ids)}"
            )
        for legend in self.legends:
            used_sources = set()
            for entry in legend.entries:
                for source in entry.source_refs:
                    if source in used_sources:
                        raise InvalidLegendSet(
                            "one history source may not be cited repeatedly across multiple entries of one legend"
                        )
                    used_sources.add(source)
                    if source.kind is LegendSourceKind.ACHIEVEMENT_INSTANCE:
                        achievement = achievements.get(source.ref)
                        if achievement is None:
                            raise InvalidLegendSet(
                                f"legend references missing achievement: {source.ref}"
                            )
                        if achievement.achieved_at > legend.as_of:
                            raise InvalidLegendSet(
                                "legend may not reference achievement after its as_of boundary"
                            )
                        if achievement.recorded_at > legend.generated_at:
                            raise InvalidLegendSet(
                                "legend may not reference achievement recorded after legend generated_at"
                            )
                    else:
                        milestone = milestones.get(source.ref)
                        if milestone is None:
                            raise InvalidLegendSet(
                                f"legend references missing milestone: {source.ref}"
                            )
                        if milestone.occurred_at > legend.as_of:
                            raise InvalidLegendSet(
                                "legend may not reference milestone after its as_of boundary"
                            )
                        if milestone.recorded_at > legend.generated_at:
                            raise InvalidLegendSet(
                                "legend may not reference milestone recorded after legend generated_at"
                            )

    def to_dict(self) -> dict:
        from .serialization import legend_set_to_dict
        return legend_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "PersonalLegendSet":
        from .serialization import legend_set_from_dict
        return legend_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import legend_set_to_json
        return legend_set_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "PersonalLegendSet":
        from .serialization import legend_set_from_json
        return legend_set_from_json(payload)


def _validated_tuple(
    value: object,
    item_type: type,
    field_name: str,
    error_type: type[HistoryError] = InvalidHistoryRecordSet,
) -> tuple:
    if isinstance(value, (str, bytes)):
        raise error_type(f"{field_name} must be an iterable")
    try:
        result = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise error_type(f"{field_name} must be iterable") from exc
    if any(not isinstance(item, item_type) for item in result):
        raise error_type(f"{field_name} contains invalid record type")
    return result


def _reject_duplicates(values, label: str, error_type: type[HistoryError] = InvalidHistoryRecordSet) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise error_type(f"duplicate {label}: {value}")
        seen.add(value)
