FROM python:3.13-slim-bookworm

# Need git and certs to install blazar-tempest-plugin from git source
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /src/
COPY src/ /src/src/

RUN pip install --no-cache-dir /src
    
# initialize the workdir
WORKDIR /workdir
RUN tempest init \
    && mkdir /var/lib/tempest \
    && cp -a /workdir/.stestr /var/lib/tempest/ \
    && cp /workdir/.stestr.conf /var/lib/tempest/ \
    && rm -rf /workdir

WORKDIR /var/lib/tempest
VOLUME /var/lib/tempest
CMD ["tempest","--help"]
