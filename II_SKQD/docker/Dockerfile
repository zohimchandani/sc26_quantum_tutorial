# CPU-only development image for the tutorial notebooks.
# CUDA-Q runs on its CPU simulators (qpp-cpu); there is no GPU in the container.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        cudaq \
        numpy scipy matplotlib \
        openfermion openfermionpyscf pyscf pubchempy \
        jupyterlab ipykernel ferrmion

WORKDIR /work
EXPOSE 8888
# A token is required: with no auth, Jupyter rejects POSTs from clients such
# as VS Code ("'_xsrf' argument missing"), so kernel restarts fail.
# The port is only published on 127.0.0.1 (see compose.yaml).
ENV JUPYTER_TOKEN=sc26
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]