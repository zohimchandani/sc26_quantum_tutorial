# CPU-only development image for the tutorial notebooks.
# CUDA-Q runs on its CPU simulators (qpp-cpu); there is no GPU in the container.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        cudaq \
        numpy scipy matplotlib \
        openfermion openfermionpyscf pyscf pubchempy \
        jupyterlab ipykernel

WORKDIR /work
EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--ServerApp.token=", "--ServerApp.password="]
