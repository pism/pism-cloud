import subprocess
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path

from pism_cloud.aws import local_to_s3, s3_to_local


def execute(work_dir: Path = Path.cwd()):
    for run_script in work_dir.glob('**/run_scripts/*.sh'):
        subprocess.run(
            f'bash -ex {run_script.resolve()}',
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=True,
            check=True,
        )


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.description = "Execute a PISM-Cloud run."
    parser.add_argument(
        "--bucket",
        help="AWS S3 Bucket to sync with the local working directory.",
    )
    parser.add_argument(
        "--bucket-prefix",
        help="AWS prefix to sync with the local working directory.",
        default="",
    )
    parser.add_argument(
        "--work-dir",
        help="Working directory.",
        default=Path.cwd(),
        type=Path,
    )

    args = parser.parse_args()

    if args.bucket:
        s3_to_local(args.work_dir, bucket=args.bucket, prefix=args.bucket_prefix)

    execute(work_dir=args.work_dir)

    if args.bucket:
        local_to_s3(args.work_dir, bucket=args.bucket, prefix=args.bucket_prefix)
