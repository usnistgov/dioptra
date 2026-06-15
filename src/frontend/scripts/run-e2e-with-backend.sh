#!/usr/bin/env bash
set -eo pipefail

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${FRONTEND_DIR}/../.." && pwd)"

if [ -n "${DIOPTRA_E2E_ENV_FILE:-}" ]; then
  ENV_FILE="${DIOPTRA_E2E_ENV_FILE}"
elif [ -f "${REPO_DIR}/env-dev.cfg" ]; then
  ENV_FILE="${REPO_DIR}/env-dev.cfg"
elif [ -f "${REPO_DIR}/../env-dev.cfg" ]; then
  ENV_FILE="${REPO_DIR}/../env-dev.cfg"
else
  echo "Could not find env-dev.cfg."
  echo "Set DIOPTRA_E2E_ENV_FILE=/path/to/env-dev.cfg and try again."
  exit 1
fi

E2E_DEPLOY="${DIOPTRA_E2E_DEPLOY:-${FRONTEND_DIR}/.dioptra-e2e}"
DB_PATH="${E2E_DEPLOY}/instance/dioptra-test.db"

if curl --silent --fail http://localhost:5000/health >/dev/null 2>&1; then
  echo "A backend is already running on http://localhost:5000."
  echo "Stop it before running this command so tests do not write to the dev DB."
  exit 1
fi

source "${REPO_DIR}/dev-kb/local-setup/dev-set.sh" --env "${ENV_FILE}"

mkdir -p "${E2E_DEPLOY}/instance" "${E2E_DEPLOY}/workdir"

export DIOPTRA_DEPLOY="${E2E_DEPLOY}"
export DIOPTRA_RESTAPI_DEV_DATABASE_URI="sqlite:///${DB_PATH}"

"${REPO_DIR}/dev-kb/local-setup/run-flask.sh" &
FLASK_PID=$!

cleanup() {
  kill "${FLASK_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Waiting for test backend at http://localhost:5000/health ..."
for _ in {1..90}; do
  if curl --silent --fail http://localhost:5000/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl --silent --fail http://localhost:5000/health >/dev/null 2>&1; then
  echo "Test backend did not become healthy."
  exit 1
fi

echo "Running Playwright against test database: ${DB_PATH}"
cd "${FRONTEND_DIR}"
npm run test:e2e -- "$@"
