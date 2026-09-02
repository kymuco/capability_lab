"""Dependency-free local runner for Civilization Bootstrap Pilot 01 capture."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from capability_lab.epistemics import CapabilitySubjectRef

from .protocol import build_civilization_bootstrap_pilot_01_protocol_v1
from .serialization import pilot_protocol_to_json
from .transactional import (
    InvalidPrivatePilotWorkspace,
    initialize_private_workspace,
    record_artifact_capture,
    record_text_capture,
    validate_private_workspace,
)


def _timestamp(value: str | None, field_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{field_name} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError(f"{field_name} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def _tools(values: list[str] | None) -> tuple[str, ...]:
    return tuple(values or ())


def _reject_input_symlink_components(path: Path, field_name: str) -> None:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink():
            raise InvalidPrivatePilotWorkspace(f"{field_name} must not contain symlink components")


def _add_capture_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", required=True, help="Existing private Pilot 01 workspace.")
    parser.add_argument("--capture-id", required=True, help="Cross-platform unique capture file key.")
    parser.add_argument("--probe", required=True, help="Exact probe id from protocol.json.")
    parser.add_argument(
        "--captured-at",
        help=(
            "Declared timezone-aware ISO capture timestamp; defaults to runner current UTC time. "
            "This field is not authenticated event time."
        ),
    )
    parser.add_argument("--tool", action="append", dest="tools", help="Declare a tool/reference actually used; repeatable.")
    parser.add_argument("--note", default="", help="Optional participant note about this capture.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture private human-provided data for Civilization Bootstrap Pilot 01. "
            "This runner does not grade, evaluate, or generate participant answers."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create an empty private workspace and frozen protocol snapshot.")
    init.add_argument("--workspace", required=True)
    init.add_argument("--session-id", required=True)
    init.add_argument("--subject-ref", required=True)
    init.add_argument(
        "--created-at",
        help=(
            "Declared timezone-aware ISO workspace timestamp; defaults to runner current UTC time. "
            "This field is not authenticated session-start time."
        ),
    )

    subparsers.add_parser("show-protocol", help="Print the frozen participant-facing Pilot 01 protocol JSON.")

    text = subparsers.add_parser("record-text", help="Record a subject-provided UTF-8 text response.")
    _add_capture_common(text)
    text.add_argument("--input", required=True, help="UTF-8 text file containing the participant response.")

    artifact = subparsers.add_parser("record-artifact", help="Copy and record one subject-provided local artifact file.")
    _add_capture_common(artifact)
    artifact.add_argument("--input", required=True, help="Local artifact file to copy into the private workspace.")

    validate = subparsers.add_parser(
        "validate",
        help=(
            "Validate workspace structure, capture closure, artifact integrity, and stable snapshot identity. "
            "Missing required probes are reported but do not make a structurally valid workspace fail."
        ),
    )
    validate.add_argument("--workspace", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "show-protocol":
            print(pilot_protocol_to_json(build_civilization_bootstrap_pilot_01_protocol_v1()), end="")
            return 0

        if args.command == "init":
            root = initialize_private_workspace(
                args.workspace,
                session_id=args.session_id,
                subject_ref=CapabilitySubjectRef(args.subject_ref),
                created_at=_timestamp(args.created_at, "created_at"),
            )
            print(root)
            return 0

        if args.command == "record-text":
            input_path = Path(args.input)
            _reject_input_symlink_components(input_path, "text input path")
            try:
                text_content = input_path.read_text(encoding="utf-8")
            except OSError as exc:
                raise InvalidPrivatePilotWorkspace(f"cannot read text input file: {exc}") from exc
            capture = record_text_capture(
                args.workspace,
                capture_id=args.capture_id,
                probe_id=args.probe,
                text_content=text_content,
                captured_at=_timestamp(args.captured_at, "captured_at"),
                declared_tools=_tools(args.tools),
                participant_note=args.note,
            )
            print(capture.capture_id)
            return 0

        if args.command == "record-artifact":
            capture = record_artifact_capture(
                args.workspace,
                capture_id=args.capture_id,
                probe_id=args.probe,
                source_file=args.input,
                captured_at=_timestamp(args.captured_at, "captured_at"),
                declared_tools=_tools(args.tools),
                participant_note=args.note,
            )
            print(capture.capture_id)
            return 0

        if args.command == "validate":
            report = validate_private_workspace(args.workspace)
            print(f"session_id={report.session_id}")
            print(f"capture_count={report.capture_count}")
            print(f"artifact_count={report.artifact_count}")
            print("captured_probe_ids=" + ",".join(report.captured_probe_ids))
            print("missing_required_probe_ids=" + ",".join(report.missing_required_probe_ids))
            print(f"capture_complete={str(report.capture_complete).lower()}")
            print(f"snapshot_sha256={report.snapshot_sha256}")
            return 0

        parser.error("unsupported command")
        return 2
    except (InvalidPrivatePilotWorkspace, ValueError, argparse.ArgumentTypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
