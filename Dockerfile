FROM python:3.13-slim-bookworm

# git is needed for the blazar-tempest-plugin VCS dependency in pyproject.toml.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /src/
COPY src/ /src/src/

RUN pip install --no-cache-dir /src

RUN mkdir -p /workspace && chown 1000:1000 /workspace
WORKDIR /workspace
USER 1000

CMD ["tempest", "--help"]
