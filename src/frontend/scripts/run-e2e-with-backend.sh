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
FRONTEND_LOG="${E2E_DEPLOY}/frontend.log"

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
FRONTEND_PID=""

kill_process_tree() {
  local pid="${1:-}"
  local child_pid

  if [ -z "${pid}" ]; then
    return
  fi

  for child_pid in $(pgrep -P "${pid}" 2>/dev/null || true); do
    kill_process_tree "${child_pid}"
  done

  kill "${pid}" >/dev/null 2>&1 || true
}

cleanup() {
  kill "${FLASK_PID}" >/dev/null 2>&1 || true
  if [ -n "${FRONTEND_PID}" ]; then
    kill_process_tree "${FRONTEND_PID}"
  fi
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

cd "${FRONTEND_DIR}"

if curl --silent --fail http://localhost:5173 >/dev/null 2>&1; then
  echo "Using existing frontend at http://localhost:5173."
else
  echo "Starting frontend at http://localhost:5173 ..."
  echo "Frontend logs: ${FRONTEND_LOG}"
  npm run dev >"${FRONTEND_LOG}" 2>&1 &
  FRONTEND_PID=$!
fi

echo "Waiting for frontend at http://localhost:5173 ..."
for _ in {1..90}; do
  if curl --silent --fail http://localhost:5173 >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl --silent --fail http://localhost:5173 >/dev/null 2>&1; then
  echo "Frontend did not become available."
  exit 1
fi

echo "Running Playwright against test database: ${DB_PATH}"
npm run test:e2e -- "$@"
