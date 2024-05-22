FROM ubuntu:22.04 as build
ARG DEBIAN_FRONTEND=noninteractive
ARG PETSC_PREFIX=/usr/lib/petsc
ENV PISM_PREFIX=/opt/pism

# Install PISM's build dependencies
RUN <<EOF
    echo "Install some build tools and dependencies"

    set -e
    set -u
    set -x

    apt-get update

    apt-get install -y --no-install-recommends \
    ca-certificates \
    cmake \
    curl \
    g++ \
    libfftw3-dev \
    libgsl-dev \
    libnetcdf-dev \
    libproj-dev \
    libudunits2-dev \
    make \
    netcdf-bin \
    pkg-config \
    petsc-dev \
    ""

    rm -rf /var/lib/apt/lists/*
EOF

# Install PISM
RUN <<EOF
    echo "Install PISM"

    set -e
    set -u
    set -x

    export CC=mpicc
    export CXX=mpicxx
    opt_flags="-O3 -mavx2"

    cd /var/tmp
    curl -OL "https://github.com/pism/pism/archive/refs/tags/v2.1.tar.gz"
    tar xzvf v2.1.tar.gz

    mkdir -p pism-build

    cmake -B pism-build -S pism-2.1 \
    -DCMAKE_CXX_FLAGS="${opt_flags}" \
    -DCMAKE_C_FLAGS="${opt_flags}" \
    -DCMAKE_INSTALL_PREFIX="${PISM_PREFIX}" \
    -DCMAKE_PREFIX_PATH="${PETSC_PREFIX}" \
    -DPism_USE_PROJ=YES

    make -j -C pism-build install

    rm -rf /var/tmp/v2.1.tar.gz /var/tmp/pism-2.1 /var/tmp/pism-build/
    rm -rf ${PISM_PREFIX}/include/pism
    rm -rf ${PISM_PREFIX}/share/pism/examples
EOF

FROM ubuntu:22.04 as runtime
ARG DEBIAN_FRONTEND=noninteractive
# Unfortunately PISM_PREFIX variable defined near the top of this file
# went out of scope at the end of the first ("build") stage.
ENV PISM_PREFIX=/opt/pism

RUN <<EOF
    echo "Install runtime dependencies"

    set -e
    set -u
    set -x

    apt-get update

    # PISM's runtime dependencies
    apt-get install -y --no-install-recommends \
    libfftw3-3 \
    libgsl27 \
    libnetcdf19 \
    libpetsc-real3.15 \
    libproj22 \
    libudunits2-0 \
    ""

    # Runner script's dependencies (unzip is needed to install AWS CLI)
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3-pip \
    python3-pycurl \
    unzip \
    ""

    rm -rf /var/lib/apt/lists/*
EOF

RUN <<EOF
    echo "Install AWS CLI and boto3"

    set -e
    set -u
    set -x

    cd /var/tmp

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf /var/tmp/awscliv2.zip /var/tmp/aws

    pip3 install boto3
EOF

COPY --from=build ${PISM_PREFIX} ${PISM_PREFIX}
COPY pism_cloud_runner.py ${PISM_PREFIX}/bin/

# Add a non-privileged user to use OpenMPI
RUN useradd --create-home --system --shell=/bin/false worker && usermod --lock worker
USER worker

# Add PISM to the PATH:
ENV PATH=${PISM_PREFIX}/bin:$PATH

ENTRYPOINT ["pism_cloud_runner.py"]
