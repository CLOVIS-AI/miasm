#                                                                              #
#                     Simplification methods library                           #
#                                                                              #

import logging

from miasm_rs import ExpressionSimplifier

# Expression Simplifier
# ---------------------

log_exprsimp = logging.getLogger("exprsimp")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)-8s]: %(message)s"))
log_exprsimp.addHandler(console_handler)
log_exprsimp.setLevel(logging.WARNING)

# Public ExprSimplificationPass instance with commons passes
expr_simp = ExpressionSimplifier()
expr_simp.enable_common()

expr_simp_high_to_explicit = ExpressionSimplifier()
expr_simp_high_to_explicit.enable_high_to_explicit()

expr_simp_explicit = ExpressionSimplifier()
expr_simp_explicit.enable_common()
expr_simp_explicit.enable_high_to_explicit()
