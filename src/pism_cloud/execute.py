import subprocess
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path

from pism_cloud.aws import local_to_s3, s3_to_local


def ensure_directories_exist(work_dir: Path):
    (work_dir /'input').mkdir(parents=True, exist_ok=True)
    (work_dir / 'logs').mkdir(parents=True, exist_ok=True)
    (work_dir / 'output' / 'post_processing').mkdir(parents=True, exist_ok=True)
    (work_dir / 'output' / 'spatial').mkdir(parents=True, exist_ok=True)
    (work_dir / 'output' / 'state').mkdir(parents=True, exist_ok=True)
    (work_dir / 'run_scripts').mkdir(parents=True, exist_ok=True)


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
        "--run-dir",
        help="Directory to execute PISM runs from. If you've provided `--bucket` and `--bucket-prefix`, "
             "this will likely be a folder within `f's3://{bucket}/{bucket_prefix}/'`.",
        default=Path.cwd(),
        type=Path,
    )

    args = parser.parse_args()

    work_dir = Path.cwd()

    if args.bucket:
        work_dir /= args.bucket_prefix
        s3_to_local(args.bucket, args.bucket_prefix, work_dir)

    run_dir = work_dir / args.run_dir
    ensure_directories_exist(run_dir)

    execute(work_dir=run_dir)

    if args.bucket:
        local_to_s3(work_dir, args.bucket, args.bucket_prefix)
