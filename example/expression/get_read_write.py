from __future__ import print_function

from future.utils import viewitems

from miasm.arch.x86.arch import mn_x86
from miasm.arch.x86.lifter_model_call import LifterModelCall_x86_32
from miasm.core.locationdb import LocationDB

loc_db = LocationDB()


def main():
    arch = mn_x86
    lifter = LifterModelCall_x86_32(loc_db)
    ircfg = lifter.new_ircfg()
    instr = arch.fromstring('LODSB', loc_db, 32)
    instr.offset, instr.l = 0, 15
    lifter.add_instr_to_ircfg(instr, ircfg)

    print('*' * 80)
    for lbl, irblock in viewitems(ircfg.blocks):
        print(irblock)
        for assignblk in irblock:
            rw = assignblk.get_rw()
            for dst, reads in viewitems(rw):
                print('read:   ', [str(x) for x in reads])
                print('written:', dst)
                print()

    open('graph_instr.dot', 'w').write(ircfg.dot())


if __name__ == '__main__':
    print("""
    Simple expression manipulation demo.
    Get read/written registers for a given instruction
    """)
    main()
