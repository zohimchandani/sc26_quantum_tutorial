# Part I: HPCQC hands-on at LRZ

Play around with a sample CUDA-Q kernel (a GHZ state) that runs on a CPU, a GPU, multiple GPUs and an IQM quantum
computer at LRZ. The kernel is deliberately simple, so the focus stays on
the infrastructure: where the code runs and how data moves between CPU, GPU and QPU.

## Outline

1. **Introduction (slides, about 10 minutes):** the LRZ HPCQC infrastructure.
2. **Log in to the portal** and open the notebook ([below](#logging-in-to-the-portal)).
3. **Hands-on notebook** [`cudaq-from-cpu-gpu-to-qpu.ipynb`](cudaq-from-cpu-gpu-to-qpu.ipynb):

   | Case | Where the kernel runs | What it shows |
   |---|---|---|
   | 1. CPU only | `qpp-cpu` simulator | The baseline; fastest for small circuits |
   | 2. Single-GPU | `nvidia` simulator on a GPU slice | GPU simulation pays off as the qubit count grows (10, 15, 20 qubits) |
   | 3. Multi-GPU | `nvidia`, `option="mqpu"`, as a separate job on 4 GPUs | Many circuits in parallel (`sample_async`), and a Hamiltonian split over 4 MPI ranks |
   | 4. QPU | `iqm`, the IQM quantum computer | The same kernel on hardware: time is mostly network and queueing, results show hardware noise |
   | Summary | | Results and timing of all backends side by side |

   Only `cudaq.set_target(...)` changes between the cases; the host (CPU) always holds the input
   and the results.
