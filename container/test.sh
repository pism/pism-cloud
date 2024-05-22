#!/bin/bash

TAG=ckhrulev/pism-for-aws

run="docker run --cap-add=sys_nice --rm -v ${HOME}/.aws:/home/worker/.aws ${TAG}"

${run} '{"inputs" : [], "command" : "mpiexec -n 1 pismr -eisII A -y 10 -Mx 5 -My 5 -Mz 3 -o eis2-A.nc", "output" : "s3://pism-cloud-play/eis2-A"}'

${run} '{"inputs" : ["s3://pism-cloud-play/eis2-A/eis2-A.nc"], "command" : "mpiexec -n 1 pismr -i eis2-A.nc -y 10 -o eis2-A-continued.nc", "output" : "s3://pism-cloud-play/eis2-A-continued"}'
