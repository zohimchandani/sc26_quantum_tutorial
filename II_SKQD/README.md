# Part II: Sample-Based Krylov Quantum Diagonalization (SKQD)

Adapted from the CUDA-Q SKQD tutorial ([docs](https://nvidia.github.io/cuda-quantum/latest/applications/python/skqd.html), source `docs/sphinx/applications/python/` in NVIDIA/cuda-quantum at `a93bee6fd567`).

## Changes from upstream

| Upstream | Here |
|---|---|
| 22-qubit Heisenberg chain | H₂O in STO-3G (14 qubits, Jordan-Wigner), geometry from PubChem via OpenFermion, FCI reference from PySCF |
| Néel reference state | Hartree-Fock state (first 10 spin orbitals occupied) |
| Trotter evolution (8 steps) | qDRIFT, 200 gates per U (about 640 CNOTs instead of about 16,600 per Trotter step) |
| GPU required (CuPy) | Falls back to NumPy/SciPy when there is no GPU, including a CPU matrix-free Lanczos (`matrix_free_eigsh_cpu`) |
| 100,000 shots | 100,000 on GPU, 1,000 on CPU |

## How to run on a laptop (CPU)

From the repository root:

```bash
docker compose up --build
```

Then open http://127.0.0.1:8888 and run `II_SKQD/skqd.ipynb`. The first cell needs network access to fetch the geometry from PubChem. A full run takes about 1 minute on an Apple Silicon Mac and converges to the FCI energy (-75.015530 Ha) by Krylov dimension 6.

## Notes

- 14 qubits is a development-sized problem: the sampled subspace reaches about 1,000 states, so SKQD recovers FCI essentially exactly. Larger molecules or basis sets are needed to show the method under pressure.
- The last code cell writes `distributed_postprocessing.py` (multi-GPU solver, needs `mpi4py` and GPUs) rather than running it.
