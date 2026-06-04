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
    
# initialize the workdir with a stestr repo
RUN mkdir /var/lib/tempest

WORKDIR /var/lib/tempest
RUN stestr init
VOLUME /var/lib/tempest

CMD ["tempest", "--help"]
