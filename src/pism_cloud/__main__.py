"""
PISM-Cloud entrypoint dispatcher.
"""

import argparse
import sys
from importlib.metadata import entry_points


def main():
    """
    PISM-Cloud entrypoint dispatcher.
    """
    parser = argparse.ArgumentParser(prefix_chars="+", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "++process",
        choices=[
            "pism-cloud-execute",
        ],
        default="pism-cloud-execute",
        help="Select the console_script entrypoint to use",  # as specified in `pyproject.toml`
    )

    args, unknowns = parser.parse_known_args()

    eps = entry_points(group="console_scripts")
    (process_entry_point,) = {process for process in eps if process.name == args.process}

    sys.argv = [args.process, *unknowns]
    sys.exit(process_entry_point.load()())


if __name__ == "__main__":
    main()
