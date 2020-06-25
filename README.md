![cryspy_logo](./docs/_images/cryspy_fix-03.png)

# CrySPY
CrySPY is a crystal structure prediction tool written in Python.

## Latest version
version 0.9.0 (2020 ???? ??)

## Important changes
* version 0.9.0
    - Interfaced with OpenMX
    - PyXtal is required
    - New structure-generation mode using PyXtal
        + Molecular crystal
* version 0.8.0
    - Migrated to Python 3
    - Several variable names
    - Several data formats
    - Unit of energy in output: eV/cell --> eV/atom
    - No. of working directories corresponds to structure ID
* version 0.7.0
    - Evolutionary algorithm is now available
* version 0.6.2
    - LAMMPS can be used in CrySPY
* version 0.6.0
    - LAQA is now available
    - Changed the data format of init_struc_data and opt_struc_data from list to dict

## System requirements
### Python
- Python 3.x.x
- [COMBO](https://github.com/tsudalab/combo3 "COMBO")
- numpy
- pandas
- [pymatgen](http://pymatgen.org "pymatgen")
- [PyXtal](https://pyxtal.readthedocs.io/en/latest "PyXtal")

Tested with Python 3.7.5 on Mac and Python 3.6.7 (miniconda3-4.3.30) on Linux (super computer).

### Structure optimizer
At least one optimizer is required.

- [VASP](https://www.vasp.at "VASP") (tested with version 5.4.1)
- [Quantum ESPRESSO](http://www.quantum-espresso.org "Quantum ESPRESSO") (tested with version 6.1, version 5.x does not work)
- [OpenMX](http://www.openmx-square.org "OpenMX")
- [soiap](https://github.com/nbsato/soiap "soiap") (tested with version 0.2.2)
- [LAMMPS](http://lammps.sandia.gov "LAMMPS")

### Others
- [find_wy](https://github.com/nim-hrkn/find_wy "find_wy"): find_wy can randomly select a combination of Wyckoff positions for a given chemical composition and space group. (optional)

## Document
[CrySPY document](https://tomoki-yamashita.github.io/CrySPY "CrySPY documment")

## Google group
[Google gruop of CrySPY](https://groups.google.com/forum/#!forum/cryspy-user "Google group")


## Tutorial (written in Japanese)
[チュートリアルと解説](https://tomoki-yamashita.github.io/cryspy/tutorial/outline.html "tutorial")


## Reference
### Bayesian optimization
* T. Yamashita, N. Sato, H. Kino, T. Miyake, K. Tsuda, and T. Oguchi, Phys. Rev. Mater. **2**, 013803 (2018).
    - https://journals.aps.org/prmaterials/abstract/10.1103/PhysRevMaterials.2.013803

* N. Sato, T. Yamashita, T. Oguchi, K. Hukushima, and T. Miyake, Phys. Rev. Mater. **4**, 033801 (2020).
    - https://journals.aps.org/prmaterials/abstract/10.1103/PhysRevMaterials.4.033801


### LAQA
* K.Terayama, T. Yamashita, T. Oguchi, and K. Tsuda, npj Comput. Mater. **4**, 32 (2018).
    - https://www.nature.com/articles/s41524-018-0090-y


## License
CrySPY is distributed under the MIT License.  
Copyright (c) 2018 CrySPY Development Team
