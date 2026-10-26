# Runner image for the Docker sandbox (PLAN.md section 4).
# Build: docker build -t matrix-globe-runner:py311 -f docker/Dockerfile docker/
FROM python:3.11-slim

# tzdata: the IANA time zone database for zoneinfo (FinCode madrid_cutoff).
RUN pip install --no-cache-dir "pytest==9.1.1" "tzdata==2026.5"

WORKDIR /work

# The sandbox runs containers as --user 1000:1000; no root-owned writes
# are needed because /work is mounted read-only and /tmp is a tmpfs.
USER 1000:1000

CMD ["python", "-m", "pytest", "-q"]
