from ipie.utils.backend import arraylib as xp
from ipie.utils.backend import synchronize


def greens_function_single_det(walker_batch, trial, build_full=False):
    """Compute walker's green's function.

    Parameters
    ----------
    walker_batch : object
        SingleDetWalkerBatch object.
    trial : object
        Trial wavefunction object.
    Returns
    -------
    det : float64 / complex128
        Determinant of overlap matrix.
    """
    ndown = walker_batch.ndown

    det = []
    for iw in range(walker_batch.nwalkers):
        ovlp = xp.dot(walker_batch.phia[iw].T, trial.psi0a.conj())
        ovlp_inv = xp.linalg.inv(ovlp)
        walker_batch.Ghalfa[iw] = xp.dot(ovlp_inv, walker_batch.phia[iw].T)
        if not trial.half_rotated or build_full:
            walker_batch.Ga[iw] = xp.dot(trial.psi0a.conj(), walker_batch.Ghalfa[iw])
        sign_a, log_ovlp_a = xp.linalg.slogdet(ovlp)
        sign_b, log_ovlp_b = 1.0, 0.0
        if ndown > 0 and not walker_batch.rhf:
            ovlp = xp.dot(walker_batch.phib[iw].T, trial.psi0b.conj())
            sign_b, log_ovlp_b = xp.linalg.slogdet(ovlp)
            walker_batch.Ghalfb[iw] = xp.dot(xp.linalg.inv(ovlp), walker_batch.phib[iw].T)
            if not trial.half_rotated or build_full:
                walker_batch.Gb[iw] = xp.dot(trial.psi0b.conj(), walker_batch.Ghalfb[iw])
            det += [sign_a * sign_b * xp.exp(log_ovlp_a + log_ovlp_b - walker_batch.log_shift[iw])]
        elif ndown > 0 and walker_batch.rhf:
            det += [sign_a * sign_a * xp.exp(log_ovlp_a + log_ovlp_a - walker_batch.log_shift[iw])]
        elif ndown == 0:
            det += [sign_a * xp.exp(log_ovlp_a - walker_batch.log_shift)]

    det = xp.array(det, dtype=xp.complex128)

    synchronize()

    return det


def greens_function_single_det_batch(walker_batch, trial, build_full=False):
    """Compute walker's green's function using only batched operations.

    Parameters
    ----------
    walker_batch : object
        SingleDetWalkerBatch object.
    trial : object
        Trial wavefunction object.
    Returns
    -------
    ot : float64 / complex128
        Overlap with trial.
    """
    ndown = walker_batch.ndown

    ovlp_a = xp.einsum("wmi,mj->wij", walker_batch.phia, trial.psi0a.conj(), optimize=True)
    ovlp_inv_a = xp.linalg.inv(ovlp_a)
    sign_a, log_ovlp_a = xp.linalg.slogdet(ovlp_a)

    walker_batch.Ghalfa = xp.einsum("wij,wmj->wim", ovlp_inv_a, walker_batch.phia, optimize=True)
    if not trial.half_rotated or build_full:
        walker_batch.Ga = xp.einsum(
            "mi,win->wmn", trial.psi0a.conj(), walker_batch.Ghalfa, optimize=True
        )

    if ndown > 0 and not walker_batch.rhf:
        ovlp_b = xp.einsum("wmi,mj->wij", walker_batch.phib, trial.psi0b.conj(), optimize=True)
        ovlp_inv_b = xp.linalg.inv(ovlp_b)

        sign_b, log_ovlp_b = xp.linalg.slogdet(ovlp_b)
        walker_batch.Ghalfb = xp.einsum(
            "wij,wmj->wim", ovlp_inv_b, walker_batch.phib, optimize=True
        )
        if not trial.half_rotated or build_full:
            walker_batch.Gb = xp.einsum(
                "mi,win->wmn", trial.psi0b.conj(), walker_batch.Ghalfb, optimize=True
            )
        ot = sign_a * sign_b * xp.exp(log_ovlp_a + log_ovlp_b - walker_batch.log_shift)
    elif ndown > 0 and walker_batch.rhf:
        ot = sign_a * sign_a * xp.exp(log_ovlp_a + log_ovlp_a - walker_batch.log_shift)
    elif ndown == 0:
        ot = sign_a * xp.exp(log_ovlp_a - walker_batch.log_shift)

    synchronize()

    return ot
