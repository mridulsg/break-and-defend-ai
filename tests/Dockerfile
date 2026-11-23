# Test runner image. Digest-pinned base, hash-pinned dependencies. Tests run with no network.
FROM python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTEST_ADDOPTS="-p no:cacheprovider"

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin tester

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt

USER tester
WORKDIR /repo
LABEL bdai.component="tests"
CMD ["pytest", "-q", "tests/unit"]
