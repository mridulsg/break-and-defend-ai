# Red-team toolbox (Course 1, Lab 8.3): garak, with CPU-only torch and every dependency pinned by hash.
# Same digest-pinned base as the gateway, so the layer is shared on disk.
FROM python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PIP_DEFAULT_TIMEOUT=300 PIP_RETRIES=10 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl jq ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 --shell /bin/bash lab \
 && mkdir /data && chown lab:lab /data

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt

USER lab
WORKDIR /home/lab
LABEL bdai.course="c1" bdai.component="redteam-toolbox"

CMD ["bash"]
