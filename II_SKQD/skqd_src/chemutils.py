import numpy as np
from openfermionpyscf import run_pyscf
from openfermion import get_fermion_operator, MolecularData
from openfermion.transforms import jordan_wigner as of_jordan_wigner
import matplotlib.pyplot as plt

def sample_krylov_evolution_circuit(pauli_words: list[str],
                                    coefficients: list[float],
                                    n_qdrift_samples: int,
                                    evolution_time: float,
                                    max_krylov_power: int,
                                    shot_count: int,
                                    ) -> dict:
    """
    Sample the Krylov evolution circuit for a given power k.

    Args:
        max_krylov_power: Maximum power k for computing U^k|ψ⟩
        shot_count: Number of shots to sample
        shots_count: Number of shots to sample
    """

    sim_measurements = []
    unique_bitstrings = set()
    
    
    qdrift_terms, angles = sample_qdrift_terms(pauli_words, coefficients, n_qdrift_samples, evolution_time)
    

    for krylov_power in range(max_krylov_power):
        t0 = time.perf_counter()

        sampling_result = cudaq.sample(
            quantum_krylov_circuit,
            molecule.n_qubits,
            molecule.n_electrons,
            krylov_power,
            qdrift_terms,
            angles,
            qdrift,
            shots_count=shot_count,
        )

        sim_measurements.append(dict(sampling_result.items()))
        unique_bitstrings.update(sampling_result)

        print(
            f"Krylov state U^{krylov_power}: {len(sampling_result)} unique bitstrings "
            f"{len(unique_bitstrings)} cumulative "
            f"({time.perf_counter() - t0:.1f} s)"
        )

    cumulative_results = calculate_cumulative_results(sim_measurements)
    return cumulative_results

def plot_qdrift_terms(required_qdrift_terms, coefficients):
    qdrift_lambda = np.sum(coefficients)
    times = np.logspace(1, 4)
    for error in np.logspace(-1, -6, 6):
        plt.plot(times, [required_qdrift_terms(error, t, qdrift_lambda) for t in times], label=f"{error:.2e}")
    plt.title("Required qDRIFT Terms")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Evolution Time")
    plt.legend()
    plt.show()

def plot_ci_convergence(reference_energy, random=None, hf=None, charge=None, spin=None, skqd=None):
    
    vals = {
        "Random":random,
        "HF":hf,
        "Charge":charge,
        "Spin":spin,
        "SKQD":skqd,
            }
    vals = {k:v for k,v in vals.items() if v is not None}
    counts = []
    
    for name,data in vals.items():
        if type(data) is list:
            data = np.array(data)

        if len(counts) == 0:
            counts = [i*100 for i in range(len(data))] 
        plt.plot(counts, data-reference_energy, label=name)
    
        if len(counts)!=0:
            plt.plot(counts, [1.6e-3]*len(counts), color = 'k' ,linestyle = ":")
    plt.legend()
    plt.title("Accuracy of Selected Configuration Interaction")
    plt.xlabel("N Configurations")
    plt.ylabel("Energy Error")
    plt.yscale("log")
    plt.show()

def get_random_configurations(
    orbitals: int, electrons: int | None = None, count: int = 40000
) -> np.ndarray:
    """Sample random electron configurations."""

    random_states = np.zeros((count, 2 * orbitals))
    
    if electrons is None:
        for ind in range(len(random_states)):
            random_states[ind] = np.random.random_integers(2, size=(2 * orbitals,))
        random_states -= 1
    else:
        for ind in range(len(random_states)):
            hf_state = np.zeros(2 * orbitals)
            hf_state[:electrons] = 1
            config = hf_state.copy()
            config[::2] = config[::2][np.random.permutation(orbitals)]
            config[1::2] = config[1::2][np.random.permutation(orbitals)]
            random_states[ind] = config

    unique = np.unique(random_states, axis=0)
    return unique[np.random.permutation(np.arange(unique.shape[0]))]

def get_nitrogen_geometry(
    bond_length: float = 1,
) -> list[tuple[str, tuple[float, float, float]]]:
    """Build raw xyz string of water for a single changing O----H bond length."""

    xyz_list= [
        ("N", (0, 0, 0)),
        ("N", (bond_length, 0, 0)),
    ]


    return xyz_list

def get_water_geometry(
    bond_stretch: float = 1,
) -> list[tuple[str, tuple[float, float, float]]]:
    """Build raw xyz string of water for a single changing O----H bond length."""

    water_xyz_list = [
        ("O", (0, 0, 0)),
        ("H", (0.2774, 0.8929, 0.2544)),
        ("H", (0.6068, -0.2383, -0.7169)),
    ]

    # Stretch a single O-H bond length, keeping the H-O-H angle fixed.
    water_xyz_list[1] = (
        "H",
        (0.2774 * bond_stretch, 0.8929 * bond_stretch, 0.2544 * bond_stretch),
    )

    return water_xyz_list


def jordan_wigner(molecule: MolecularData) -> tuple[np.ndarray, np.ndarray]:
    """Get the Jordan-Wigner transformed Pauli words and coefficients of the Hamiltonian.

    Args:
        molecule: OpenFermion MolecularData object with the Hamiltonian.
    Returns:
        pauli_words: List of Pauli words for the Hamiltonian
        hamiltonian_coefficients_numpy: Numpy array of coefficients for the Hamiltonian
    """
    H = of_jordan_wigner(get_fermion_operator(molecule.get_molecular_hamiltonian()))
    H.compress()

    # OpenFermion terms -> Pauli words, with qubit i at position i of the word
    pauli_words, hamiltonian_coefficients = [], []
    for term, coeff in H.terms.items():
        assert abs(coeff.imag) < 1e-6
        word = ["I"] * molecule.n_qubits
        for qubit, pauli in term:
            word[qubit] = pauli
        pauli_words.append("".join(word))
        hamiltonian_coefficients.append(coeff.real)
    pauli_words_numpy = np.array(pauli_words)
    hamiltonian_coefficients_numpy = np.array(hamiltonian_coefficients)

    return pauli_words_numpy, hamiltonian_coefficients_numpy


def qdrift(
    pauli_words: np.ndarray,
    coefficients: np.ndarray,
    samples: int,
    total_time_evolution: float,
) -> tuple[list[str], list[float]]:
    """qDRIFT Stochastic Hamiltonian simulation (Campbell, PRL 123, 070503, 2019).

    Args:
        pauli_words: List of Pauli words for the Hamiltonian.
        coefficients: Numpy array of coefficients for the Hamiltonian.
        samples: Number of gates in the qDRIFT sequence for one application of U.
        total_time_evolution: Total time evolution for U = exp(-iHt).
    Returns:
        qdrift_pauli_words: List of Pauli words for the qDRIFT sequence
        qdrift_angles: List of angles for the qDRIFT sequence

    Example:
        qdrift_pauli_words, qdrift_angles = qdrift(molecule, samples=200, total_time_evolution=np.pi)
    """

    # The identity term only adds a global phase to the time evolution, so it is
    # left out of the circuit (it stays in the Hamiltonian for post-processing).
    circuit_terms = [i for i, w in enumerate(pauli_words) if set(w) != {"I"}]
    circuit_coefficients = coefficients[circuit_terms]

    # qDRIFT: draw the gate sequence for U = exp(-iHt)
    qdrift_lambda = np.abs(circuit_coefficients).sum()
    qdrift_rng = np.random.default_rng(7)
    qdrift_terms = qdrift_rng.choice(
        len(circuit_terms), size=samples, p=np.abs(circuit_coefficients) / qdrift_lambda
    )
    qdrift_pauli_words = [pauli_words[circuit_terms[j]] for j in qdrift_terms]
    qdrift_angles = (
        -np.sign(circuit_coefficients[qdrift_terms])
        * qdrift_lambda
        * total_time_evolution
        / samples
    ).tolist()
    # qdrift_cnots = sum(2 * (len(w) - w.count("I") - 1) for w in qdrift_pauli_words)

    return qdrift_pauli_words, qdrift_angles
