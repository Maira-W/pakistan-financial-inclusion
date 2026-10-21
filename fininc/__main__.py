"""Command line entry point:  python -m fininc <command>

Commands
    ingest      download the raw data into data/raw (needs internet; run once)
    build       clean the raw data and build the unit table
    analyze     fit the models and write the analysis tables
    report      write charts, the web dashboard, the Power BI project and the documents
    all         build, analyze and report
    notebook    run notebooks/analysis.ipynb and save it with its outputs (needs nbclient and ipykernel)
    verify      check that data/raw matches the checksum manifest
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fininc", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["ingest", "build", "analyze", "report", "all", "notebook", "verify"])
    parser.add_argument("--refresh", action="store_true", help="ingest: download files again")
    parser.add_argument("--only", nargs="+", help="ingest: limit to worldbank, sbp, pbs or geo")
    args = parser.parse_args(argv)

    if args.command == "ingest":
        from . import ingest
        ingest.run(only=args.only, refresh=args.refresh)
        return 0
    if args.command == "verify":
        from . import ingest
        problems = ingest.verify()
        print("raw data matches the manifest" if not problems else "\n".join(problems))
        return 1 if problems else 0
    if args.command == "notebook":
        from . import notebook
        notebook.build()
        return 0

    from . import pipeline
    getattr(pipeline, args.command)()
    return 0


if __name__ == "__main__":
    sys.exit(main())
