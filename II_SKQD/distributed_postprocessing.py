"""
Multi-GPU SKQD Eigenvalue Solver

Usage:
    Save the code below in a distributed_postprocessing.py file
    Execute with the command below, for example on a system with 8 GPUs: 
    mpirun -np 8 --bind-to none --allow-run-as-root python distributed_postprocessing.py 
"""

import numpy as np
import cupy as cp
from skqd_src.pre_and_postprocessing import *
from mpi4py import MPI
import pickle
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

n_devices = cp.cuda.runtime.getDeviceCount()
my_gpu = rank % n_devices
cp.cuda.Device(my_gpu).use()

tile_size = 32

#uncomment this to load the data
# with open('skqd_data.pkl', 'rb') as f:
#     data = pickle.load(f)
#     basis_states = data['basis_states']
#     pauli_words = data['pauli_words']
#     hamiltonian_coefficients_numpy = data['hamiltonian_coefficients']



subspace_dimension = basis_states.shape[0]

ham_data = prepare_hamiltonian_data(basis_states, pauli_words, hamiltonian_coefficients_numpy)
cp.cuda.Device(my_gpu).synchronize()

nccl_comm_obj = None
if size > 1:
    from cupy.cuda import nccl
    if rank == 0:
        nccl_id = nccl.get_unique_id()
    else:
        nccl_id = None
    nccl_id = comm.bcast(nccl_id, root=0)
    nccl_comm_obj = nccl.NcclCommunicator(size, nccl_id, rank)

np.random.seed(42)
v0_np = np.random.random((subspace_dimension,)).astype(np.float64)
v0_np = v0_np / np.linalg.norm(v0_np)
v0 = cp.asarray(v0_np, dtype=cp.complex128)

cp.get_default_memory_pool().free_all_blocks()

ncv = min(20, subspace_dimension - 1)

eigenvalues, = distributed_eigsh(
    ham_data, rank, size, nccl_comm_obj,
    k=1, which='SA', ncv=ncv, v0_full=v0,
    tile_size=tile_size, return_eigenvectors=False)

eigenvalue = eigenvalues[0]
cp.cuda.Device(my_gpu).synchronize()
eigenvalue_real = float(cp.asnumpy(eigenvalue).real)

MPI.Finalize()
