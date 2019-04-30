import warnings

import numpy as np
import scipy.sparse
import pytest

import matrix
import matrix.approximate
import matrix.constants
import matrix.tests.random
import matrix.util


# *** approximate *** #


def supported_permutation_methods(dense):
    methods = matrix.APPROXIMATION_ONLY_PERMUTATION_METHODS + matrix.UNIVERSAL_PERMUTATION_METHODS
    if not dense:
        methods += matrix.SPARSE_ONLY_PERMUTATION_METHODS
    return methods


test_overwrite_setups = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D,
     min_abs_value_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
    for min_abs_value_D in (None, 0.01, np.random.rand(1))
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D, min_abs_value_D'),
                         test_overwrite_setups)
def test_overwrite(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                   min_diag_D, max_diag_D, min_abs_value_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10
    if not dense:
        A = A.tocsc(copy=False)
    A_copy = A.copy()

    # check if A is not overwritten with in approximate decomposition
    overwrite_A = False
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', scipy.sparse.SparseEfficiencyWarning)
        decomposition = matrix.approximate.decomposition(
            A, permutation=permutation,
            min_diag_B=min_diag_B, max_diag_B=max_diag_B,
            min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
            overwrite_A=overwrite_A)

    assert matrix.util.is_equal(A, A_copy)

    # check if A is not overwritten with in approximate matrix
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', scipy.sparse.SparseEfficiencyWarning)
        B = matrix.approximate.positive_definite_matrix(
            A, permutation=permutation,
            min_diag_B=min_diag_B, max_diag_B=max_diag_B,
            min_diag_D=min_diag_D, max_diag_D=max_diag_D,
            overwrite_A=overwrite_A)

    assert matrix.util.is_equal(A, A_copy)


test_dense_equals_sparse_setups = [
    (n, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D, min_abs_value_D)
    for n in (10,)
    for complex_values in (True, False)
    for permutation in matrix.UNIVERSAL_PERMUTATION_METHODS + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
    for min_abs_value_D in (None, 0.01, np.random.rand(1))
]


@pytest.mark.parametrize(('n, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D, min_abs_value_D'),
                         test_dense_equals_sparse_setups)
def test_dense_equals_sparse(n, complex_values, permutation, min_diag_B, max_diag_B,
                             min_diag_D, max_diag_D, min_abs_value_D):

    # create random hermitian matrix
    A_sparse = matrix.tests.random.hermitian_matrix(n, dense=False, complex_values=complex_values) * 10
    A_sparse = A_sparse.tocsc(copy=False)
    A_dense = A_sparse.toarray()

    # approximate decompositions
    overwrite_A = False

    decomposition_sparse = matrix.approximate.decomposition(
        A_sparse, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        overwrite_A=overwrite_A)

    decomposition_dense = matrix.approximate.decomposition(
        A_dense, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        overwrite_A=overwrite_A)

    assert decomposition_sparse.is_almost_equal(decomposition_dense)


test_decomposition_equals_matrix_setups = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D,
     min_abs_value_D,)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
    for min_abs_value_D in (None, 0.01, np.random.rand(1))
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D, min_abs_value_D'),
                         test_decomposition_equals_matrix_setups)
def test_decomposition_equals_matrix(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                                     min_diag_D, max_diag_D, min_abs_value_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10
    if not dense:
        A = A.tocsc(copy=False)

    # create approximated decomposion
    overwrite_A = False
    decomposition = matrix.approximate.decomposition(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        overwrite_A=overwrite_A)

    # create approximated positive definite matrix
    try:
        min_diag_D = max(v for v in (min_diag_D, min_abs_value_D) if v is not None)
    except ValueError:
        pass
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # check if approximations are the same
    assert matrix.util.is_almost_equal(decomposition.composed_matrix, B)


test_value_checks_setups = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D,
     min_abs_value_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
    for min_abs_value_D in (None, 0.01, np.random.rand(1))
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D, min_abs_value_D'),
                         test_value_checks_setups)
def test_value_checks(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                      min_diag_D, max_diag_D, min_abs_value_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10
    if not dense:
        A = A.tocsc(copy=False)

    # create approximated decomposition
    overwrite_A = False
    decomposition = matrix.approximate.decomposition(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        overwrite_A=overwrite_A)

    # check values in decomposition
    d = decomposition.d
    assert np.all(np.isfinite(d))
    assert np.all(np.isreal(d))
    assert min_diag_D is None or np.all(d >= min_diag_D)
    assert max_diag_D is None or np.all(d <= max_diag_D)
    assert min_abs_value_D is None or np.all(np.logical_or(np.abs(d) >= min_abs_value_D, d == 0))

    L = decomposition.L
    if not dense:
        L = L.tocsr(copy=False).data
    assert np.all(np.isfinite(L))
    assert complex_values or np.all(np.isreal(L))

    # create approximated positive definite matrix
    try:
        min_diag_D = max(v for v in (min_diag_D, min_abs_value_D) if v is not None)
    except ValueError:
        pass
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # check values in approximation matrix
    if dense:
        B_data = B
    else:
        B_data = B.data
    assert np.all(np.isfinite(B_data))
    assert complex_values or np.all(np.isreal(B_data))
    B_diagonal = B.diagonal()
    assert np.all(np.isreal(B_diagonal))
    assert min_diag_B is None or np.all(B_diagonal >= min_diag_B)
    assert max_diag_B is None or np.all(B_diagonal <= max_diag_B)


test_invariance_setups = [
    (n, dense, complex_values, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
]


@pytest.mark.parametrize(('n, dense, complex_values, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D'),
                         test_invariance_setups)
def test_invariance(n, dense, complex_values, min_diag_B, max_diag_B, min_diag_D, max_diag_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10
    if not dense:
        A = A.tocsc(copy=False)

    # approximate matrix
    permutation = 'none'
    overwrite_A = False
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # approximate again matrix
    B_invariant = matrix.approximate.positive_definite_matrix(
        B, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)
    assert matrix.util.is_almost_equal(B, B_invariant, rtol=1e-04, atol=1e-06)


test_infinity_values_setups = [
    (n, dense, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (4,)
    for dense in (True, False)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
]


@pytest.mark.parametrize('n, dense, min_diag_B, max_diag_B, min_diag_D, max_diag_D',
                         test_infinity_values_setups)
def test_infinity_values(n, dense, min_diag_B, max_diag_B, min_diag_D, max_diag_D):

    # create matrix
    A = np.ones((n, n)) * np.finfo(np.float64).max
    for i in range(n):
        A[i, i] = 1
    if not dense:
        A = scipy.sparse.csc_matrix(A)

    # approximate matrix
    permutation = 'none'
    overwrite_A = False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        matrix.approximate.positive_definite_matrix(
            A, permutation=permutation,
            min_diag_B=min_diag_B, max_diag_B=max_diag_B,
            min_diag_D=min_diag_D, max_diag_D=max_diag_D,
            overwrite_A=overwrite_A)


def test_infinite_alpha_square():
    m = np.finfo(np.float64).max
    a = np.sqrt(m)
    A = np.array([[1, a / 10], [-a / 10, m / 100]])
    matrix.approximate.decomposition(A, permutation='none')


test_hermitian_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D'),
                         test_hermitian_setup)
def test_hermitian(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                   min_diag_D, max_diag_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # test hermitian
    for i in range(n):
        for j in range(i - 1):
            assert B[i, j] == np.conjugate(B[j, i])


test_positive_definitness_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D'),
                         test_positive_definitness_setup)
def test_positive_definitness(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                              min_diag_D, max_diag_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # test positive eigenvalues
    if scipy.sparse.issparse(B):
        min_eigenvalue = scipy.sparse.linalg.eigsh(B, k=1, which='SA', return_eigenvectors=False)
    else:
        eigenvalues = np.linalg.eigvalsh(B)
        min_eigenvalue = eigenvalues.min()

    assert min_eigenvalue > 0 or np.abs(min_eigenvalue) <= np.finfo(B.dtype).resolution * 10**2


test_stability_matrix_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n, np.random.rand(n))
    for max_diag_B in (1, np.arange(n) + 1, np.random.rand(n) + 1)
    for min_diag_D in (None, 1, np.random.rand(1))
    for max_diag_D in (None, 1, np.random.rand(1) + 1)
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D'),
                         test_stability_matrix_setup)
def test_stability_matrix(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                          min_diag_D, max_diag_D):
    assert max_diag_B is not None

    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    if scipy.sparse.issparse(B):
        B = B.tocsr(copy=False).data
    B_max_abs = np.abs(B).max()
    max_diag_B_max = np.asanyarray(max_diag_B).max()

    assert B_max_abs <= max_diag_B_max


test_stability_decomposition_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D,
     min_abs_value_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n, np.random.rand(n))
    for max_diag_B in (1, np.arange(n) + 1, np.random.rand(n) + 1)
    for min_diag_D in (None, 1, np.random.rand(1))
    for max_diag_D in (None, 1, np.random.rand(1) + 1)
    for min_abs_value_D in (0.01, np.random.rand(1))
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D, min_abs_value_D'),
                         test_stability_decomposition_setup)
def test_stability_decomposition(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                                 min_diag_D, max_diag_D, min_abs_value_D):
    assert max_diag_B is not None
    assert min_abs_value_D is not None

    # machine precision
    res = np.finfo(np.float64).resolution

    def less_or_equal(a, b):
        return a <= b or np.isclose(a, b, atol=res, rtol=res)

    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    decomposition = matrix.approximate.decomposition(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        overwrite_A=overwrite_A)

    # check d
    max_diag_B_max = np.asanyarray(max_diag_B).max()
    alpha = min(max_diag_B_max, max_diag_D) if max_diag_D is not None else max_diag_B_max
    assert less_or_equal(np.abs(decomposition.d).max(), alpha)

    # check L
    L = decomposition.L
    if scipy.sparse.issparse(L):
        L = L.tocsr(copy=False).data
    L_max_abs = np.abs(L).max()
    epsilon = max(min_diag_D, min_abs_value_D) if min_diag_D is not None else min_abs_value_D
    bound = (max_diag_B_max / epsilon)**0.5
    assert less_or_equal(L_max_abs, bound)

    # check omegas
    if min_diag_D is not None:
        if scipy.sparse.issparse(A):
            A_data = A.data
        else:
            A_data = A
        A_data = A_data[A_data != 0]
        A_data = np.abs(A_data)
        rho = A_data.min()
        bound = ((max_diag_B_max - min_diag_D) * alpha)**0.5 / rho
        bound = max(bound, 1)
        omega = decomposition.omega
        assert less_or_equal(np.abs(omega).max(), bound)

    # check delta
    if min_diag_B is not None:
        A_diag = A.diagonal()
        min_diag_B_min = np.asanyarray(min_diag_B).min()
        bound = max(max_diag_B_max - A_diag.min(), A_diag.max() - min_diag_B_min)
        delta = decomposition.delta
        assert less_or_equal(np.abs(delta).max(), bound)


test_condition_number_matrix_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n, np.random.rand(n))
    for max_diag_B in (1, np.arange(n) + 1, np.random.rand(n) + 1)
    for min_diag_D in (1, np.random.rand(1))
    for max_diag_D in (1, np.random.rand(1) + 1)
]


def _condition_number(B):
    if scipy.sparse.issparse(B):
        B = B.toarray()
    condition_number = np.linalg.cond(B, p=2)
    return condition_number


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D'),
                         test_condition_number_matrix_setup)
def test_condition_number_matrix(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                                 min_diag_D, max_diag_D):
    assert max_diag_B is not None
    assert min_diag_D is not None
    assert max_diag_D is not None

    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # check bound
    y = np.asanyarray(max_diag_B)
    bound = 4 * (y.mean(dtype=np.float128) / min_diag_D)**n * (min(y.max(), max_diag_D) / min_diag_D)
    condition_number = _condition_number(B)
    assert condition_number <= bound


test_condition_number_decomposition_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D,
     min_abs_value_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n, np.random.rand(n))
    for max_diag_B in (1, np.arange(n) + 1, np.random.rand(n) + 1)
    for min_diag_D in (1, np.random.rand(1))
    for max_diag_D in (1, np.random.rand(1) + 1)
    for min_abs_value_D in (0.01, np.random.rand(1))
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D, min_abs_value_D'),
                         test_condition_number_decomposition_setup)
def test_condition_number_decomposition(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                                        min_diag_D, max_diag_D, min_abs_value_D):
    assert max_diag_B is not None
    assert min_diag_D is not None
    assert max_diag_D is not None
    assert min_abs_value_D is not None

    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    decomposition = matrix.approximate.decomposition(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        overwrite_A=overwrite_A)

    # check bound for L
    y = np.asanyarray(max_diag_B)
    bound = 2 * (y.mean(dtype=np.float128) / min_diag_D)**(n / 2)
    condition_number = _condition_number(decomposition.L)
    assert condition_number <= bound
    # check bound for D
    bound = min(y.max(), max_diag_D) / min_diag_D
    condition_number = _condition_number(decomposition.D)
    assert condition_number <= bound or np.isclose(condition_number, bound)


test_delta_and_omega_setup = [
    (n, dense, complex_values, permutation, min_diag_B, max_diag_B, min_diag_D, max_diag_D)
    for n in (10,)
    for dense in (True, False)
    for complex_values in (True, False)
    for permutation in supported_permutation_methods(dense) + (matrix.tests.random.permutation_vector(n),)
    for min_diag_B in (None, 1, np.arange(n) / n)
    for max_diag_B in (None, 1, np.arange(n) + 1)
    for min_diag_D in (None, 1)
    for max_diag_D in (None, 1)
]


@pytest.mark.parametrize(('n, dense, complex_values, permutation, min_diag_B, max_diag_B,'
                          'min_diag_D, max_diag_D'),
                         test_delta_and_omega_setup)
def test_delta_and_omega(n, dense, complex_values, permutation, min_diag_B, max_diag_B,
                         min_diag_D, max_diag_D):
    # create random hermitian matrix
    A = matrix.tests.random.hermitian_matrix(n, dense=dense, complex_values=complex_values) * 10

    # approximate matrix
    overwrite_A = False
    B = matrix.approximate.positive_definite_matrix(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # get auxiliary variables
    L, d, p, omega, delta = matrix.approximate._decomposition(
        A, permutation=permutation,
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D,
        overwrite_A=overwrite_A)

    # test delta and omega
    for i in range(n):
        assert np.isclose(B[i, i], A[i, i] + delta[i])
        for j in range(i - 1):
            assert np.isclose(B[p[i], p[j]], A[p[i], p[j]] * omega[p[i]])
