import numpy as np
from openfermionpyscf import run_pyscf
from openfermion import get_fermion_operator, MolecularData
from openfermion.transforms import jordan_wigner as of_jordan_wigner

def get_random_configurations(orbitals: int, electrons: int | None = None, count: int =1000) -> np.ndarray:
    """Sample random electron configurations."""

    random_states = np.zeros((count, 2*orbitals))
    
    if electrons is None:
        for ind in range(len(random_states)):
            random_states[ind] = np.random.random_integers(2, size=(2*orbitals,))
        random_states -= 1 
    else:
        for ind in range(len(random_states)):
            hf_state = np.zeros(2*orbitals)
            hf_state[:electrons] = 1
            config = hf_state.copy()
            config[::2]=config[::2][np.random.permutation(orbitals)]
            config[1::2]=config[1::2][np.random.permutation(orbitals)]
            random_states[ind] = config
            
    return random_states


def get_water_geometry(bond_stretch: float = 1) -> list[tuple[str, tuple[float, float, float]]]:
    """Build raw xyz string of water for a single changing O----H bond length.
    """
    
    water_xyz_list = geom = [
        ('O', (0, 0, 0)),
        ('H', (0.2774, 0.8929, 0.2544)),
        ('H', (0.6068, -0.2383, -0.7169))
        ]

    # Stretch a single O-H bond length, keeping the H-O-H angle fixed.
    water_xyz_list[1] = ('H', (0.2774 * bond_stretch, 0.8929 * bond_stretch, 0.2544 * bond_stretch)) 
    
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

def qdrift(pauli_words: np.ndarray, coefficients: np.ndarray, samples: int, total_time_evolution: float) -> tuple[list[str], list[float]]:
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
    qdrift_terms = qdrift_rng.choice(len(circuit_terms), size=samples,
                                    p=np.abs(circuit_coefficients) / qdrift_lambda)
    qdrift_pauli_words = [pauli_words[circuit_terms[j]] for j in qdrift_terms]
    qdrift_angles = (-np.sign(circuit_coefficients[qdrift_terms])
                    * qdrift_lambda * total_time_evolution / samples).tolist()
    # qdrift_cnots = sum(2 * (len(w) - w.count("I") - 1) for w in qdrift_pauli_words)
    
    return qdrift_pauli_words, qdrift_angles