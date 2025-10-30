# Taken from https://github.com/rapidsai/ucx-py/tree/3faf968a0876247f9339cea57f0e9f2a4145ebaf/docker
ARG CUDA_VERSION=13.0.0
ARG DISTRIBUTION_VERSION=ubuntu22.04
FROM nvidia/cuda:${CUDA_VERSION}-devel-${DISTRIBUTION_VERSION}

# Where to install conda, and what to name the created environment
ARG CONDA_HOME=/opt/conda
ARG CONDA_ENV=rapids
# Name of conda spec file in the current working directory that
# will be used to build the conda environment.

ENV CONDA_ENV="${CONDA_ENV}"
ENV CONDA_HOME="${CONDA_HOME}"


# Where cuda is installed
ENV CUDA_HOME="/usr/local/cuda"
ENV NV_HOME="/usr/local/nvidia"

SHELL ["/bin/bash", "-c"]

RUN apt-get update -y \
    && apt-get --fix-missing upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && apt-get install -y \
        automake \
        dh-make \
        git \
        libcap2 \
        libnuma-dev \
        libtool \
        make \
        pkg-config \
        udev \
        curl \
        librdmacm-dev \
        rdma-core \
        gcc \
        g++ \
    && apt-get autoremove -y \
    && apt-get clean

RUN curl -fsSL https://github.com/conda-forge/miniforge/releases/download/25.3.1-0/Miniforge3-25.3.1-0-Linux-x86_64.sh \
    -o /minimamba.sh \
    && bash /minimamba.sh -b -p ${CONDA_HOME} \
    && rm /minimamba.sh

ENV PATH="${CONDA_HOME}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${CUDA_HOME}/bin:${NV_HOME}/bin"

RUN mamba create -n ${CONDA_ENV} -c rapidsai -c conda-forge -c nvidia \
    python dask-cuda dask-cudf rapids cuml rapids-xgboost click gcsfs cuda-version=12.9 \
    --yes

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8


RUN apt update -y && apt-get install vim nano -y

WORKDIR /app


