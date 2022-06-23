import pytest
from miasm.expression.expression import *
from miasm.ir.translators.translator import Translator


def test():
    import z3
    t_z3 = Translator.to_language("z3")
    t_smt2 = Translator.to_language("smt2")

    # create nested expression
    a = ExprId("a", 64)
    b = ExprId('b', 32)
    c = ExprId('c', 16)
    d = ExprId('d', 8)
    e = ExprId('e', 1)

    left = ExprCond(
        e + ExprOp('parity', a),
        ExprMem(a * a, 64),
        ExprMem(a, 64)
    )

    cond = (
            ExprSlice(
                ExprSlice(
                    ExprSlice(a, 0, 32) + b, 0, 16
                ) * c,
                0,
                8
            ) << ExprOp('>>>', d, ExprInt(0x5, 8))
    )
    right = ExprCond(
        cond,
        a + ExprInt(0x64, 64),
        ExprInt(0x16, 64)
    )

    e = ExprAssign(left, right)

    # translate to z3
    e_z3 = t_z3.from_expr(e)
    # translate to smt2
    smt2 = t_smt2.to_smt2([t_smt2.from_expr(e)])

    # parse smt2 string with z3
    result = z3.parse_smt2_string(smt2)
    smt2_z3 = result[0]
    # initialise SMT solver
    s = z3.Solver()

    # prove equivalence of z3 and smt2 translation
    s.add(e_z3 != smt2_z3)
    assert (s.check() == z3.unsat)
