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

# Tempest complains if run without a homedir
RUN useradd \
    --home-dir /home/tempest \
    --create-home \
    --shell /usr/sbin/nologin \
    --user-group \
    tempest
    
# initialize the workdir with a stestr repo
RUN mkdir /var/lib/tempest \
    && chown tempest:tempest /var/lib/tempest

WORKDIR /var/lib/tempest
USER tempest
RUN stestr init
VOLUME /var/lib/tempest

CMD ["tempest", "--help"]
