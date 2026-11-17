"""Configuration, schema, and provenance helpers for Gate A.

The configuration file uses JSON syntax with a ``.yml`` extension. JSON is a
valid subset of YAML, which keeps the file usable by YAML readers while
allowing this feasibility workflow to run without a PyYAML dependency.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable, Mapping, Any


def load_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate the frozen Gate A configuration."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)

    required_sections = {
        "schema_version",
        "years",
        "latitude",
        "assets",
        "stability",
        "tree_cover",
        "matching",
        "decision",
        "forbidden_outcome_tokens",
    }
    missing = required_sections.difference(config)
    if missing:
        raise ValueError(f"Gate A configuration is missing sections: {sorted(missing)}")

    years = config["years"]
    actual_count = years["end"] - years["start"] + 1
    if actual_count != years["expected_count"]:
        raise ValueError(
            "Gate A year range is inconsistent: "
            f"{actual_count} inclusive years but expected_count="
            f"{years['expected_count']}"
        )

    covariates = {str(name).casefold() for name in config["matching"]["covariates"]}
    forbidden = {str(name).casefold() for name in config["forbidden_outcome_tokens"]}
    leakage = sorted(covariates.intersection(forbidden))
    if leakage:
        raise ValueError(f"Outcome-dependent matching covariates are forbidden: {leakage}")

    return config


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_columns(columns_or_frame: Any, required: Iterable[str]) -> None:
    """Raise ``ValueError`` when required column names are absent."""
    columns = getattr(columns_or_frame, "columns", columns_or_frame)
    available = {str(column) for column in columns}
    missing = sorted(set(required).difference(available))
    if missing:
        raise ValueError(f"Required columns are missing: {missing}")


def update_manifest(
    manifest_path: Path,
    *,
    key: str,
    artifact_path: Path,
    schema_version: str,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Insert or replace one artifact record in the Gate A manifest."""
    manifest_path = Path(manifest_path)
    artifact_path = Path(artifact_path).resolve()
    if not artifact_path.is_file():
        raise FileNotFoundError(artifact_path)

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = json.load(stream)
    else:
        manifest = {"manifest_version": "gate-a-manifest-1.0", "artifacts": {}}

    record: dict[str, Any] = {
        "path": str(artifact_path),
        "sha256": sha256_file(artifact_path),
        "bytes": artifact_path.stat().st_size,
        "schema_version": schema_version,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        record["metadata"] = dict(metadata)

    manifest["artifacts"][key] = record
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return record
