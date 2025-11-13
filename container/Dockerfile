FROM ghcr.io/pism/pism:9c1679b AS runtime

FROM runtime AS build
ARG DEBIAN_FRONTEND=noninteractive
ARG ONEAPI_VERSION=2025.3
ARG IMPI_VERSION=2021.17

USER root
RUN <<EOF
    echo "Install build tools"

    set -e
    set -u
    set -x

    apt-get update

    apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    git \
    libtool \
    make \
    intel-oneapi-compiler-dpcpp-cpp-${ONEAPI_VERSION} \
    intel-oneapi-compiler-fortran-${ONEAPI_VERSION} \
    intel-oneapi-mpi-devel-${IMPI_VERSION} \
    ""

    rm -rf /var/lib/apt/lists/*
EOF

RUN <<EOF
    echo "Install NCAR/peak_memusage"

    set -e
    set -u
    set -x

    build_dir=/var/tmp/build/peak_memusage
    prefix=/opt/peak_memusage

    mkdir -p ${build_dir}
    cd ${build_dir}

    git clone --depth=1 https://github.com/NCAR/peak_memusage.git .

    ./autogen.sh

    ./configure CC=mpiicx CXX=mpiicpx FC=mpiifx \
    --disable-nvml \
    --disable-fortran \
    --disable-openmp \
    --enable-mpi \
    --prefix=${prefix} || (cat config.log && exit 1)

    make all && make install

    rm -rf ${build_dir}
EOF

FROM runtime

COPY --from=build /opt/peak_memusage/ /opt/peak_memusage

ENV PATH=/opt/peak_memusage/bin:$PATH
