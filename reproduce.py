"""Reproduce archived descriptive results and figures offline."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside(path, parent):
    return path == parent or parent in path.parents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["summaries", "overlap", "figures", "all"], default="all")
    parser.add_argument("--output", type=Path, default=Path("reproduced"))
    parser.add_argument("--domain-inputs", type=Path,
                        help="Optional display-domain inputs for regenerating Figure 1.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    out = (root / args.output).resolve()
    domain = args.domain_inputs.resolve() if args.domain_inputs is not None else None
    protected = [root / name for name in ["data", "assets", "code", "evidence", "figures"]]
    if inside(root, out) or any(inside(out, path.resolve()) for path in protected):
        parser.error("Output must be separate from packaged inputs, code and reference figures.")
    if domain is not None:
        if not domain.is_dir():
            parser.error("--domain-inputs must be an existing directory.")
        if inside(out, domain) or inside(domain, out):
            parser.error("Output and external display-domain inputs must not overlap.")
    if out.exists() and any(out.iterdir()):
        parser.error("Choose a new or empty output directory to keep runs separate.")
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)

    def input_snapshot():
        records = {}
        for folder in protected:
            if folder.exists():
                for path in sorted(folder.rglob("*")):
                    if path.is_file():
                        records[path.relative_to(root).as_posix()] = sha256(path)
        for name in ["reproduce.py", "requirements.txt", "figure_map.json"]:
            path = root / name
            if path.is_file():
                records[name] = sha256(path)
        if domain is not None:
            for path in sorted(domain.rglob("*")):
                if path.is_file():
                    records["external_domain/" + path.relative_to(domain).as_posix()] = sha256(path)
        return records

    before = input_snapshot()
    env = os.environ.copy()
    env.update(PHENOLOGY_OUTPUT=str(out), PROJ_NETWORK="OFF",
               MPLCONFIGDIR=str(out / "plot_cache"), PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1")
    # An inherited environment variable must not silently request Figure 1 regeneration.
    env.pop("PHENOLOGY_DOMAIN_INPUTS", None)
    if domain is not None:
        env["PHENOLOGY_DOMAIN_INPUTS"] = str(domain)
    commands, figure_status = [], {}

    def run(script, *arguments):
        started = time.monotonic()
        command = [sys.executable, str(root / script), *map(str, arguments)]
        result = subprocess.run(command, cwd=out, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        label = f"{len(commands) + 1:02d}_{Path(script).stem}"
        (out / "logs" / (label + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
        (out / "logs" / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
        commands.append(dict(script=script, returncode=result.returncode,
                             seconds=round(time.monotonic() - started, 3)))
        if result.returncode:
            raise RuntimeError(f"{script} failed; see logs/{label}.stderr.txt")
        print("PASS " + script, flush=True)

    failure = None
    try:
        if args.mode in ["summaries", "all"]:
            run("code/review_descriptives.py")
            run("code/check_tables.py")
        if args.mode in ["overlap", "all"]:
            run("code/summarize_overlap.py", "--base", root,
                "--returns", root / "data/overlap/incoming", "--output", out / "overlap")
        if args.mode in ["summaries", "overlap", "all"]:
            section = {"summaries": "main", "overlap": "overlap", "all": "all"}[args.mode]
            run("code/export_current_tables.py", "--section", section)
        if args.mode in ["figures", "all"]:
            mapping = json.loads((root / "figure_map.json").read_text(encoding="utf-8-sig"))
            figure_out = out / "figures"
            figure_out.mkdir(exist_ok=True)
            if domain is None:
                shutil.copy2(root / "figures/reference/Figure1.png", figure_out / "Figure1.png")
                figure_status["Figure1"] = "archived_reference_copy"
            keys = ["Figure2", "Figure3", "Figure4", "FigureS1", "FigureS2", "FigureS3", "FigureS4"]
            if domain is not None:
                keys.insert(0, "Figure1")
            for key in keys:
                row = mapping[key]
                run(row["script"])
                for extension in ["png", "svg", "pdf", "tiff"]:
                    shutil.copy2(figure_out / key / (row["generated_stem"] + "." + extension),
                                 figure_out / (key + "." + extension))
                figure_status[key] = "regenerated_from_packaged_inputs" if key != "Figure1" else "regenerated_with_display_domain_inputs"
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        try:
            after = input_snapshot()
            changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
        except Exception as error:
            after, changed = {}, ["input_snapshot_failed"]
            failure = failure or f"Input verification failed: {error}"
        if changed:
            failure = failure or "Protected inputs changed during execution."
        report_path = out / "reproduction_report.json"
        outputs = {path.relative_to(out).as_posix(): sha256(path)
                   for path in sorted(out.rglob("*"))
                   if path.is_file() and path != report_path and "plot_cache" not in path.relative_to(out).parts}
        report = dict(status="FAIL" if failure else "PASS", mode=args.mode,
                      error=failure, commands=commands, figures=figure_status,
                      inputs_unchanged=not changed, changed_inputs=changed,
                      input_sha256_before=before, input_sha256_after=after,
                      output_sha256=outputs, python=sys.version,
                      strict_filter_distributions="aggregate_only",
                      annual_distributions="aggregate_only",
                      overlap_geometry="Archived GEE returns; no geometry query is rerun.",
                      scope="Offline deterministic reproduction of previously defined descriptive results; no fitting, matching, GEE or random execution.")
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failure:
        print(failure, file=sys.stderr)
        return 1
    print(json.dumps(dict(status="PASS", mode=args.mode, commands=len(commands)), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
