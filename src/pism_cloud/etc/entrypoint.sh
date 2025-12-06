#!/bin/bash --login
set -e
conda activate pism-cloud
exec python -um pism_cloud "$@"
