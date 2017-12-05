# coding: utf-8

__all__ = [
    'RADEX',
]

# standard library
import os
import re
from collections import OrderedDict
from copy import deepcopy
from urllib.request import urlopen
from itertools import product
from pathlib import Path
from subprocess import run, PIPE

# dependent packages
import wradex
import yaml
import numpy as np
from astropy import units as u

# yaml is loaded as an ordered dict
yaml.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda loader, node: OrderedDict(loader.construct_pairs(node))
)

# local constants
with wradex.WRADEX_CONFIG.open() as f:
    config = yaml.load(f)

RADEX_PATH    = config['radex_path']
RADEX_PARAMS  = config['radex_params']
RADEX_INPUT   = config['radex_input']
RADEX_OUTPUT  = config['radex_output']
RADEX_LOG     = config['radex_log']
RADEX_IN_UNI  = config['radex_input_units']
RADEX_OUT_UNI = config['radex_output_units']
MOLDATA_DIR   = config['moldata_dir']
MOLDATA_URL   = config['moldata_url']
MOLDATA_LIST  = config['moldata_list']

RADEX_PATH    = str(Path(RADEX_PATH).expanduser())
RADEX_OUTPUT  = str(Path(RADEX_OUTPUT).expanduser())
RADEX_LOG     = str(Path(RADEX_LOG).expanduser())
MOLDATA_DIR   = str(Path(MOLDATA_DIR).expanduser())
for key, val in RADEX_PARAMS.items():
    num, unit = val.split()
    RADEX_PARAMS.update({key: float(num)*u.Unit(unit)})

# classes
class RADEX(object):
    available = list(MOLDATA_LIST.keys())

    def __init__(self, molname):
        """Create a RADEX calculator.

        Args:
            molname (str): A molecular name decscibed in config.yaml.
                If the corresponding data is not found in the moldat directory,
                this program will try to download it from LAMDA database.

        Examples:
            >>> import wradex
            >>> calc = wradex.RADEX('CO')

        """
        self.params = {
            'molname': molname,
            'moldata': MOLDATA_LIST[molname],
            'radex_input': deepcopy(RADEX_INPUT),
            'default_params': deepcopy(RADEX_PARAMS),
        }

        # download a moldat (*.dat) if it is not found
        path = Path(MOLDATA_DIR, self.moldata).expanduser()
        url  = '{}/{}'.format(MOLDATA_URL, self.moldata)

        if not path.exists():
            print('{} is not in the RADEX moldata direcrory'.format(self.moldata))
            print('--> downloading {} from the LAMDA website'.format(self.moldata))
            with urlopen(url) as data, path.open('w') as f:
                f.write(data.read().decode('utf-8'))

        # read a moldat and extract information
        with path.open() as f:
            self._energy_levels = self._get_energy_levels(f)
            self._transitions   = self._get_transitions(f)

        self.transitions = list(self._transitions.keys())

    def __call__(self, transition, **kwargs):
        """Execute RADEX and return the values.

        Args:
            transition (str): A transition described in transitions.
                Available transitions are listed in `self.transitions`.
            kwargs (int or float with units): Spacify if you change the default
                parameters which is stored in `self.default_params`.

        Returns:
            params (dict): Parameters used for Calculation.
            outputs (dict): Values Calculated by RADEX.

        Examples:
            Calculate values of CO(3-2) at T_kin=100K with other parameters as default::
                >>> import radex
                >>> from astropy import units as u
                >>> calc = radex.RADEX('CO')
                >>> params, output = calc('3-2', T_kin=100*u.K)

            Calculate grid values of CO(3-2) at T_kin=[100,200,300] K,
            n_H2=[1e3,1e4,1e5] cm^-3, and other parameters as default::
                >>> T_kin = [100, 200, 300] * u.K
                >>> n_H2  = [1e3, 1e4, 1e5] / u.cm**3
                >>> params, output = calc('3-2', T_kin=Tkin, n_H2=n_H2)

        """
        f_rest = self._transitions[transition]['f_rest']

        # override parameters if spacified
        params = deepcopy(self.default_params)
        params.update(kwargs)
        params.update({
            'moldata': self.moldata,
            'output': RADEX_OUTPUT,
            'f_min': f_rest-0.001*u.GHz,
            'f_max': f_rest+0.001*u.GHz,
        })

        # make gridded parameters
        grids = np.meshgrid(*[params.pop(key) for key in RADEX_PARAMS], indexing='ij')
        gparams = {}
        for i, key in enumerate(RADEX_PARAMS):
            unit = RADEX_IN_UNI[key]
            grid = grids[i].to(u.Unit(unit))
            gparams.update({key: grid})

        # execute RADEX
        gshape = grids[0].shape
        outputs = {key: np.zeros(gshape) for key in RADEX_OUT_UNI}
        for idx in product(*map(range, gshape)):
            eachgparams = {key: val[idx] for key, val in gparams.items()}
            output = self._calc_radex({**params, **eachgparams})
            for key in RADEX_OUT_UNI:
                outputs[key][idx] = output[key]

        # remove RADEX output and log
        os.remove(RADEX_OUTPUT)
        os.remove(RADEX_LOG)

        # remove redundancies of the params
        params = {**params, **gparams}
        for key in RADEX_PARAMS:
            if len(np.unique(params[key])) == 1:
                params.update({key: np.unique(params[key])[0]})
            else:
                params.update({key: np.squeeze(params[key])})

        # add units to the outputs
        for key, val in outputs.items():
            unit = RADEX_OUT_UNI[key]
            outputs.update({key: np.squeeze(val)*u.Unit(unit)})

        return params, outputs

    def _get_energy_levels(self, f):
        kwd = ''
        pat = re.compile('energy levels', re.IGNORECASE)
        while not pat.search(kwd):
            kwd = f.readline()

        n_levels = int(f.readline())
        f.readline()

        energy_levels = {}
        for i in range(n_levels):
            elems  = f.readline().split()
            energy = float(elems[1]) / u.cm
            weight = float(elems[2]) / u.dimensionless_unscaled
            level  = elems[3]

            energy_levels[i+1] = {'energy': energy, 'weight': weight, 'level': level}

        return energy_levels

    def _get_transitions(self, f):
        kwd = ''
        pat = re.compile('radiative transitions', re.IGNORECASE)
        while not pat.search(kwd):
            kwd = f.readline()

        n_transitions = int(f.readline())
        f.readline()

        transitions = {}
        for i in range(n_transitions):
            elems  = f.readline().split()
            upper  = self._energy_levels[int(elems[1])]['level']
            lower  = self._energy_levels[int(elems[2])]['level']
            A_ul   = float(elems[3]) / u.s
            f_rest = float(elems[4]) * u.GHz
            E_u    = float(elems[5]) * u.K

            key = '{}-{}'.format(upper, lower)
            transitions[key] = {'A_ul': A_ul, 'f_rest': f_rest, 'E_u': E_u}

        return transitions

    def _calc_radex(self, params):
        self._remove_units(params)
        inp = self.radex_input.format(**params).encode('utf-8')
        cp = run(RADEX_PATH, input=inp, stdout=PIPE, stderr=PIPE)

        with open(RADEX_OUTPUT) as f:
            kwd = ''
            pat = re.compile('calculation finished', re.IGNORECASE)
            while not pat.search(kwd):
                kwd = f.readline()

            f.readline()
            f.readline()
            elems = f.readline().split()

            output = {}
            for i, key in enumerate(RADEX_OUT_UNI):
                try:
                    output[key] = float(elems[i+3])
                except:
                    output[key] = np.nan

        return output

    def _remove_units(self, params):
        for key, val in params.items():
            try:
                params[key] = val.value
            except AttributeError:
                pass

    def __getattr__(self, name):
        return self.params[name]

    def __repr__(self):
        return 'RADEX({})'.format(self.molname)
