"""%%beast for Google Colab: `import colab_skip_beast_cells` defines it.

On the LRZ system, a %%beast cell runs as a Slurm job on the cluster. In Colab, it runs right
here in the notebook instead; --mpi cells, and GPU cells on a runtime without a GPU, are skipped.
"""

import os
from pathlib import Path

from IPython import get_ipython
from IPython.core.magic import register_cell_magic


class LocalJob:                              # used like the LRZ job: NAME.result(), NAME.files
    def __init__(self, name, message):
        self.name, self.message = name, message

    def result(self):
        return self.message

    @property
    def files(self):
        folder = Path(f"jobs/{self.name}/output")
        return sorted(folder.resolve().iterdir()) if folder.exists() else []


@register_cell_magic
def beast(line, cell):
    import cudaq
    opts = line.split()
    name = opts[0]
    gpus = int(opts[opts.index("--gpus") + 1]) if "--gpus" in opts else 1
    if "--mpi" in opts:
        message = f"{name}: skipped, this cell needs {gpus} GPUs with MPI and runs only on the LRZ system."
    elif gpus > 0 and cudaq.num_available_gpus() == 0:
        message = f"{name}: skipped, this cell needs a GPU, but no GPU is available."
    else:
        folder = Path(f"jobs/{name}")        # one folder per cell, like a job on the cluster
        (folder / "output").mkdir(parents=True, exist_ok=True)
        here = os.getcwd()
        os.chdir(folder)
        try:
            exec(cell, get_ipython().user_ns)
        except Exception:
            get_ipython().user_ns[name] = LocalJob(name, f"{name}: failed, see the error above.")
            raise
        finally:
            os.chdir(here)
        message = f"{name}: the cell output is above."
    print(message)
    get_ipython().user_ns[name] = LocalJob(name, message)
