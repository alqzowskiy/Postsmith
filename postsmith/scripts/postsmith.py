import argparse
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export
import generate
import serve
import wizard
import workspace


def cmd_init(args):
    workspace_path = workspace.init_workspace()
    print("Workspace ready at " + workspace_path)
    print("Brand file:  " + workspace.brand_path(workspace_path))
    print("Config:      " + workspace.config_path(workspace_path))
    print("Fill in brand.json (palette, fonts, tone, never-list) before generating.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="postsmith",
        description="Generate brand-consistent Instagram visuals with gpt-image-2.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the .postsmith workspace for this project")

    sub.add_parser("wizard", help="build a job interactively")

    g = sub.add_parser("generate", help="generate images for a job")
    g.add_argument("--job", help="job id under .postsmith/jobs/ (default: latest)")
    g.add_argument("--yes", action="store_true", help="skip both confirmations")

    s = sub.add_parser("serve", help="serve a job gallery or the job history")
    s.add_argument("--job", help="job id to serve (default: history of all jobs)")
    s.add_argument("--port", type=int, default=None)
    s.add_argument("--no-open", action="store_true", help="do not open a browser")

    e = sub.add_parser("export", help="zip a job for handoff")
    e.add_argument("--job", help="job id to export (default: latest)")
    e.add_argument("--all", action="store_true", help="zip the whole jobs tree")

    args = parser.parse_args(argv)

    if args.command == "init":
        cmd_init(args)
    elif args.command == "wizard":
        wizard.run()
    elif args.command == "generate":
        generate.run(args.job, assume_yes=args.yes)
    elif args.command == "serve":
        serve.run(job=args.job, port=args.port, no_open=args.no_open)
    elif args.command == "export":
        export.run(job=args.job, all_jobs=args.all)


if __name__ == "__main__":
    main()
