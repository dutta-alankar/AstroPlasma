#!/usr/bin/env bash
set -euo pipefail

# Submit GPU tests to Freya Slurm and block until completion.

if ! command -v sbatch >/dev/null 2>&1; then
  echo "error: sbatch not found. This job must run on a Freya node with Slurm available." >&2
  exit 1
fi

REPO_ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
SLURM_SCRIPT="$(mktemp -t astroplasma-gpu-XXXXXX.sbatch)"

cat >"${SLURM_SCRIPT}" <<EOF
#!/usr/bin/env bash
#SBATCH --job-name=astroplasma-gpu-ci
#SBATCH --partition=p.gpu
#SBATCH --nodes=1            # Request 1 or more full nodes
#SBATCH --constraint="gpu"   #   providing GPUs.
#SBATCH --gres=gpu:1    # Request 1 GPU per node.
#SBATCH --ntasks-per-node=1  # Run one task per GPU
#SBATCH --cpus-per-task=1    #   using 1 cores for each task.
#SBATCH --mail-type=none
#SBATCH --time=00:45:00
#SBATCH --output=${REPO_ROOT}/slurm-%j.out

set -euo pipefail

module purge
module load cuda/12.8 gcc/12 openmpi/4.1

export LD_LIBRARY_PATH="/mpcdf/soft/SLE_15/packages/skylake/openmpi/gcc_12-12.1.0/4.1.8/lib:${LD_LIBRARY_PATH:-}"

cd "${REPO_ROOT}"

if [[ ! -f .venv/bin/activate ]]; then
  echo "error: .venv is missing in ${REPO_ROOT}. Ensure workflow step 'Prepare virtual environment' ran." >&2
  exit 1
fi

source .venv/bin/activate

if [[ -x .venv/bin/uv ]]; then
  UV_BIN=.venv/bin/uv
elif command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
else
  echo "error: uv is unavailable. Ensure workflow prep step installs dependencies with uv." >&2
  exit 1
fi

# Derive the header location from the venv interpreter itself, so this keeps
# working when the Python version changes.
PY_INCLUDE="\$(python -c 'import sysconfig; print(sysconfig.get_paths()["include"])')"
MPICC=/mpcdf/soft/SLE_15/packages/skylake/openmpi/gcc_12-12.1.0/4.1.8/bin/mpicc

MPICC="\${MPICC}" \
CPPFLAGS="-I\${PY_INCLUDE}" \
CFLAGS="-I\${PY_INCLUDE}" \
"\${UV_BIN}" pip install --python "${REPO_ROOT}/.venv/bin/python" \
  --force-reinstall --no-cache-dir --no-binary=mpi4py mpi4py

export RUN_ON_CUDA=1
python -m pytest tests/test_cuda.py -v
EOF

chmod +x "${SLURM_SCRIPT}"

echo "Submitting Slurm job with script: ${SLURM_SCRIPT}"
JOB_ID="$(sbatch --parsable "${SLURM_SCRIPT}" | cut -d';' -f1)"

if [[ -z "${JOB_ID}" ]]; then
  echo "error: failed to parse Slurm job id from sbatch output" >&2
  exit 1
fi

echo "Submitted job id: ${JOB_ID}"

LOG_FILE="${REPO_ROOT}/slurm-${JOB_ID}.out"

while true; do
  STATE="$(sacct -j "${JOB_ID}" --format=State --noheader 2>/dev/null | head -n1 | awk '{print $1}')"
  if [[ -z "${STATE}" ]]; then
    STATE="$(squeue -j "${JOB_ID}" -h -o "%T" 2>/dev/null | head -n1 || true)"
  fi

  echo "Job ${JOB_ID} state: ${STATE:-UNKNOWN}"

  case "${STATE}" in
    COMPLETED)
      break
      ;;
    FAILED|CANCELLED|TIMEOUT|PREEMPTED|NODE_FAIL|OUT_OF_MEMORY|BOOT_FAIL|DEADLINE)
      if [[ -f "${LOG_FILE}" ]]; then
        echo "--- Slurm log tail (${LOG_FILE}) ---"
        tail -n 200 "${LOG_FILE}" || true
      fi
      exit 1
      ;;
    PENDING|CONFIGURING|RUNNING|COMPLETING|"")
      ;;
    *)
      ;;
  esac

  sleep 20
done

if [[ -f "${LOG_FILE}" ]]; then
  echo "--- Slurm log tail (${LOG_FILE}) ---"
  tail -n 200 "${LOG_FILE}" || true
fi

echo "Slurm GPU test job ${JOB_ID} completed successfully."
