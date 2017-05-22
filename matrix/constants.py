# *** decomposition types *** #

BASE_DECOMPOSITION_TYPE = 'base'
LDL_DECOMPOSITION_TYPE = 'LDL'
LDL_DECOMPOSITION_COMPRESSED_TYPE = 'LDL_compressed'
LL_DECOMPOSITION_TYPE = 'LL'

DECOMPOSITION_TYPES = (LDL_DECOMPOSITION_TYPE, LDL_DECOMPOSITION_COMPRESSED_TYPE, LL_DECOMPOSITION_TYPE)
""" Supported types of decompositions. """

# *** permutation methods *** #

NO_PERMUTATION_METHODS = (None, '', 'none', 'natural')

DECREASING_DIAGONAL_VALUES_PERMUTATION_METHOD = 'decreasing_diagonal_values'
INCREASING_DIAGONAL_VALUES_PERMUTATION_METHOD = 'increasing_diagonal_values'
DECREASING_ABSOLUTE_DIAGONAL_VALUES_PERMUTATION_METHOD = 'decreasing_absolute_diagonal_values'
INCREASING_ABSOLUTE_DIAGONAL_VALUES_PERMUTATION_METHOD = 'increasing_absolute_diagonal_values'

UNIVERSAL_PERMUTATION_METHODS = (
    DECREASING_DIAGONAL_VALUES_PERMUTATION_METHOD,
    INCREASING_DIAGONAL_VALUES_PERMUTATION_METHOD,
    DECREASING_ABSOLUTE_DIAGONAL_VALUES_PERMUTATION_METHOD,
    INCREASING_ABSOLUTE_DIAGONAL_VALUES_PERMUTATION_METHOD)
PERMUTATION_METHODS = NO_PERMUTATION_METHODS + UNIVERSAL_PERMUTATION_METHODS
""" Supported permutation methods for dense and sparse matrices. """

from matrix.sparse.constants import SPARSE_PERMUTATION_METHODS
