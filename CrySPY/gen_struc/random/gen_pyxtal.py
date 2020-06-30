'''
Random structure generation using PyXtal
    https://github.com/qzhu2017/PyXtal
'''

import random
import warnings

from pyxtal.crystal import random_crystal
from pyxtal.molecular_crystal import molecular_crystal

from ..struc_util import sort_by_atype
from ..struc_util import out_poscar


class Rnd_struc_gen_pyxtal:
    '''
    Random structure generation using pyxtal

    # ---------- args
    natot (int): number of atoms, e.g. 12 for Si4O8

    atype (list): atom type, e.g. ['Si', 'O'] for Si4O8

    nat (list): number of atom, e.g. [4, 8] for Si4O8

    vol_factor (int or float): default --> 1.0
                        volume factor

    spgnum ('all' or list): space group numbers which you use
                            'all' --> 1--230
                            list --> e.g. [1, 3, 100 ..., 229, 230]

    symprec (float): default --> 0.01
                     tolerance for symmetry finding
    '''

    def __init__(self, natot, atype, nat, vol_factor=1.0,
                 spgnum='all', symprec=0.01):
        # ---------- check args
        # ------ int
        for i in [natot]:
            if type(i) is int and i > 0:
                pass
            else:
                raise ValueError('natot must be positive int')
        # ------ list
        for x in [atype, nat]:
            if type(x) is not list:
                raise ValueError('atype and nat must be list')
        if not len(atype) == len(nat):
            raise ValueError('not len(atype) == len(nat)')
        # ------ vol_factor
        if type(vol_factor) is not float and type(vol_factor) is not int:
            raise ValueError('vol_factor must be int or float')
        if vol_factor <= 0:
            raise ValueError('vol_factor must be positive')
        # ------ spgnum
        if spgnum == 'all' or type(spgnum) is list:
            pass
        else:
            raise ValueError('spgnum is wrong. spgnum = {}'.format(spgnum))
        # ------ self.xxx = xxx
        self.natot = natot
        self.atype = atype
        self.nat = nat
        self.vol_factor = vol_factor
        self.spgnum = spgnum
        self.symprec = symprec
        # ------ error list for spg number
        self.spg_error = []

    def set_mol(self, mol_file, nmol):
        '''
        set molecule files and number of molecules

        # ---------- args
        mol_file (list): list of path for molecular files (.xyz, etc)
                         one can also use pre-defined strings such as
                         H2O, CH4, benzene, ... etc.
                         see PyXtal document
 
        nmol (list): number of molecules

        # ---------- example
        # ------ 4 benzene molecules in unit cell
        mol_file = ['benzene']
        nmol = [4]
        # ------ molecules you make (2 * mol_1 and 2 * mol_2)
        mol_file = ['./mol_1.xyz', './mol_2.xyz']
        nmol = [2, 2]
        '''
        # ---------- check args
        # ------ mol_file
        if type(mol_file) is not list:
            raise ValueError('mol_file must be list')
        for s in mol_file:
            if type(s) is not str:
                raise ValueError('elements in mol_file must be string')
        # ------ nmol
        if type(nmol) is not list:
            raise ValueError('nmol must be list')
        for i in nmol:
            if type(i) is not int:
                raise ValueError('elements in nmol must be int')
        # ------ mol_file and nmol
        if not len(mol_file) == len(nmol):
            raise ValueError('not len(mol_file) == len(nmol)')
        # ------ self.xxx
        self.nmol = nmol
        self.mol_file = mol_file

    def gen_struc(self, nstruc, id_offset=0, init_pos_path=None):
        '''
        Generate random structures for given space groups

        # ---------- args
        nstruc (int): number of generated structures

        id_offset (int): default: 0
                         structure ID starts from id_offset
                         e.g. nstruc = 3, id_offset = 10
                              you obtain ID 10, ID 11, ID 12

        init_pos_path (str): default: None
                             specify a path of file
                             if you write POSCAR data of init_struc_data
                             ATTENSION: data are appended to the specified file

        # ---------- comment
        generated structure data are saved in self.init_struc_data
        '''
        # ---------- check args
        if not (type(nstruc) is int and nstruc > 0):
            raise ValueError('nstruc must be positive int')
        if type(id_offset) is not int:
            raise TypeError('id_offset must be int')
        if init_pos_path is None or type(init_pos_path) is str:
            pass
        else:
            raise ValueError('init_pos_path is wrong.'
                             ' init_pos_path = {}'.format(init_pos_path))
        # ---------- initialize
        self.init_struc_data = {}
        # ---------- loop for structure generattion
        while len(self.init_struc_data) < nstruc:
            # ------ spgnum --> spg
            if self.spgnum == 'all':
                spg = random.randint(1, 230)
            else:
                spg = random.choice(self.spgnum)
            if spg in self.spg_error:
                continue
            # ------ generate structure
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')    # for incompatible
                tmp_crystal = random_crystal(spg, self.atype, self.nat, self.vol_factor)
            if tmp_crystal.valid:
                tmp_struc = tmp_crystal.struct    # pymatgen Structure format
                # -- check nat
                if not self._check_nat(tmp_struc):
                    # pyxtal returns conventional cell, that is, too many atoms
                    tmp_struc = tmp_struc.get_primitive_structure()
                    # recheck nat
                    if not self._check_nat(tmp_struc):    # failure
                        raise ValueError('number of atoms is wrong')
                # -- sort, just in case
                tmp_struc = sort_by_atype(tmp_struc, self.atype)
                # -- check actual space group
                try:
                    spg_sym, spg_num = tmp_struc.get_space_group_info(
                        symprec=self.symprec)
                except TypeError:
                    spg_num = 0
                    spg_sym = None
                # -- register the structure in pymatgen format
                cid = len(self.init_struc_data) + id_offset
                self.init_struc_data[cid] = tmp_struc
                print('Structure ID {0:>6} was generated.'
                      ' Space group: {1:>3} --> {2:>3} {3}'.format(
                       cid, spg, spg_num, spg_sym))
                # -- save init_POSCARS
                if init_pos_path is not None:
                    out_poscar(tmp_struc, cid, init_pos_path)
            else:
                self.spg_error.append(spg)

    def gen_struc_mol(self, nstruc, id_offset=0, init_pos_path=None):
        '''
        Generate random molecular crystal structures for given space groups
        one have to run self.set_mol() in advance
        # ---------- args
        nstruc (int): number of generated structures

        id_offset (int): default: 0
                         structure ID starts from id_offset
                         e.g. nstruc = 3, id_offset = 10
                              you obtain ID 10, ID 11, ID 12

        init_pos_path (str): default: None
                             specify a path of file
                             if you write POSCAR data of init_struc_data
                             ATTENSION: data are appended to the specified file

        # ---------- comment
        generated structure data are saved in self.init_struc_data
        '''
        # ---------- check args
        if not (type(nstruc) is int and nstruc > 0):
            raise ValueError('nstruc must be positive int')
        if type(id_offset) is not int:
            raise TypeError('id_offset must be int')
        if init_pos_path is None or type(init_pos_path) is str:
            pass
        else:
            raise ValueError('init_pos_path is wrong.'
                             ' init_pos_path = {}'.format(init_pos_path))
        # ---------- initialize
        self.init_struc_data = {}
        # ---------- loop for structure generattion
        while len(self.init_struc_data) < nstruc:
            # ------ spgnum --> spg
            if self.spgnum == 'all':
                spg = random.randint(1, 230)
            else:
                spg = random.choice(self.spgnum)
            if spg in self.spg_error:
                continue
            # ------ generate structure
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')    # for incompatible
                tmp_crystal = molecular_crystal(spg, self.mol_file, self.nmol, self.vol_factor)
            if tmp_crystal.valid:
                tmp_struc = tmp_crystal.struct    # pymatgen Structure format
                # -- check nat
                if not self._check_nat(tmp_struc):
                    # pyxtal returns conventional cell, too many atoms if centering
                    tmp_struc = tmp_struc.get_primitive_structure()
                    # recheck nat
                    if not self._check_nat(tmp_struc):    # failure
                        raise ValueError('number of atoms is wrong')
                # -- sort, necessary in molecular crystal
                tmp_struc = sort_by_atype(tmp_struc, self.atype)
                # -- check actual space group
                try:
                    spg_sym, spg_num = tmp_struc.get_space_group_info(
                        symprec=self.symprec)
                except TypeError:
                    spg_num = 0
                    spg_sym = None
                # -- register the structure in pymatgen format
                cid = len(self.init_struc_data) + id_offset
                self.init_struc_data[cid] = tmp_struc
                print('Structure ID {0:>6} was generated.'
                      ' Space group: {1:>3} --> {2:>3} {3}'.format(
                       cid, spg, spg_num, spg_sym))
                # -- save init_POSCARS
                if init_pos_path is not None:
                    out_poscar(tmp_struc, cid, init_pos_path)
            else:
                self.spg_error.append(spg)

    def _check_nat(self, struc):
        # ---------- count number of atoms in each element for check
        species_list = [a.species_string for a in struc]
        for i in range(len(self.atype)):
            if species_list.count(self.atype[i]) != self.nat[i]:
                return False    # failure
        return True
