#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/.."

if command -v podman > /dev/null 2>&1; then
  ENGINE=podman
elif command -v docker > /dev/null 2>&1; then
  ENGINE=docker
else
  echo "No container engine found. Install podman or docker." >&2
  exit 1
fi

$ENGINE build -f Dockerfile.test -t pollen-no-tests .
$ENGINE run --rm pollen-no-tests
