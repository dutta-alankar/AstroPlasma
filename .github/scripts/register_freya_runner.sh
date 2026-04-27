#!/usr/bin/env bash
set -euo pipefail

# Register a GitHub self-hosted runner for this repository on Freya.
#
# Required:
#   RUNNER_TOKEN   One-time registration token from:
#                  Repo -> Settings -> Actions -> Runners -> New self-hosted runner
#
# Optional env vars:
#   REPO_URL            default: https://github.com/dutta-alankar/AstroPlasma
#   RUNNER_ROOT         default: $HOME/actions-runner-astroplasma
#   RUNNER_VERSION      default: 2.326.0
#   RUNNER_NAME         default: <hostname>-gpu
#   RUNNER_LABELS       default: self-hosted,linux,freya,gpu,slurm
#   RUNNER_WORKDIR      default: _work
#   START_MODE          default: interactive (interactive|nohup)
#   FORCE_RECONFIGURE   default: 0 (set to 1 to re-run config with --replace)

REPO_URL="${REPO_URL:-https://github.com/dutta-alankar/AstroPlasma}"
RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runner-astroplasma}"
RUNNER_VERSION="${RUNNER_VERSION:-2.326.0}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname -s)-gpu}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,linux,freya,gpu,slurm}"
RUNNER_WORKDIR="${RUNNER_WORKDIR:-_work}"
START_MODE="${START_MODE:-interactive}"
FORCE_RECONFIGURE="${FORCE_RECONFIGURE:-0}"

if [[ -z "${RUNNER_TOKEN:-}" ]]; then
  echo "error: RUNNER_TOKEN is required." >&2
  exit 1
fi

mkdir -p "${RUNNER_ROOT}"
cd "${RUNNER_ROOT}"

RUNNER_TGZ="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_TGZ}"

if [[ ! -x "./config.sh" ]]; then
  echo "Downloading GitHub Actions runner ${RUNNER_VERSION}..."
  curl -fsSL -o "${RUNNER_TGZ}" "${RUNNER_URL}"
  tar xzf "${RUNNER_TGZ}"
  rm -f "${RUNNER_TGZ}"
fi

if [[ -f ./.runner && "${FORCE_RECONFIGURE}" != "1" ]]; then
  echo "Runner already configured in ${RUNNER_ROOT}."
  echo "Set FORCE_RECONFIGURE=1 to reconfigure with --replace."
else
  echo "Configuring runner ${RUNNER_NAME} for ${REPO_URL}..."
  ./config.sh \
    --url "${REPO_URL}" \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --work "${RUNNER_WORKDIR}" \
    --unattended \
    --replace
fi

case "${START_MODE}" in
  interactive)
    cat <<MSG
Runner is configured.
Start it in the current shell with:
  cd ${RUNNER_ROOT}
  ./run.sh
MSG
    ;;
  nohup)
    LOG_FILE="${RUNNER_ROOT}/runner-nohup.log"
    nohup ./run.sh >"${LOG_FILE}" 2>&1 &
    echo "Runner started in background (nohup)."
    echo "Log: ${LOG_FILE}"
    ;;
  *)
    echo "error: START_MODE must be 'interactive' or 'nohup'" >&2
    exit 1
    ;;
esac
