#!/usr/bin/env python3

import argparse
from urllib.parse import urlparse
import pathlib
import pycurl
import boto3
from botocore.exceptions import ClientError
import subprocess               # subprocess.run()
import shlex                    # shlex.split()
import json                     # json.loads()
import shutil                   # shutil.rmtree()
import tempfile                 # tempfile.mkdtemp()
import logging

def parse_s3_url(url):
    """Extract bucket_name and object_name from an S3 URL.

    :param url: URL to parse"""
    url_parts = urlparse(url)

    path = pathlib.Path(url_parts.path)
    bucket_name = url_parts.netloc

    if path.is_relative_to("/"):
        object_name = path.relative_to("/")
    else:
        object_name = path

    return bucket_name, str(object_name)

def download_s3(url, file_name):
    """Download a file from an S3 bucket.

    :param url: S3 URL (including the bucket name and the object name) to download from
    :param file_name: Output file name (a string)
    """

    bucket_name, object_name = parse_s3_url(url)

    logging.info(f"Downloading file='{file_name}' from bucket_name={bucket_name}, object_name={object_name}")

    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket_name, object_name, file_name)
    except ClientError as e:
        logging.error(e)
        raise

def upload_s3(url, file_name):
    """Upload a file to an S3 bucket

    :param url: S3 URL (including the bucket name and the object name) to upload to
    :param file_name: Input file name (a pathlib.Path instance)
    """

    bucket_name, object_name = parse_s3_url(f"{url}/{file_name.name}")

    logging.info(f"Uploading file='{file_name}' to bucket_name={bucket_name}, object_name={object_name}")

    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
    except ClientError as e:
        logging.error(e)
        raise

def download_pycurl(url, file_name):
    """Use pycurl to download a file from `url`, saving to `file_name`.

    :param url: URL to download from
    :param file_name: Output file name (a string)
    """

    logging.info(f"Downloading file='{file_name}' from url={url} using cURL")

    with open(file_name, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEDATA, f)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.FAILONERROR, True)
        c.setopt(c.NOPROGRESS, False)
        try:
            c.perform()
        except pycurl.error as e:
            logging.error(e)
            raise
        finally:
            c.close()

def download(url, file_name):
    """Download a file from `url`, saving to `file_name`.

    Supports S3 buckets and all protocols that libcurl can handle.

    :param url: URL to download from
    :param file_name: Output file name
    """
    if urlparse(url).scheme == "s3":
        download_s3(url, file_name)
        return

    download_pycurl(url, file_name)

def stage(inputs, output_dir):
    """Stage input files in `output_dir`. `inputs` is a list. Each element
    is an URL string or a two-element sequence containing the URL and
    the output file name.

    :param inputs: List of input files to download and stage
    :param output_dir: Output directory
    """
    for item in inputs:
        if isinstance(item, str):
            url = item
            file_name = pathlib.Path(urlparse(url).path).name
        else:
            assert len(item) == 2
            url = item[0]
            file_name = item[1]

        logging.info(f"Downloading file='{file_name}' from url='{url}'")

        download(url, output_dir / file_name)

def process_output(obj, output_dir, log_output=False):
    """Save captured stdout and stderr to log files.

    :param obj: An object containing stdout and stderr info (a CompletedProcess or CalledProcessError instance)
    :param output_dir: Output directory
    :param log_output: If True, log captured output (we're processing an error)
"""
    if len(obj.stdout) > 0:
        if log_output:
            logging.error(f"====== START OF CAPTURED STDOUT ======\n{obj.stdout.decode('ascii')}")
            logging.error("======  END OF CAPTURED STDOUT  ======\n")
        else:
            with open(output_dir / "stdout.log", "wb") as f:
                f.write(obj.stdout)

    if len(obj.stderr) > 0:
        if log_output:
            logging.error(f"====== START OF CAPTURED STDERR ======\n{obj.stderr.decode('ascii')}")
            logging.error("======  END OF CAPTURED STDERR  =====\n")
        else:
            with open(output_dir / "stderr.log", "wb") as f:
                f.write(obj.stderr)

def run(command, working_directory):
    """Run a `command` in the `working_directory`, saving stdout and
    stderr to files. Return the list of files created by `command`
    plus output logs.

    :param command: string containing the command
    :param working_directory: working directory to use
    :return: list of files that were created
    """
    try:
        logging.info(f"Running '{command}' in '{working_directory}'")

        p = pathlib.Path(working_directory)
        old_file_list = [x for x in p.iterdir() if x.is_file()]

        process = subprocess.run(shlex.split(command), capture_output=True, check=True, cwd=working_directory)
        process_output(process, working_directory)

        new_file_list = [x for x in p.iterdir() if x.is_file()]

        return  [x for x in new_file_list if x not in old_file_list]
    except subprocess.CalledProcessError as e:
        logging.error(f"'{e.cmd}' exited with the return code {e.returncode}")
        process_output(e, working_directory, error=True)
        raise
    except FileNotFoundError as e:
        logging.error(e)
        raise

    return []

def main(params):
    """Stage inputs, run a command, upload results."""
    # use 'params' here so it fails early
    inputs  = params["inputs"]
    command = params["command"]
    output  = params["output"]

    # create a temporary directory to work in
    tempdir = pathlib.Path(tempfile.mkdtemp())

    try:
        stage(inputs, tempdir)

        new_files = run(command, tempdir)

        logging.info(f"Command generated {[str(x) for x in new_files]}")

        for f in new_files:
            full_path = pathlib.Path(tempdir) / f
            upload_s3(output, full_path)
    finally:
        # clean up:
        logging.info(f"Removing '{tempdir}' and its contents")
        shutil.rmtree(tempdir)

usage = """The positional argument `parameters` should have the form

{"inputs": ["https://foo.com/input.nc",
            "ftp://bar.org/climate.nc",
            ["s3://bucket-name/object-name", "forcing.nc"]],
 "command": "mpiexec -n 8 pismr -i input.nc -o output.nc ...",
 "output": "s3://bucket-name/prefix/"}

Here 'inputs' is a list of URLs pointing to inputs required by
'command'. Downloaded files are saved into the current working
directory using the last component of the path in the URL as the name.
Use a two-element sequence [URL, file_name] to use a different file name
(see forcing.nc above). URLs can use HTTP, HTTPS, FTP ... protocols
(anything supported by cURL) *plus* AWS S3.

The 'command' should save outputs into the current working directory.
Flags in 'command' should not contain any absolute paths or paths
containing sub-directories.

All files generated by this command (along with the captured output)
will be uploaded to 'output'. Only AWS S3 is supported here.

We assume that AWS credentials are set using `~/.aws/credentials` or
environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and
possibly `AWS_SESSION_TOKEN`.
"""

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog='pism_cloud_runner',
        description='Downloads inputs, runs PISM, uploads results to an S3 bucket.',
        usage=usage)

    parser.add_argument('parameters', help="JSON encoded set of parameters")

    args = parser.parse_args()

    params = json.loads(args.parameters)

    main(params)
