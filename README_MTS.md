# DeePMD-kit with Scale MTS

This repository extends DeePMD-kit with the LAMMPS pair style
`deepmd/mts`, which switches between two Deep Potential models
at a specified MD-step interval.

Based on DeePMD-kit commit:
`be437483c3b6bd3633efd62fdf0a0ce3a9efa089`

## Tested environment

- Ubuntu 22.04
- Python 3.11
- TensorFlow 2.16.1
- CUDA 12.3 / cuDNN 8.9
- CMake 3.27
- GCC 11.4
- LAMMPS stable_2Aug2023_update3
- NVIDIA Quadro RTX 8000

## GPU installation

Run these commands from the repository root.
CUDA Toolkit 12.3 must be installed at `/usr/local/cuda-12.3`.

~~~bash
conda create -n mts-release-build python=3.11 cmake=3.27 pip -y
conda activate mts-release-build
python -m pip install 'tensorflow[and-cuda]==2.16.1'

export CUDA_HOME=/usr/local/cuda-12.3
export PATH="$CUDA_HOME/bin:$PATH"

cmake -S source -B source/build-gpu \
  -DUSE_TF_PYTHON_LIBS=TRUE \
  -DUSE_CUDA_TOOLKIT=TRUE \
  -DCUDAToolkit_ROOT="$CUDA_HOME" \
  -DCUDA_TOOLKIT_ROOT_DIR="$CUDA_HOME" \
  -DCMAKE_CUDA_COMPILER="$CUDA_HOME/bin/nvcc" \
  -DCMAKE_INSTALL_PREFIX="$PWD/install-gpu" \
  -DCMAKE_BUILD_TYPE=Release

cmake --build source/build-gpu -j4
cmake --install source/build-gpu
cmake --build source/build-gpu --target lammps -j4
~~~

## Build LAMMPS

~~~bash
ROOT="$PWD"

curl -fL \
  https://github.com/lammps/lammps/archive/refs/tags/stable_2Aug2023_update3.tar.gz \
  -o lammps-2023.tar.gz

tar -xzf lammps-2023.tar.gz

cp -a source/build-gpu/USER-DEEPMD \
  lammps-stable_2Aug2023_update3/src/

cd lammps-stable_2Aug2023_update3/src

make yes-kspace
make yes-extra-fix
make yes-molecule
make yes-user-deepmd
make serial -j4

cd "$ROOT"

export LD_LIBRARY_PATH="$ROOT/install-gpu/lib:$CONDA_PREFIX/lib/python3.11/site-packages/tensorflow:${LD_LIBRARY_PATH:-}"

for lib in "$CONDA_PREFIX"/lib/python3.11/site-packages/nvidia/*/lib; do
  [ ! -d "$lib" ] || export LD_LIBRARY_PATH="$lib:${LD_LIBRARY_PATH:-}"
done
~~~

## MTS usage

Supply two compatible Deep Potential models.

For 1:1 switching (6 Å every 2 steps):

~~~text
pair_style deepmd/mts /path/to/4ang.pb /path/to/6ang.pb timestep 2
pair_coeff * * Ti O
~~~

For 1:3 switching (6 Å every 4 steps):

~~~text
pair_style deepmd/mts /path/to/4ang.pb /path/to/6ang.pb timestep 4
pair_coeff * * Ti O
~~~

The `timestep` keyword specifies the model-switching period,
not the MD integration timestep.

## Validation

GPU smoke tests completed successfully for a 12,000-atom TiO2
system, using 100 MD steps per case:

- 4 Å model only
- 6 Å model only
- MTS 1:1
- MTS 1:3

Potential energies recorded for 20 steps showed the expected
2-step and 4-step switching patterns.

These tests do not replace full production-scale validation.
Model files and proprietary datasets are not distributed.

## License and citation

See `LICENSE` for the original DeePMD-kit license.
The paper citation and contributor attribution will be
finalized before public release.
