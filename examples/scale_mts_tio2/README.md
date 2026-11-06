# Scale MTS: TiO2 Example

This example provides the trained Deep Potential models, LAMMPS
inputs, and analysis scripts used for Scale MTS simulations of
anatase TiO2.

For installation instructions, see [README_MTS.md](../../README_MTS.md).

## Simulation settings

- System: anatase TiO2, 12,000 atoms
- Ensemble: NPT, 300 K, 1 bar
- MD timestep: 1 fs
- Production run: 1,000,000 steps
- Additional trajectory: 1,000 steps
- Initial structure: 12 atoms, replicated 10 x 10 x 10

| Directory | Model |
|---|---|
| `lammps/4/` | 4 Å model |
| `lammps/6/` | 6 Å model |
| `lammps/1:1/` | MTS, 6 Å every 2 steps |
| `lammps/1:3/` | MTS, 6 Å every 4 steps |

## Running simulations

After building LAMMPS and configuring the runtime libraries,
run the following commands from the repository root:

~~~bash
REPO="$PWD"
EX="$REPO/examples/scale_mts_tio2"
LMP="$REPO/lammps-stable_2Aug2023_update3/src/lmp_serial"

for case in 4 6 '1:1' '1:3'; do
    (cd "$EX/lammps/$case" && "$LMP" -in lammps.in) || break
done
~~~

These commands use the original production simulation settings.

## Analysis

Install the required Python packages:

~~~bash
python -m pip install numpy matplotlib ovito
~~~

After completing the MD simulations:

~~~bash
cd "$EX"

# Thermodynamic properties
python analysis/plot_thermo_compare.py \
  --base_dir lammps --paths 4 6 '1:1' '1:3'

# Radial distribution functions
python analysis/plot_rdf_pair_compare.py \
  --base_dir lammps --paths 4 6 '1:1' '1:3'

# NPT block averages
python analysis/calc_block_average_npt.py \
  --base_dir lammps --paths 4 6 '1:1' '1:3'
~~~

The analysis scripts are based on those used in the original study.
Full-length MD outputs are required for meaningful statistical analysis.

## Notes

The provided 4 Å and 6 Å models are pre-trained.
The training workflow follows standard DeePMD-kit procedures.

## Quick test (100 steps)

To verify the installation without running the full simulation:

~~~bash
cd "$EX/lammps/1:3"

sed -e 's/^run 1000000$/run 100/' \
    -e 's/^run 1000$/run 0/' \
    lammps.in > smoke.in

"$LMP" -in smoke.in
rm -f smoke.in
~~~

This is a functionality check, not a production MD simulation.
