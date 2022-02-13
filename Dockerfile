# Usage:
#
# cd pyblish-lite
# docker run --rm -v $(pwd):/pyblish-lite pyblish/pyblish-lite


FROM ubuntu:20.04 AS base

MAINTAINER marcus@abstractfactory.io

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && apt-get install -yq \
    build-essential \
    python3-pip \
    git \
    libgl1 \
    libglib2.0-0

FROM base AS final

COPY ./requirements.txt ./dev-requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r dev-requirements.txt

WORKDIR /pyblish-lite
COPY . .

# ENTRYPOINT flake8 --append-config .flake8.docker pyblish_lite
# ENTRYPOINT mypy
CMD [ "nosetests", \
    "--verbose", \
    "--with-doctest", \
    "--exe", \
    "--exclude=vendor"]
