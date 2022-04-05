from future.utils import viewitems

from miasm.expression.expression import ExprId, ExprInt, ExprAssign, \
    ExprCond, ExprLoc, LocKey
from miasm.core.locationdb import LocationDB
from miasm.ir.analysis import LifterModelCall
from miasm.ir.ir import IRBlock, AssignBlock, IRCFG
from miasm.core.graph import DiGraph
from miasm.analysis.depgraph import DependencyNode, DependencyGraph, DependencyResult
from itertools import count
from pdb import pm
import re

loc_db = LocationDB()

dst = ExprId("IRDst", 32)
a = ExprId("a", 32)
b = ExprId("b", 32)
db = LocationDB()


lbl0 = db.add_location("lbl0", 0)

ircfg = IRCFG(dst, db)

ircfg.add_irblock(IRBlock(db, lbl0, [
    AssignBlock([
        ExprAssign(dst, ExprInt(10, 32)),
        ExprAssign(b, ExprInt(12, 32) + b),
    ], "test"),
    AssignBlock([
        ExprAssign(a, ExprInt(12, 32) + b),
    ], "test2", 1),
]))

generator = DependencyGraph(ircfg)
results: list[DependencyResult] = generator.get(lbl0, [a], 1, set())

print("Program", ircfg)

for result in results:
    print(result)
    print("Pending", result.unresolved)
    print("Relevant", result.relevant_nodes)

    block = ircfg.get_block(lbl0)
    print("IRBlock", block)
    block_sliced = result.irblock_slice(block, 10)
    print("IRBlock slice", block_sliced)
