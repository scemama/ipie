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
# Authors: Joonho Lee
#          Fionn Malone <fionn.malone@gmail.com>
#

import os

import numpy
import pytest
from mpi4py import MPI

from ipie.utils.testing import build_driver_test_instance
from ipie.utils.legacy_testing import build_legacy_driver_instance
from ipie.analysis.extraction import extract_observable, extract_mixed_estimates

steps = 25
blocks = 5
seed = 7
nwalkers = 25
nmo = 3
nelec = (2, 1)
pop_control_freq = 1
ndets = 5
stabilise_freq = 10
options = {
    "dt": 0.005,
    "nstblz": 5,
    "nwalkers": nwalkers,
    "nwalkers_per_task": nwalkers,
    "batched": True,
    "hybrid": True,
    "steps": steps,
    "blocks": blocks,
    "pop_control_freq": pop_control_freq,
    "stabilise_freq": stabilise_freq,
    "rng_seed": seed,
}
driver_options = {
    "verbosity": 0,
    "get_sha1": False,
    "qmc": options,
    "estimates": {
        "filename": "estimates.test_generic_multi_det_batch.h5",
        "observables": {
            "energy": {},
        },
    },
    "walkers": {"population_control": "pair_branch"},
}


@pytest.mark.driver
def test_generic_multi_det_batch():
    comm = MPI.COMM_WORLD
    afqmc = build_driver_test_instance(
        nelec,
        nmo,
        trial_type="phmsd",
        wfn_type="naive",
        options=driver_options,
        seed=7,
        num_dets=ndets,
    )
    afqmc.run(comm=comm, verbose=1)
    afqmc.finalise(verbose=0)
    afqmc.estimators.compute_estimators(
        comm,
        afqmc.system,
        afqmc.hamiltonian,
        afqmc.trial,
        afqmc.walkers,
    )
    numer_batch = afqmc.estimators["energy"]["ENumer"]
    denom_batch = afqmc.estimators["energy"]["EDenom"]

    data_batch = extract_observable("estimates.test_generic_multi_det_batch.h5", "energy")

    numpy.random.seed(seed)
    driver_options["estimates"] = {
        "filename": "estimates.test_generic_multi_det_batch.h5",
        "mixed": {"energy_eval_freq": options["steps"]},
    }
    driver_options["qmc"]["batched"] = False
    legacy_afqmc = build_legacy_driver_instance(
        nelec,
        nmo,
        trial_type="phmsd",
        options=driver_options,
        seed=7,
        num_dets=ndets,
    )
    legacy_afqmc.estimators.estimators["mixed"].print_header()
    legacy_afqmc.run(comm=comm, verbose=1)
    legacy_afqmc.finalise(verbose=0)
    legacy_afqmc.estimators.estimators["mixed"].update(
        legacy_afqmc.qmc,
        legacy_afqmc.system,
        legacy_afqmc.hamiltonian,
        legacy_afqmc.trial,
        legacy_afqmc.psi,
        0,
    )
    enum = legacy_afqmc.estimators.estimators["mixed"].names
    numer = legacy_afqmc.estimators.estimators["mixed"].estimates[enum.enumer]
    denom = legacy_afqmc.estimators.estimators["mixed"].estimates[enum.edenom]
    weight = legacy_afqmc.estimators.estimators["mixed"].estimates[enum.weight]

    # assert numer.real == pytest.approx(numer_batch.real)
    assert denom.real == pytest.approx(denom_batch.real)
    # assert weight.real == pytest.approx(weight_batch.real)
    assert numer.imag == pytest.approx(numer_batch.imag)
    assert denom.imag == pytest.approx(denom_batch.imag)
    data = extract_mixed_estimates("estimates.test_generic_multi_det_batch.h5")

    assert numpy.mean(data_batch.WeightFactor.values[:-1].real) == pytest.approx(
        numpy.mean(data.WeightFactor.values[:-1].real)
    )
    assert numpy.mean(data_batch.Weight.values[:-1].real) == pytest.approx(
        numpy.mean(data.Weight.values[:-1].real)
    )
    assert numpy.mean(data_batch.ENumer.values[:-1].real) == pytest.approx(
        numpy.mean(data.ENumer.values[:-1].real)
    )
    assert numpy.mean(data_batch.EDenom.values[:-1].real) == pytest.approx(
        numpy.mean(data.EDenom.values[:-1].real)
    )
    assert numpy.mean(data_batch.ETotal.values[:-1].real) == pytest.approx(
        numpy.mean(data.ETotal.values[:-1].real)
    )
    assert numpy.mean(data_batch.E1Body.values[:-1].real) == pytest.approx(
        numpy.mean(data.E1Body.values[:-1].real)
    )
    assert numpy.mean(data_batch.E2Body.values[:-1].real) == pytest.approx(
        numpy.mean(data.E2Body.values[:-1].real)
    )
    assert numpy.mean(data_batch.HybridEnergy.values[:-1].real) == pytest.approx(
        numpy.mean(data.EHybrid.values[:-1].real)
    )
    # assert numpy.mean(data_batch.Overlap.values[:-1].real) == pytest.approx(
    # numpy.mean(data.Overlap.values[:-1].real)
    # )


def teardown_module():
    cwd = os.getcwd()
    files = ["estimates.test_generic_multi_det_batch.h5"]
    for f in files:
        try:
            os.remove(cwd + "/" + f)
        except OSError:
            pass


if __name__ == "__main__":
    test_generic_multi_det_batch()
