"""Provide dependency graph"""

import miasm_rs
from miasm.expression.expression import ExprInt, ExprLoc, ExprAssign, \
    ExprWalk, canonize_to_exprloc
from miasm.ir.symbexec import SymbolicExecutionEngine
from miasm.ir.translators import Translator
from miasm.expression.expression_helper import possible_values

try:
    import z3
except:
    pass

DependencyGraph = miasm_rs.DependencyGraph
DependencyNode = miasm_rs.DependencyNode
DependencyResult = miasm_rs.DependencyResult


# class DependencyResultImplicit(DependencyResult):
#     # TODO: migrate to Rust
#
#     """Stand for a result of a DependencyGraph with implicit option
#
#     Provide path constraints using the z3 solver"""
#     # Z3 Solver instance
#     _solver = None
#
#     unsat_expr = ExprAssign(ExprInt(0, 1), ExprInt(1, 1))
#
#     def _gen_path_constraints(self, translator, expr, expected):
#         """Generate path constraint from @expr. Handle special case with
#         generated loc_keys
#         """
#         out = []
#         expected = canonize_to_exprloc(self._ircfg.loc_db, expected)
#         expected_is_loc_key = expected.is_loc()
#         for consval in possible_values(expr):
#             value = canonize_to_exprloc(self._ircfg.loc_db, consval.value)
#             if expected_is_loc_key and value != expected:
#                 continue
#             if not expected_is_loc_key and value.is_loc_key():
#                 continue
#
#             conds = z3.And(*[translator.from_expr(cond.to_constraint())
#                              for cond in consval.constraints])
#             if expected != value:
#                 conds = z3.And(
#                     conds,
#                     translator.from_expr(
#                         ExprAssign(value,
#                                 expected))
#                 )
#             out.append(conds)
#
#         if out:
#             conds = z3.Or(*out)
#         else:
#             # Ex: expr: lblgen1, expected: 0x1234
#             # -> Avoid inconsistent solution lblgen1 = 0x1234
#             conds = translator.from_expr(self.unsat_expr)
#         return conds
#
#     def emul(self, lifter, ctx=None, step=False):
#         # Init
#         ctx_init = {}
#         if ctx is not None:
#             ctx_init.update(ctx)
#         solver = z3.Solver()
#         symb_exec = SymbolicExecutionEngine(lifter, ctx_init)
#         history = self.history[::-1]
#         history_size = len(history)
#         translator = Translator.to_language("z3")
#         size = self._ircfg.IRDst.size
#
#         for hist_nb, loc_key in enumerate(history, 1):
#             if hist_nb == history_size and loc_key == self.initial_state.loc_key:
#                 line_nb = self.initial_state.line_nb
#             else:
#                 line_nb = None
#             irb = self.irblock_slice(self._ircfg.blocks[loc_key], line_nb)
#
#             # Emul the block and get back destination
#             dst = symb_exec.eval_updt_irblock(irb, step=step)
#
#             # Add constraint
#             if hist_nb < history_size:
#                 next_loc_key = history[hist_nb]
#                 expected = symb_exec.eval_expr(ExprLoc(next_loc_key, size))
#                 solver.add(self._gen_path_constraints(translator, dst, expected))
#         # Save the solver
#         self._solver = solver
#
#         # Return only inputs values (others could be wrongs)
#         return {
#             element: symb_exec.eval_expr(element)
#             for element in self.inputs
#         }
#
#     @property
#     def is_satisfiable(self):
#         """Return True iff the solution path admits at least one solution
#         PRE: 'emul'
#         """
#         return self._solver.check() == z3.sat
#
#     @property
#     def constraints(self):
#         """If satisfiable, return a valid solution as a Z3 Model instance"""
#         if not self.is_satisfiable:
#             raise ValueError("Unsatisfiable")
#         return self._solver.model()
#
#
# class FollowExpr(object):
#     # TODO: migrate to Rust
#
#     "Stand for an element (expression, depnode, ...) to follow or not"
#     __slots__ = ["follow", "element"]
#
#     def __init__(self, follow, element):
#         self.follow = follow
#         self.element = element
#
#     def __repr__(self):
#         return '%s(%r, %r)' % (self.__class__.__name__, self.follow, self.element)
#
#     @staticmethod
#     def to_depnodes(follow_exprs, loc_key, line):
#         """Build a set of FollowExpr(DependencyNode) from the @follow_exprs set
#         of FollowExpr
#         @follow_exprs: set of FollowExpr
#         @loc_key: LocKey instance
#         @line: integer
#         """
#         dependencies = set()
#         for follow_expr in follow_exprs:
#             dependencies.add(FollowExpr(follow_expr.follow,
#                                         DependencyNode(loc_key,
#                                                        follow_expr.element,
#                                                        line)))
#         return dependencies
#
#     @staticmethod
#     def extract_depnodes(follow_exprs, only_follow=False):
#         """Extract depnodes from a set of FollowExpr(Depnodes)
#         @only_follow: (optional) extract only elements to follow"""
#         return set(follow_expr.element
#                    for follow_expr in follow_exprs
#                    if not(only_follow) or follow_expr.follow)
#
#
# class FilterExprSources(ExprWalk):
#     # TODO: Migrate to Rust
#
#     """
#     Walk Expression to find sources to track
#     @follow_mem: (optional) Track memory syntactically
#     @follow_call: (optional) Track through "call"
#     """
#     def __init__(self, follow_mem, follow_call):
#         super(FilterExprSources, self).__init__(lambda x:None)
#         self.follow_mem = follow_mem
#         self.follow_call = follow_call
#         self.nofollow = set()
#         self.follow = set()
#
#     def visit(self, expr, *args, **kwargs):
#         if expr in self.cache:
#             return None
#         ret = self.visit_inner(expr, *args, **kwargs)
#         self.cache.add(expr)
#         return ret
#
#     def visit_inner(self, expr, *args, **kwargs):
#         if expr.is_id():
#             self.follow.add(expr)
#         elif expr.is_int():
#             self.nofollow.add(expr)
#         elif expr.is_loc():
#             self.nofollow.add(expr)
#         elif expr.is_mem():
#             if self.follow_mem:
#                 self.follow.add(expr)
#             else:
#                 self.nofollow.add(expr)
#                 return None
#         elif expr.is_function_call():
#             if self.follow_call:
#                 self.follow.add(expr)
#             else:
#                 self.nofollow.add(expr)
#                 return None
#
#         ret = super(FilterExprSources, self).visit(expr, *args, **kwargs)
#         return ret
