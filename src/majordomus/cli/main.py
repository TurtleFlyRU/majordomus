from __future__ import annotations

import argparse
import sys
from pathlib import Path

from majordomus.cli.init_cmd import render_init_report, run_init_command
from majordomus.cli.project_cmd import run_project_validate
from majordomus.cli.render import render_project_report, render_workspace_report
from majordomus.cli.workspace_cmd import run_workspace_command
from majordomus.core.domain import ProjectStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="majordomus")
    parser.add_argument(
        "--format", dest="output_format", choices=["human", "json"], default="human"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    project_parser = subparsers.add_parser("validate")
    project_parser.add_argument("--path", type=Path, default=Path("."))

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--path", type=Path, default=Path("."))
    init_parser.add_argument("--project-name", type=str, default=None)
    init_parser.add_argument(
        "--workspace-file", type=Path, default=Path("majordomus.workspace.yaml")
    )
    init_parser.add_argument("--no-workspace", action="store_true")
    init_parser.add_argument("--force", action="store_true")

    workspace_parser = subparsers.add_parser("workspace")
    workspace_sub = workspace_parser.add_subparsers(dest="workspace_command", required=True)
    for name in ("validate", "status", "audit"):
        cmd = workspace_sub.add_parser(name)
        cmd.add_argument("--workspace-file", type=Path, default=Path("majordomus.workspace.yaml"))

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 3

    try:
        if args.command == "validate":
            project_report = run_project_validate(project_root=args.path)
            print(render_project_report(project_report, args.output_format))
            return 0 if project_report.status == ProjectStatus.PASS else 2

        if args.command == "workspace":
            workspace_report = run_workspace_command(
                args.workspace_command,
                workspace_file=args.workspace_file,
            )
            print(render_workspace_report(workspace_report, args.output_format))
            return int(workspace_report.exit_code)

        if args.command == "init":
            init_report = run_init_command(
                project_root=args.path,
                project_name=args.project_name,
                workspace_file=args.workspace_file,
                include_workspace=not args.no_workspace,
                force=args.force,
            )
            print(render_init_report(init_report, args.output_format))
            return 0

        return 3
    except Exception as exc:  # pragma: no cover
        print(f"Internal error: {exc}", file=sys.stderr)
        return 4


def entrypoint() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    entrypoint()
