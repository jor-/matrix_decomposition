import numpy as np
import scipy.sparse

import matrix
import matrix.constants
import matrix.decompositions
import matrix.errors
import matrix.permute
import matrix.sparse.util


def _decomposition(
        A, min_diag_B=None, max_diag_B=None, min_diag_D=None, max_diag_D=None,
        min_abs_value_D=None, permutation_method=None, overwrite_A=False,
        strict_lower_triangular_only_L=False):
    """
    Computes an (approximative) `LDL` decomposition of a matrix with the specified properties.

    Returns a `LDL` decomposition of `A` if such a decomposition exists.
    Otherwise a `LDL` decomposition of an approximation of `A` is retuned.

    Parameters
    ----------
    A : numpy.ndarray or scipy.sparse.spmatrix
        The matrix that should be approximated by a decomposition.
        It is assumed, that A is Hermitian. The matrix must be a squared matrix.
    min_diag_B : numpy.ndarray or float
        Each component of the diagonal of the composed matrix `B` of an approximated
        `LDL` decomposition is forced to be greater or equal to `min_diag_B`.
        optional, default : No minimal value is forced.
    max_diag_B : numpy.ndarray or float
        Each component of the diagonal of the composed matrix `B` of an approximated
        `LDL` decomposition is forced to be lower or equal to `max_diag_B`.
        optional, default : No maximal value is forced.
    min_diag_D : float
        Each component of the diagonal of the matrix `D` in an approximated
        `LDL` decomposition is forced to be greater or equal to `min_diag_D`.
        `min_diag_D` must be greater or equal to 0.
        optional, default : 0
    max_diag_D : float
        Each component of the diagonal of the matrix `D` in an approximated
        `LDL` decomposition is forced to be lower or equal to `max_diag_D`.
        optional, default : No maximal value is forced.
    min_abs_value_D : float
        Absolute values below `min_abs_value_D` are considered as zero
        in the matrix `D` of an approximated `LDL` decomposition.
        optional, default : The square root of the resolution of the underlying data type.
    permutation_method : str
        The symmetric permutation method that is applied to the matrix before it is decomposed.
        It has to be a value in :const:`matrix.APPROXIMATION_PERMUTATION_METHODS`.
        If `A` is sparse, it can also be a value in
        :const:`matrix.SPARSE_ONLY_PERMUTATION_METHODS`.
        optional, default: The permutation is chosen by the algorithm.
    overwrite_A : bool
        Whether it is allowed to overwrite A. Enabling may result in performance gain.
        optional, default: False
    strict_lower_triangular_only_L : bool
        Whether only the strict lower triangular matrix of the matrix `L` in the
        `LDL` decomposition should be computed. If this is true, its upper triangular matrix
        may contain arbitrary values. Enabling may result in performance gain.
        optional, default : False

    Returns
    -------
    L : numpy.ndarray or scipy.sparse.spmatrix (same type as A)
        Matrix `L` of `LDL` decomposition.
    d : numpy.ndarray
        Diagonal of matrix `D` of `LDL` decomposition.
    p : numpy.ndarray
        Permutation vector.
    omega : numpy.ndarray
        Auxiliary vector for calculating B.
    delta : numpy.ndarray
        Auxiliary vector for calculating B.

    Raises
    ------
    matrix.errors.MatrixNotSquareError
        If `A` is not a square matrix.
    matrix.errors.MatrixComplexDiagonalValueError
        If `A` has complex diagonal values.
    """

    # debug info
    matrix.logger.debug(('Calculating approximated LDL decomposition with passed values: '
                         'min_diag_B={min_diag_B}, max_diag_B={max_diag_B}, '
                         'min_diag_D={min_diag_D}, max_diag_D={max_diag_D}, '
                         'min_abs_value_D={min_abs_value_D}, '
                         'permutation_method={permutation_method}, overwrite_A={overwrite_A}, '
                         'strict_lower_triangular_only_L={strict_lower_triangular_only_L}.'
                         ).format(
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A,
        strict_lower_triangular_only_L=strict_lower_triangular_only_L))

    # check A
    is_dense = not matrix.sparse.util.is_sparse(A)
    if is_dense:
        A = np.asarray(A)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise matrix.errors.MatrixNotSquareError(A)
    n = A.shape[0]

    # calculate gamma
    gamma = A.diagonal()
    if np.issubdtype(A.dtype, np.complexfloating):
        if not np.all(np.isreal(gamma)):
            index_with_complex_value = np.where(~np.isreal(gamma))[0][0]
            raise matrix.errors.MatrixComplexDiagonalValueError(A, i=index_with_complex_value)
        gamma = gamma.real

    # check diag values
    def check_float_scalar_or_vector(f, f_name='variable', default_value=None,
                                     minus_inf_okay=False, plus_inf_okay=False):
        if f is not None:
            try:
                f = np.asarray(f)
            except TypeError as original_error:
                error = ValueError(('{} must a scalar value or a vector but it is {}.'
                                    ).format(f_name, f))
                matrix.logger.error(error)
                raise error from original_error
            if not (f.ndim == 0 or (f.ndim == 1 and f.shape[0] == n)):
                error = ValueError(('{} must be a scalar or a vector with the same dimension as A '
                                    'but its shape is {}.').format(f_name, f.shape))
                matrix.logger.error(error)
                raise error
            if not (np.all(np.isreal(f))):
                error = ValueError(('{} must be real valued but it is {}.').format(f_name, f))
                matrix.logger.error(error)
                raise error
            if not np.all(np.logical_or(np.isfinite(f),
                                        np.logical_or(np.logical_and(plus_inf_okay,
                                                                     f == np.inf),
                                                      np.logical_and(minus_inf_okay,
                                                                     f == -np.inf)))):
                error = ValueError('{} must be finite'.format(f_name) +
                                   (' or minus infinity' if minus_inf_okay else '') +
                                   (' or plus infinity' if plus_inf_okay else '') +
                                   ' but it is {}.'.format(f))
                matrix.logger.error(error)
                raise error
        else:
            f = np.asarray(default_value)
        return f

    def check_float_scalar(f, f_name='variable', default_value=None, lower_bound=-np.inf,
                           minus_inf_okay=False, plus_inf_okay=False):
        if f is not None:
            try:
                f = float(f)
            except TypeError as original_error:
                error = ValueError('{} must a float value but it is {}.'.format(f_name, f))
                matrix.logger.error(error)
                raise error from original_error
            if not (np.isfinite(f) or (minus_inf_okay and f == -np.inf) or
                    (plus_inf_okay and f == np.inf)):
                error = ValueError('{} must be finite'.format(f_name) +
                                   (' or minus infinity' if minus_inf_okay else '') +
                                   (' or plus infinity' if plus_inf_okay else '') +
                                   ' but it is {}.'.format(f))
                matrix.logger.error(error)
                raise error
            if lower_bound is not None and f < lower_bound:
                error = ValueError(('{} must be finite and greater or equal to {} '
                                    'but it is {}.').format(f_name, lower_bound, f))
                matrix.logger.error(error)
                raise error
        else:
            f = default_value
        return f

    min_diag_B = check_float_scalar_or_vector(min_diag_B, 'min_diag_B', default_value=-np.inf,
                                              minus_inf_okay=True, plus_inf_okay=False)
    max_diag_B = check_float_scalar_or_vector(max_diag_B, 'max_diag_B', default_value=np.inf,
                                              minus_inf_okay=False, plus_inf_okay=True)

    min_diag_D = check_float_scalar(min_diag_D, f_name='min_diag_D',
                                    default_value=0, lower_bound=0,
                                    minus_inf_okay=False, plus_inf_okay=False)
    max_diag_D = check_float_scalar(max_diag_D, f_name='max_diag_D',
                                    default_value=np.inf, lower_bound=None,
                                    minus_inf_okay=False, plus_inf_okay=True)

    if not max(np.max(min_diag_B), min_diag_D) <= min(np.min(max_diag_B), max_diag_D):
        error = ValueError(('The values of min_diag_B and min_diag_D must be lower or equal '
                            'to the values of max_diag_B and max_diag_D.'))
        matrix.logger.error(error)
        raise error

    # check permutation method
    if permutation_method is None:
        permutation_method = matrix.constants.MINIMAL_DIFFERENCE_PERMUTATION_METHOD
    else:
        permutation_method = permutation_method.lower()
    if is_dense:
        supported_permutation_methods = matrix.APPROXIMATION_PERMUTATION_METHODS
    else:
        supported_permutation_methods = (matrix.APPROXIMATION_PERMUTATION_METHODS +
                                         matrix.SPARSE_ONLY_PERMUTATION_METHODS)
    if permutation_method not in supported_permutation_methods:
        error = ValueError(('Permutation method {} is unknown. Only the following methods are '
                            'supported {}.'
                            ).format(permutation_method, supported_permutation_methods))
        matrix.logger.error(error)
        raise error
    use_minimal_difference_permutation_method = (
        permutation_method == matrix.constants.MINIMAL_DIFFERENCE_PERMUTATION_METHOD)

    # check overwrite_A
    if overwrite_A is None:
        overwrite_A = False
    if overwrite_A and np.issubdtype(A.dtype, np.integer):
        error = ValueError(('A has an integer dtype ({}) which can not be used to store the '
                            'values of L. Please set overwrite_A to False.').format(A.dtype))
        matrix.logger.error(error)
        raise error

    # check strict_lower_triangular_only_L
    if strict_lower_triangular_only_L is None:
        strict_lower_triangular_only_L = False

    # init L
    if overwrite_A:
        L = A
    else:
        L_dtype = np.promote_types(A.dtype, np.float16)
        if is_dense:
            if strict_lower_triangular_only_L or use_minimal_difference_permutation_method:
                L = np.empty((n, n), dtype=L_dtype)
            else:
                L = np.identity(n, dtype=L_dtype)
        else:
            if strict_lower_triangular_only_L or use_minimal_difference_permutation_method:
                L = scipy.sparse.lil_matrix((n, n), dtype=L_dtype)
            else:
                L = scipy.sparse.identity(n, dtype=L_dtype, format='lil')
    L_set_all_strict_lower_triangular_values = overwrite_A or is_dense
    L_set_all_diagonal_values = ((overwrite_A or use_minimal_difference_permutation_method) and
                                 not strict_lower_triangular_only_L)
    L_set_all_upper_triangular_values = ((overwrite_A or is_dense) and
                                         not strict_lower_triangular_only_L)

    # init other values
    alpha = np.zeros(n, dtype=np.float64)
    beta = np.zeros(n, dtype=np.float64)
    delta = np.empty(n, dtype=np.float64)
    omega = np.empty(n, dtype=np.float64)
    d = np.empty(n, dtype=np.float64)

    # check min_abs_values
    d_eps = np.finfo(d.dtype).eps
    L_eps = np.finfo(L.dtype).eps
    min_abs_value_D = check_float_scalar(min_abs_value_D, f_name='min_abs_value_D',
                                         default_value=d_eps**0.5, lower_bound=0,
                                         minus_inf_okay=False, plus_inf_okay=False)
    min_abs_value_D = max(min_abs_value_D, d_eps)

    # debug info
    matrix.logger.debug(('Using the following values: '
                         'min_diag_B={min_diag_B}, max_diag_B={max_diag_B}, '
                         'min_diag_D={min_diag_D}, max_diag_D={max_diag_D}, '
                         'min_abs_value_D={min_abs_value_D} '
                         'permutation_method={permutation_method}, overwrite_A={overwrite_A}, '
                         'strict_lower_triangular_only_L={strict_lower_triangular_only_L}.'
                         ).format(
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A,
        strict_lower_triangular_only_L=strict_lower_triangular_only_L))

    # calculate permutation vector
    if use_minimal_difference_permutation_method:
        if min_diag_D < 0:
            raise ValueError(('The permutation method {} is only available if min_diag_D greater '
                              'or equal zero.'
                              ).format(matrix.constants.MINIMAL_DIFFERENCE_PERMUTATION_METHOD))
        p = np.arange(n, dtype=np.min_scalar_type(n))
    else:
        p = matrix.permute.permutation_vector(A, permutation_method=permutation_method)

    # calculate values iteratively
    def get_value_i(v, i):
        try:
            return v[i]
        except TypeError:
            return v
        except IndexError:
            assert v.ndim == 0
            return v

    for i in range(n):
        # update p, d, omega
        if use_minimal_difference_permutation_method:
            all_minimal_changes = ((j, *_minimal_change(
                alpha[p[j]], beta[p[j]], gamma[p[j]], min_diag_D, max_diag_D=max_diag_D,
                min_diag_B=get_value_i(min_diag_B, p[j]), max_diag_B=get_value_i(max_diag_B, p[j]),
                min_abs_value_D=min_abs_value_D))
                for j in range(i, n))
            (j, d_i, omega_i, f_value_i) = min(all_minimal_changes,
                                               key=lambda x: (x[3], -x[1], x[2], x[0]))
            # swap p[i] and p[j]
            p_j = p[j]
            p[j] = p[i]
            p[i] = p_j
            # swap L[i, :] and L[j, :]
            if i > 0:
                if is_dense or L.format != 'lil':
                    L_j = L[j, :i].copy()
                    L[j, :i] = L[i, :i]
                    L[i, :i] = L_j
                else:
                    for iterable in (L.rows, L.data):
                        tmp = iterable[i]
                        iterable[i] = iterable[j]
                        iterable[j] = tmp
        else:
            d_i, omega_i, f_value_i = _minimal_change(
                alpha[p[i]], beta[p[i]], gamma[p[i]], min_diag_D, max_diag_D=max_diag_D,
                min_diag_B=get_value_i(min_diag_B, p[i]), max_diag_B=get_value_i(max_diag_B, p[i]),
                min_abs_value_D=min_abs_value_D)
        assert np.isfinite(d_i)
        assert np.isfinite(omega_i)
        d[i] = d_i
        omega[p[i]] = omega_i

        # update delta
        delta[p[i]] = d[i] + omega[p[i]]**2 * alpha[p[i]] - gamma[p[i]]
        assert np.isfinite(delta[p[i]])

        # update i-th row of L
        for j in range(i):
            L_j_i = L[i, j] * omega[p[i]]
            if abs(L_j_i) < L_eps:
                L_j_i = 0
            L[i, j] = L_j_i

        # calculate i-th column of L and update beta
        if d[i] != 0:
            if i > 0:
                L_i_d = L[i, :i].conj()
                if is_dense:
                    L_i_d = L_i_d * d[:i]
                else:
                    L_i_d = L_i_d.multiply(d[:i]).T

        for j in range(i + 1, n):
            # get value of A
            if not overwrite_A or p[i] >= p[j]:
                a = A[p[j], p[i]]
            else:
                a = A[p[i], p[j]].conj()

            # update beta
            beta_p_j_add = 2 * a * a.conj()
            assert np.isreal(beta_p_j_add)
            beta[p[j]] += beta_p_j_add.real

            # update i-th column of L
            if d[i] != 0:
                if i > 0:
                    b = L[j, :i] @ L_i_d
                    if not is_dense:
                        assert b.shape == (1, 1)
                        b = b[0, 0]
                else:
                    b = 0
                L_j_i = (a - b) / d[i]
                assert np.isfinite(L_j_i)
                if abs(L_j_i) < L_eps:
                    if L_set_all_strict_lower_triangular_values:
                        L[j, i] = 0
                else:
                    L[j, i] = L_j_i
                    alpha_p_j_add = L_j_i * L_j_i.conj() * d[i]
                    assert np.isreal(alpha_p_j_add)
                    alpha[p[j]] += alpha_p_j_add.real
            elif L_set_all_strict_lower_triangular_values:
                L[j, i] = 0

    # prepare diagonal and upper triangle of L if needed
    if L_set_all_diagonal_values:
        for i in range(n):
            L[i, i] = 1
    if L_set_all_upper_triangular_values:
        for i in range(n):
            L[i, i + 1:] = 0

    # return values
    matrix.logger.debug('Approximation of LDL decomposition finished.')
    return L, d, p, omega, delta


def decomposition(
        A, min_diag_B=None, max_diag_B=None, min_diag_D=None, max_diag_D=None,
        min_abs_value_D=None, permutation_method=None, overwrite_A=False, return_type=None):
    """
    Computes an approximative decomposition of a matrix with the specified properties.

    Returns a decomposition of `A` if has such a decomposition and
    otherwise  a decomposition of an approximation of `A`.

    Parameters
    ----------
    A : numpy.ndarray or scipy.sparse.spmatrix
        The matrix that should be approximated by a decomposition.
        It is assumed, that A is Hermitian. The matrix must be a squared matrix.
    min_diag_B : numpy.ndarray or float
        Each component of the diagonal of the composed matrix `B` of an approximated
        `LDL` decomposition is forced to be greater or equal to `min_diag_B`.
        optional, default : No minimal value is forced.
    max_diag_B : numpy.ndarray or float
        Each component of the diagonal of the composed matrix `B` of an approximated
        `LDL` decomposition is forced to be lower or equal to `max_diag_B`.
        optional, default : No maximal value is forced.
    min_diag_D : float
        Each component of the diagonal of the matrix `D` in an approximated
        `LDL` decomposition is forced to be greater or equal to `min_diag_D`.
        `min_diag_D` must be greater or equal to 0.
        optional, default : 0
    max_diag_D : float
        Each component of the diagonal of the matrix `D` in an approximated
        `LDL` decomposition is forced to be lower or equal to `max_diag_D`.
        optional, default : No maximal value is forced.
    min_abs_value_D : float
        Absolute values below `min_abs_value_D` are considered as zero
        in the matrix `D` of an approximated `LDL` decomposition.
        optional, default : _matrixThe square root of the resolution of the underlying data type.
    permutation_method : str
        The symmetric permutation method that is applied to the matrix before it is decomposed.
        It has to be a value in :const:`matrix.APPROXIMATION_PERMUTATION_METHODS`.
        If `A` is sparse, it can also be a value in
        :const:`matrix.SPARSE_ONLY_PERMUTATION_METHODS`.
        optional, default: The permutation is chosen by the algorithm.
    overwrite_A : bool
        Whether it is allowed to overwrite A. Enabling may result in performance gain.
        optional, default: False
    return_type : str
        The type of the decomposition that should be returned.
        It has to be a value in :const:`matrix.DECOMPOSITION_TYPES`.
        optional, default : The type of the decomposition is chosen by the function itself.

    Returns
    -------
    matrix.decompositions.DecompositionBase
        An (approximative) decomposition of `A` of type `return_type`.

    Raises
    ------
    matrix.errors.MatrixNotSquareError
        If `A` is not a square matrix.
    matrix.errors.MatrixComplexDiagonalValueError
        If `A` has complex diagonal values.
    """

    # debug info
    matrix.logger.debug(('Calculatin approximated decomposition with passed values: '
                         'min_diag_B={min_diag_B}, max_diag_B={max_diag_B}, '
                         'min_diag_D={min_diag_D}, max_diag_D={max_diag_D}, '
                         'min_abs_value_D={min_abs_value_D}, '
                         'permutation_method={permutation_method}, overwrite_A={overwrite_A}, '
                         'return_type={return_type}.').format(
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A, return_type=return_type))

    # check return type
    supported_return_types = matrix.constants.DECOMPOSITION_TYPES
    if return_type is not None and return_type not in supported_return_types:
        error = ValueError(('Unkown return type {}. Only values in {} are supported.'
                            ).format(return_type, supported_return_types))
        matrix.logger.error(error)
        raise error

    # calculate decomposition
    L, d, p, omega, delta = _decomposition(
        A, min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A,
        strict_lower_triangular_only_L=False)

    if matrix.sparse.util.is_sparse(L):
        matrix.logger.debug('Converting L to csr format.')
        L = L.tocsr(copy=False)
    decomposition = matrix.decompositions.LDL_Decomposition(L=L, d=d, p=p).as_type(return_type)

    # return decomposition
    matrix.logger.debug('Approximation of decomposition {} finished.'.format(decomposition))
    return decomposition


def _matrix(
        A, min_diag_B=None, max_diag_B=None, min_diag_D=None, max_diag_D=None,
        min_abs_value_D=None, permutation_method=None, overwrite_A=False):
    """
    Computes an approximation of `A` which has a `LDL` decomposition with the specified properties.

    Returns `A` if `A` has such a decomposition and otherwise an approximation of `A`.

    Parameters
    ----------
    A : numpy.ndarray or scipy.sparse.spmatrix
        The matrix that should be approximated.
        It is assumed, that A is Hermitian. The matrix must be a squared matrix.
    min_diag_B : numpy.ndarray or float
        Each component of the diagonal of the returned matrix
        is forced to be greater or equal to `min_diag_B`.
        optional, default : No minimal value is forced.
    max_diag_B : numpy.ndarray or float
        Each component of the diagonal of the returned matrix
        is forced to be lower or equal to `max_diag_B`.
        optional, default : No maximal value is forced.
    min_diag_D : float
        Each component of the diagonal of the matrix `D` in a `LDL` decomposition
        of the returned matrix is forced to be greater or equal to `min_diag_D`.
        `min_diag_D` must be greater or equal to 0.
        optional, default : 0
    max_diag_D : float
        Each component of the diagonal of the matrix `D` in a `LDL` decomposition
        of the returned matrix is forced to be lower or equal to `max_diag_D`.
        optional, default : No maximal value is forced.
    min_abs_value_D : float
        Absolute values below `min_abs_value_D` are considered as zero
        in the matrix `D` in a `LDL` decomposition of the returned matrix.
        optional, default : _matrixThe square root of the resolution of the underlying data type.
    permutation_method : str
        The symmetric permutation method that is applied to the matrix before it is decomposed.
        It has to be a value in :const:`matrix.APPROXIMATION_PERMUTATION_METHODS`.
        If `A` is sparse, it can also be a value in
        :const:`matrix.SPARSE_ONLY_PERMUTATION_METHODS`.
        optional, default: The permutation is chosen by the algorithm.
    overwrite_A : bool
        Whether it is allowed to overwrite A. Enabling may result in performance gain.
        optional, default: False

    Returns
    -------
    B : numpy.ndarray or scipy.sparse.spmatrix (same type as `A`)
        An approximation of `A` which has a `LDL` decomposition.

    Raises
    ------
    matrix.errors.MatrixNotSquareError
        If `A` is not a square matrix.
    matrix.errors.MatrixComplexDiagonalValueError
        If `A` has complex diagonal values.
    """

    # debug info
    matrix.logger.debug(('Calcualting approximation of a matrix with passed values: '
                         'min_diag_B={min_diag_B}, max_diag_B={max_diag_B}, '
                         'min_diag_D={min_diag_D}, max_diag_D={max_diag_D}, '
                         'min_abs_value_D={min_abs_value_D}, '
                         'permutation_method={permutation_method}, overwrite_A={overwrite_A}.'
                         ).format(
        min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A))

    # calculate decomposition
    L, d, p, omega, delta = _decomposition(
        A, min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A,
        strict_lower_triangular_only_L=True)

    # init B
    matrix.logger.debug('Calculating approximation matrix B.')
    n = L.shape[0]
    B_dtype = L.dtype
    if np.all(d != 0):
        del L
    is_dense = not matrix.sparse.util.is_sparse(A)
    if overwrite_A:
        B = A
    else:
        if is_dense:
            B = np.empty((n, n), dtype=B_dtype)
        else:
            B = scipy.sparse.lil_matrix((n, n), dtype=B_dtype)

    # populate B
    q = matrix.permute.invert_permutation_vector(p)

    def get_value_i(v, i):
        try:
            return v[i]
        except TypeError:
            return v
        except IndexError:
            assert v.ndim == 0
            return v

    for i in range(n):
        # set diagonal entries
        B_i_i = A[i, i] + delta[i]
        min_B_i_i = get_value_i(min_diag_B, i)
        if min_B_i_i is not None and B_i_i < min_B_i_i:
            assert np.isclose(B_i_i, min_B_i_i)
            B_i_i = min_B_i_i
        max_B_i_i = get_value_i(max_diag_B, i)
        if max_B_i_i is not None and B_i_i > max_B_i_i:
            assert np.isclose(B_i_i, max_B_i_i)
            B_i_i = max_B_i_i
        assert np.isfinite(B_i_i)
        assert np.isreal(B_i_i)
        B[i, i] = B_i_i

        # set upper diagonal entries
        for j in range(i + 1, n):
            if q[i] > q[j]:
                a = j
                b = i
            else:
                a = i
                b = j
            assert q[a] < q[b]
            if d[q[a]] != 0:
                B_i_j = A[i, j] * omega[b]
            else:
                if q[a] > 0:
                    if is_dense:
                        r_i = L[q[i], :q[a]] * d[:q[a]]
                    else:
                        r_i = L[q[i], :q[a]].multiply(d[:q[a]])
                    B_i_j = r_i @ L[q[j], :q[a]].T.conj()
                    if not is_dense:
                        assert B_i_j.shape == (1, 1)
                        B_i_j = B_i_j[0, 0]
                else:
                    B_i_j = 0
            assert np.isfinite(B_i_j)
            B[i, j] = B_i_j
#            B[j, i] = np.conj(B_i_j)

    # set lower diagonal entries
    for i in range(n):
        for j in range(i + 1, n):
            B[j, i] = np.conj(B[i, j])

    # return B
    if not is_dense:
        B = B.asformat(A.format)
    matrix.logger.debug('Approximation matrix B calculated.')
    return B


def positive_semidefinite_matrix(
        A, min_diag_B=None, max_diag_B=None, min_diag_D=None, max_diag_D=None,
        min_abs_value_D=None, permutation_method=None, overwrite_A=False):
    """
    Computes a positive semidefinite approximation of `A`.

    Returns `A` if `A` is positive semidefinite and otherwise an approximation of `A`.

    Parameters
    ----------
    A : numpy.ndarray or scipy.sparse.spmatrix
        The matrix that should be approximated.
        It is assumed, that A is Hermitian. The matrix must be a squared matrix.
    min_diag_B : numpy.ndarray or float
        Each component of the diagonal of the returned matrix
        is forced to be greater or equal to `min_diag_B`.
        optional, default : No minimal value is forced.
    max_diag_B : numpy.ndarray or float
        Each component of the diagonal of the returned matrix
        is forced to be lower or equal to `max_diag_B`.
        optional, default : No maximal value is forced.
    min_diag_D : float
        Each component of the diagonal of the matrix `D` in a `LDL` decomposition
        of the returned matrix is forced to be greater or equal to `min_diag_D`.
        `min_diag_D` must be greater or equal to 0.
        optional, default : 0
    max_diag_D : float
        Each component of the diagonal of the matrix `D` in a `LDL` decomposition
        of the returned matrix is forced to be lower or equal to `max_diag_D`.
        optional, default : No maximal value is forced.
    min_abs_value_D : float
        Absolute values below `min_abs_value_D` are considered as zero
        in the matrix `D` in a `LDL` decomposition of the returned matrix.
        optional, default : _matrixThe square root of the resolution of the underlying data type.
    permutation_method : str
        The symmetric permutation method that is applied to the matrix before it is decomposed.
        It has to be a value in :const:`matrix.APPROXIMATION_PERMUTATION_METHODS`.
        If `A` is sparse, it can also be a value in
        :const:`matrix.SPARSE_ONLY_PERMUTATION_METHODS`.
        optional, default: The permutation is chosen by the algorithm.
    overwrite_A : bool
        Whether it is allowed to overwrite A. Enabling may result in performance gain.
        optional, default: False

    Returns
    -------
    B : numpy.ndarray or scipy.sparse.spmatrix (same type as `A`)
        An approximation of `A` which has a `LDL` decomposition.

    Raises
    ------
    matrix.errors.MatrixNotSquareError
        If `A` is not a square matrix.
    matrix.errors.MatrixComplexDiagonalValueError
        If `A` has complex diagonal values.
    """

    return _matrix(
        A, min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A)


def positive_definite_matrix(
        A, min_diag_B=None, max_diag_B=None, min_diag_D=None, max_diag_D=None,
        min_abs_value_D=None, permutation_method=None, overwrite_A=False):
    """
    Computes a positive definite approximation of `A`.

    Returns `A` if `A` is positive definite and otherwise an approximation of `A`.

    Parameters
    ----------
    A : numpy.ndarray or scipy.sparse.spmatrix
        The matrix that should be approximated.
        It is assumed, that A is Hermitian. The matrix must be a squared matrix.
    min_diag_B : numpy.ndarray or float
        Each component of the diagonal of the returned matrix
        is forced to be greater or equal to `min_diag_B`.
        optional, default : No minimal value is forced.
    max_diag_B : numpy.ndarray or float
        Each component of the diagonal of the returned matrix
        is forced to be lower or equal to `max_diag_B`.
        optional, default : No maximal value is forced.
    min_diag_D : float
        Each component of the diagonal of the matrix `D` in a `LDL` decomposition
        of the returned matrix is forced to be greater or equal to `min_diag_D`.
        `min_diag_D` must be greater than 0.
        optional, default : The square root of the resolution of the underlying data type.
    max_diag_D : float
        Each component of the diagonal of the matrix `D` in a `LDL` decomposition
        of the returned matrix is forced to be lower or equal to `max_diag_D`.
        optional, default : No maximal value is forced.
    min_abs_value_D : float
        Absolute values below `min_abs_value_D` are considered as zero
        in the matrix `D` in a `LDL` decomposition of the returned matrix.
        optional, default : _matrixThe square root of the resolution of the underlying data type.
    permutation_method : str
        The symmetric permutation method that is applied to the matrix before it is decomposed.
        It has to be a value in :const:`matrix.APPROXIMATION_PERMUTATION_METHODS`.
        If `A` is sparse, it can also be a value in
        :const:`matrix.SPARSE_ONLY_PERMUTATION_METHODS`.
        optional, default: The permutation is chosen by the algorithm.
    overwrite_A : bool
        Whether it is allowed to overwrite A. Enabling may result in performance gain.
        optional, default: False

    Returns
    -------
    B : numpy.ndarray or scipy.sparse.spmatrix (same type as `A`)
        An approximation of `A` which has a `LDL` decomposition.

    Raises
    ------
    matrix.errors.MatrixNotSquareError
        If `A` is not a square matrix.
    matrix.errors.MatrixComplexDiagonalValueError
        If `A` has complex diagonal values.
    """

    if min_diag_D is None:
        min_diag_D = np.finfo(np.float64).eps**(0.5)
    elif min_diag_D <= 0:
        raise ValueError('min_diag_D must be greater to zero.')

    return _matrix(
        A, min_diag_B=min_diag_B, max_diag_B=max_diag_B,
        min_diag_D=min_diag_D, max_diag_D=max_diag_D, min_abs_value_D=min_abs_value_D,
        permutation_method=permutation_method, overwrite_A=overwrite_A)


def _minimal_change(alpha, beta, gamma, min_diag_D, max_diag_D=np.inf,
                    min_diag_B=-np.inf, max_diag_B=np.inf, min_abs_value_D=0):
    # check input
    assert min_diag_D >= 0
    assert alpha >= 0
    assert beta >= 0
    assert min_abs_value_D >= 0
    assert beta != 0 or alpha == 0
    assert max(min_diag_D, min_diag_B) <= min(max_diag_D, max_diag_B)

    def f(d, omega):
        f_value = (d + omega**2 * alpha - gamma)**2 + (omega - 1)**2 * beta
        assert f_value >= 0
        return f_value

    # inner solution
    d = gamma - alpha
    if (max(min_diag_D, min_diag_B - alpha) <= d <= min(max_diag_D, max_diag_B - alpha) and
            (d == 0 or d >= min_abs_value_D)):
        omega = 1
        f_value = 0
        assert np.isclose(f(d, omega), f_value)

    # solution at bound,  alpha == 0
    elif alpha == 0:
        if min_diag_D == 0 and min_diag_B <= 0 and 2 * gamma < min_abs_value_D:
            d = 0
        else:
            d = max(min_diag_D, min_abs_value_D, min_diag_B, min(gamma, max_diag_D, max_diag_B))
        omega = 1
        f_value = f(d, omega)

    # solution at bound, alpha != 0
    else:
        # omega on bound
        assert alpha > 0
        assert beta > 0
        C = []
        a = max(min_diag_D, min_abs_value_D)
        b = min(max_diag_D, max_diag_B)
        for d in (min_diag_B - alpha, max_diag_B - alpha):
            if np.isfinite(d) and a <= d <= b:
                C.append((d, 1))
        if max(a, min_diag_B) <= gamma <= b:
            C.append((gamma, 0))

        # d on bound
        d_values = [a]
        if np.isfinite(b):
            d_values.append(b)
        if min_diag_D == 0:
            d_values.append(min_diag_D)
        for d in d_values:
            # get roots
            omegas = np.roots([2 * alpha**2, 0, 2 * alpha * (d - gamma) + beta, - beta])
            assert len(omegas) == 3
            # use only real roots
            omegas = tuple(omega.real for omega in omegas if np.isreal(omega))
            assert len(omegas) in (1, 3)
            # apply bounds and add to candidate list
            omega_lower = (max(min_diag_B - d, 0) / alpha)**0.5
            assert omega_lower >= 0
            omega_upper = ((max_diag_B - d) / alpha)**0.5
            assert omega_upper >= omega_lower
            for omega in omegas:
                omega = min(max(omega, omega_lower), omega_upper)
                C.append((d, omega))

        # calculate function values for candidates
        C_with_f_value = ((d, omega, f(d, omega)) for (d, omega) in C)

        # return best values
        (d, omega, f_value) = min(C_with_f_value, key=lambda x: (x[2], -x[0], x[1]))

    # return value
    assert min_diag_D <= d <= max_diag_D
    assert d >= min_abs_value_D or (d == 0 and min_diag_D == 0)
    assert omega >= 0
    assert min_diag_B <= d + omega**2 * alpha or np.isclose(min_diag_B, d + omega**2 * alpha)
    assert d + omega**2 * alpha <= max_diag_B or np.isclose(max_diag_B, d + omega**2 * alpha)
    assert f_value >= 0
    return (d, omega, f_value)