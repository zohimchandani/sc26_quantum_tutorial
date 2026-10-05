# Part I: HPCQC hands-on at LRZ

Infrastructure demo (about 10 minutes): the same CUDA-Q kernel runs on the CPU, a GPU, multiple GPUs and an IQM QPU on the LRZ BEAST system, and each run is timed. The kernel is deliberately simple, so the focus stays on the infrastructure.

## Files

| Path | Content |
|---|---|
| `cudaq-gpu-qpu-dataflow.ipynb` | Hands-on notebook (4 cases + summary) |
| `hpcqc-output/` | Plots written by the notebook |
| `slides/` | Slides for the 10-minute presentation |

## System

- **BEAST** at LRZ, accessed through the LRZ Q-Open Portal (Open OnDemand)
- 15 nodes with NVIDIA A100 80 GB GPUs; GPUs can be split into 10 GB MIG slices
- 1 IQM QPU (`iqm_eqe1`)
- Jupyter kernel: `cudaq-gpu-env` (CUDA-Q, NumPy, Matplotlib)

## How to run

1. Log in to the portal and start a Jupyter session on a `wolpy` node with the `cudaq-gpu-env` kernel.
2. Open `cudaq-gpu-qpu-dataflow.ipynb` and run all cells.
3. Optional:
   - **Case 3:** request two or more GPUs or MIG slices for the session.
   - **Case 4:** request the `iqm_eqe1` license and set `USE_QPU = True`. The IQM token is read from `IQM_TOKEN`, or from `~/.iqmclient_eqe1_token` if that is not set.

Cases whose hardware is not available are skipped with a message, so the notebook always runs to the end.

## The four cases

The host (CPU) always holds the parameters and results. Only `cudaq.set_target(...)` changes.

| Case | Target | What it shows |
|---|---|---|
| 1. CPU only | `qpp-cpu` | Baseline. Fastest for small circuits. |
| 2. CPU + GPU | `nvidia` | GPU simulation pays off as the qubit count grows (10, 15 and 20 qubits). |
| 3. CPU + multi-GPU | `nvidia`, `option="mqpu"` | Many circuits spread across GPUs with `sample_async`. |
| 4. CPU + QPU | `iqm` | Same kernel on hardware. Time is mostly network and queueing. |

**Kernels:**
- `rotations` applies `rz`, `ry` and `rx` to one qubit. It is used in cases 1, 2 and 4. The expected result is P(1) = (1 − cos a₁ cos a₂)/2.
- `layer` applies `ry` to each of n qubits, followed by a CNOT chain. It is used for the timing comparisons in cases 1–3.

**Error measure:** `max |P(1) - exact|` is the worst-case error over the sweep, not fidelity. On the simulators it is only shot noise, about 0.03–0.04 with 1000 shots. On the QPU, readout and gate errors are added on top.

## Notes

- `mqpu` splits *many circuits* across GPUs. To split *one large circuit* across GPUs or nodes, use `option="mgpu"` launched with `mpirun` from a batch job. That is outside this notebook.
- Today the GPU and QPU exchange data only through the host. NVQLink is meant to connect them directly.
- Settings such as shots, sweep size and qubit counts are in the **Setup** cell.

## To do before the tutorial

- [ ] Participant test accounts ready by Oct 10, 2026
- [ ] Test case 2 (`nvidia`) on a MIG slice
- [ ] Test case 3 (`mqpu`) with two or more GPUs
- [ ] Test case 4 against `iqm_eqe1`, including the token file format
