"""
This package provides functions to approximate matrices by positive semidefinite matrices.
"""

from matrix.approximation.positive_semidefinite.Reimer import decomposition, positive_semidefinite_matrix

from matrix.approximation.positive_semidefinite.Reimer import APPROXIMATION_ONLY_PERMUTATION_METHODS, MAXIMAL_STABILITY_PERMUTATION_METHOD, MINIMAL_DIFFERENCE_PERMUTATION_METHOD
APPROXIMATION_ONLY_PERMUTATION_METHODS = APPROXIMATION_ONLY_PERMUTATION_METHODS
""" Permutation methods supported only by the decomposition and the positive_semidefinite_matrix algorithm. """
MINIMAL_DIFFERENCE_PERMUTATION_METHOD = MINIMAL_DIFFERENCE_PERMUTATION_METHOD
""" Permutation method supported by the decomposition and the positive_semidefinite_matrix algorithm. """
MAXIMAL_STABILITY_PERMUTATION_METHOD = MAXIMAL_STABILITY_PERMUTATION_METHOD
""" Permutation method supported by the decomposition and the positive_semidefinite_matrix algorithm. """
