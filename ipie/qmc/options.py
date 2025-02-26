# Copyright 2022 The ipie Developers. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: Fionn Malone <fmalone@google.com>
#          Joonho Lee
#

from ipie.utils.io import get_input_value


def convert_from_reduced_unit(system, qmc_opts, verbose=False):
    if system.name == "UEG":
        TF = system.ef  # Fermi temeprature
        if verbose:
            print("# Fermi Temperature: {:13.8e}".format(TF))
            print("# beta in reduced unit: {:13.8e}".format(qmc_opts["beta"]))
            print("# dt in reduced unit: {:13.8e}".format(qmc_opts["dt"]))
        dt = qmc_opts["dt"]  # original dt
        beta = qmc_opts["beta"]  # original dt
        scaled_dt = dt / TF  # converting to Hartree ^ -1
        scaled_beta = beta / TF  # converting to Hartree ^ -1
        if verbose:
            print("# beta in Hartree^-1:  {:13.8e}".format(scaled_beta))
            print("# dt in Hartree^-1: {:13.8e}".format(scaled_dt))
        return scaled_dt, scaled_beta


class QMCOpts(object):
    r"""Input options and certain constants / parameters derived from them.

    Initialised from a dict containing the following options, not all of which
    are required.

    Parameters
    ----------
    method : string
        Which auxiliary field method are we using? Currently only CPMC is
        implemented.
    nwalkers : int
        Number of walkers to propagate in a simulation.
    dt : float
        Timestep.
    nsteps : int
        Number of steps per block.
    nmeasure : int
        Frequency of energy measurements.
    nstblz : int
        Frequency of Gram-Schmidt orthogonalisation steps.
    npop_control : int
        Frequency of population control.
    temp : float
        Temperature. Currently not used.
    nequilibrate : int
        Number of steps used for equilibration phase. Only used to fix local
        energy bound when using phaseless approximation.
    importance_sampling : boolean
        Are we using importance sampling. Default True.
    hubbard_statonovich : string
        Which hubbard stratonovich transformation are we using. Currently the
        options are:

        - discrete : Use the discrete Hirsch spin transformation.
        - opt_continuous : Use the continuous transformation for the Hubbard
          model.
        - generic : Use the generic transformation. To be used with Generic
          system class.

    ffts : boolean
        Use FFTS to diagonalise the kinetic energy propagator? Default False.
        This may speed things up for larger lattices.

    Attributes
    ----------
    cplx : boolean
        Do we require complex wavefunctions?
    mf_shift : float
        Mean field shift for continuous Hubbard-Stratonovich transformation.
    iut_fac : complex float
        Stores i*(U*dt)**0.5 for continuous Hubbard-Stratonovich transformation.
    ut_fac : float
        Stores (U*dt) for continuous Hubbard-Stratonovich transformation.
    mf_nsq : float
        Stores M * mf_shift for continuous Hubbard-Stratonovich transformation.
    local_energy_bound : float
        Energy pound for continuous Hubbard-Stratonovich transformation.
    mean_local_energy : float
        Estimate for mean energy for continuous Hubbard-Stratonovich transformation.
    """

    # pylint: disable=dangerous-default-value
    # TODO: Remove this class / replace with dataclass
    def __init__(self, inputs={}, verbose=False):
        self.nwalkers = get_input_value(
            inputs, "num_walkers", default=None, alias=["nwalkers"], verbose=verbose
        )
        self.nwalkers_per_task = get_input_value(
            inputs,
            "num_walkers",
            default=None,
            alias=["nwalkers_per_task"],
            verbose=verbose,
        )
        if self.nwalkers_per_task is not None:
            self.nwalkers = None
        self.dt = get_input_value(inputs, "timestep", default=0.005, alias=["dt"], verbose=verbose)
        self.batched = get_input_value(inputs, "batched", default=True, verbose=verbose)
        self.nsteps = get_input_value(
            inputs, "num_steps", default=25, alias=["nsteps", "steps"], verbose=verbose
        )
        self.nblocks = get_input_value(
            inputs,
            "blocks",
            default=1000,
            alias=["num_blocks", "nblocks"],
            verbose=verbose,
        )
        self.nstblz = get_input_value(
            inputs,
            "stabilise_freq",
            default=5,
            alias=["nstabilise", "reortho"],
            verbose=verbose,
        )
        self.npop_control = get_input_value(
            inputs,
            "pop_control_freq",
            default=5,
            alias=["npop_control", "pop_control"],
            verbose=verbose,
        )
        self.eqlb_time = get_input_value(
            inputs,
            "equilibration_time",
            default=2.0,
            alias=["tau_eqlb"],
            verbose=verbose,
        )
        self.neqlb = int(self.eqlb_time / self.dt)
        self.rng_seed = get_input_value(
            inputs,
            "rng_seed",
            default=None,
            alias=["random_seed", "seed"],
            verbose=verbose,
        )

    def __str__(self, verbose=0):
        _str = ""
        for k, v in self.__dict__.items():
            _str += f"# {k:<25s} : {v}\n"
        return _str
