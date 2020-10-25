'''
Random structure generation using PyXtal
    https://github.com/qzhu2017/PyXtal
'''

from contextlib import redirect_stdout
from multiprocessing import Process, Queue
import os
import random
import sys

from pyxtal.crystal import random_crystal
from pyxtal.molecular_crystal import molecular_crystal

from ..struc_util import check_distance
from ..struc_util import sort_by_atype
from ..struc_util import out_poscar
from ..struc_util import scale_cell_mol


class Rnd_struc_gen_pyxtal:
    '''
    Random structure generation using pyxtal

    # ---------- args
    natot (int): number of atoms, e.g. 12 for Si4O8

    atype (list): atom type, e.g. ['Si', 'O'] for Si4O8

    nat (list): number of atom, e.g. [4, 8] for Si4O8

    vol_factor (list): default --> [1.0, 1.0]
                       [min, max] int or float

    vol_mu (int or float or None): default --> None
                                   average volume in Gaussian distribution
                                   when you scale cell volume

    vol_sigma (int or float or None): default --> None
                                      standard deviation in Gaussian distribution
                                      when you scale cell volume

    mindist (2d list): default --> None
                       constraint on minimum interatomic distance,
                       mindist must be a symmetric matrix
        e.g. [[1.8, 1.2], [1.2, 1.5]]
            Si - Si: 1.8 angstrom
            Si -  O: 1.2
             O -  O: 1.5

    spgnum ('all' or list): space group numbers which you use
                            'all' --> 1--230
                            list --> e.g. [1, 3, 100 ..., 229, 230]

    symprec (float): default --> 0.01
                     tolerance for symmetry finding
    '''

    def __init__(self, natot, atype, nat, vol_factor=[1.0, 1.0],
                 vol_mu=None, vol_sigma=None,
                 mindist=None, spgnum='all', symprec=0.01):
        # ---------- check args
        # ------ int
        for i in [natot]:
            if type(i) is int and i > 0:
                pass
            else:
                raise ValueError('natot must be positive int')
        # ------ list
        for x in [atype, nat, vol_factor]:
            if type(x) is not list:
                raise ValueError('atype, nat, and vol_factor must be list')
        if not len(atype) == len(nat):
            raise ValueError('not len(atype) == len(nat)')
        # ------ vol_factor
        if len(vol_factor) == 2:
            if not 0 < vol_factor[0] <= vol_factor[1]:
                raise ValueError('0 < vol_factor[0] <= vol_factor[1]')
        else:
            raise ValueError('length of vol_factor must be 2')
        # ------ vol_mu, vol_sigma
        if vol_mu is not None:
            for x in [vol_mu, vol_sigma]:
                if type(x) is not float and type(x) is not int:
                    raise ValueError('vol_mu and vol_sigma must be int or float')
            if vol_mu <= 0:
                raise ValueError('vol_mu must be positive')
        # ------ mindist
        if mindist is not None:
            if not len(atype) == len(mindist):
                raise ValueError('not len(atype) == len(mindist)')
            # -- check symmetric
            for i in range(len(mindist)):
                for j in range(i):
                    if not mindist[i][j] == mindist[j][i]:
                        raise ValueError('mindist is not symmetric. '
                                         '({}, {}): {}, ({}, {}): {}'.format(
                                             i, j, mindist[i][j],
                                             j, i, mindist[j][i]))

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
        self.vol_mu = vol_mu
        self.vol_sigma = vol_sigma
        self.mindist = mindist
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
            # ------ vol_factor
            rand_vol = random.uniform(self.vol_factor[0], self.vol_factor[1])
            # ------ generate structure
            tmp_crystal = random_crystal(spg, self.atype,
                                         self.nat, rand_vol)
            if tmp_crystal.valid:
                #tmp_struc = tmp_crystal.struct    # pymatgen Structure format, old pyxtal
                tmp_struc = tmp_crystal.to_pymatgen()    # pymatgen Structure format
                # -- check nat
                if not self._check_nat(tmp_struc):
                    # pyxtal returns conventional cell, that is, too many atoms
                    tmp_struc = tmp_struc.get_primitive_structure()
                    # recheck nat
                    if not self._check_nat(tmp_struc):    # failure
                        continue
                # -- sort, just in case
                tmp_struc = sort_by_atype(tmp_struc, self.atype)
                # -- scale volume
                if self.vol_mu is not None:
                    vol = random.gauss(mu=self.vol_mu, sigma=self.vol_sigma)
                    tmp_struc.scale_lattice(volume=vol)
                # -- check minimum distance
                if self.mindist is not None:
                    if not check_distance(tmp_struc, self.atype, self.mindist):
                        continue    # failure
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

    def gen_struc_mol(self, nstruc, id_offset=0, init_pos_path=None,
                      timeout_mol=180):
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

        timeout_mol (int or float): timeout for one molecular structure generation

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
        if type(timeout_mol) is not float and type(timeout_mol) is not int:
            raise ValueError('timeout_mol must be int or float')
        if timeout_mol <= 0:
            raise ValueError('timeout_mol must be positive')
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
            rand_vol = random.uniform(self.vol_factor[0], self.vol_factor[1])
            # ------ generate structure
            # -- multiprocess for measures against hangup
            q = Queue()
            p = Process(target=self._mp_mc, args=(spg, rand_vol, q))
            p.start()
            p.join(timeout=timeout_mol)
            if p.is_alive():
                p.terminate()
                p.join()
            if sys.version_info.minor >= 7:
                # Process.close() available from python 3.7
                p.close()
            if q.empty():
                print('timeout for molecular structure generation. retry.')
                continue
            else:
                tmp_struc = q.get()
                tmp_valid = q.get()
                if tmp_struc == 'error':
                    raise NameError('could not load  mol_file')
            if tmp_valid:
                # -- scale volume
                if self.vol_mu is not None:
                    vol = random.gauss(mu=self.vol_mu, sigma=self.vol_sigma)
                    vol = vol * tmp_struc.num_sites / self.natot    # for conv. cell
                    tmp_struc = scale_cell_mol(tmp_struc, self.mol_file, vol)
                # -- check nat
                if not self._check_nat(tmp_struc):
                    # pyxtal returns conventional cell,
                    # too many atoms if centering
                    tmp_struc = tmp_struc.get_primitive_structure()
                    # recheck nat
                    if not self._check_nat(tmp_struc):    # failure
                        continue
                # -- sort, necessary in molecular crystal
                tmp_struc = sort_by_atype(tmp_struc, self.atype)
                # -- check minimum distance
                if self.mindist is not None:
                    if not check_distance(tmp_struc, self.atype, self.mindist):
                        continue
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

    def _mp_mc(self, spg, rand_vol, q):
        '''multiprocess part'''
        try:
            # ---------- temporarily stdout --> devnull
            with redirect_stdout(open(os.devnull, 'w')):
                tmp_crystal = molecular_crystal(spg, self.mol_file,
                                                self.nmol, rand_vol)
                # ---------- queue
                #q.put(tmp_crystal.struct)    # old pyxtal
            if tmp_crystal.valid:
                q.put(tmp_crystal.to_pymatgen())
                q.put(tmp_crystal.valid)
            else:
                q.put(None)
                q.put(tmp_crystal.valid)
        except (NameError):
            # ------ no molecule file
            q.put('error')
            q.put(None)