from __future__ import print_function

import os.path
from typing import Tuple, Optional

from future.utils import viewitems
from miasm.loader import pe_init
from miasm.loader.strpatchwork import StrPatchwork

from miasm.core import parse_asm, asmblock
from miasm.analysis.machine import Machine
from miasm.core.interval import interval
from miasm.core.locationdb import LocationDB
from miasm.core.utils import iterbytes, int_to_byte


def shellcode(source_path: str, architecture: str, output_path: str, generate_pe: bool = False,
              encrypt: Optional[Tuple[str, str]] = None, force: bool = False) -> bool:
    """
    Assembles an ASM file into a binary file.

    :param source_path: The ASM file that should be assembled
    :param architecture: The architecture of the `source_path` file
    :param output_path: The file that will be created, containing the generated binary
    :param generate_pe: `True` to generate a PE file
    :param encrypt: Tuple of the label where encryption starts, and the label where encryption ends. `None` for no encryption.
    :param force: `True` to assemble the file even if the output was already up-to-date, `False` to assemble only if the input is newer than the output.
    :return: `True` if the file was assembled, `False` if it was not (eg. if it was up-to-date).
    """

    # region Avoid assembling if the output is newer than the input
    try:
        output_modified_time = os.path.getmtime(output_path)
    except FileNotFoundError:
        output_modified_time = 0

    if force or os.path.getmtime(source_path) > output_modified_time:
        print("shellcode: Assembling", source_path, "into", output_path)
    else:
        print("shellcode:", source_path, "is up-to-date; output file:", output_path)
        return False
    # endregion

    # Get architecture-dependent parameters
    machine = Machine(architecture)
    try:
        attrib = machine.dis_engine.attrib
        size = int(attrib)
    except AttributeError:
        attrib = None
        size = 32
    except ValueError:
        size = 32
    reg_and_id = dict(machine.mn.regs.all_regs_ids_byname)
    base_expr = machine.base_expr
    dst_interval = None

    # Output format
    if generate_pe:
        pe = pe_init.PE(wsize=size)
        s_text = pe.SHList.add_section(name="text", addr=0x1000, rawsize=0x1000)
        s_iat = pe.SHList.add_section(name="iat", rawsize=0x100)
        new_dll = [
            (
                {
                    "name": "USER32.dll",
                    "firstthunk": s_iat.addr
                },
                [
                    "MessageBoxA"
                ]
            )
        ]
        pe.DirImport.add_dlldesc(new_dll)
        s_myimp = pe.SHList.add_section(name="myimp", rawsize=len(pe.DirImport))
        pe.DirImport.set_rva(s_myimp.addr)
        pe.Opthdr.AddressOfEntryPoint = s_text.addr

        addr_main = pe.rva2virt(s_text.addr)
        virt = pe.virt
        output = pe
        dst_interval = interval(
            [
                (pe.rva2virt(s_text.addr), pe.rva2virt(s_text.addr + s_text.size))
            ]
        )
    else:
        st = StrPatchwork()

        addr_main = 0
        virt = st
        output = st

    # Get and parse the source code
    with open(source_path) as fstream:
        source_path = fstream.read()

    loc_db = LocationDB()

    asmcfg = parse_asm.parse_txt(machine.mn, attrib, source_path, loc_db)

    # Fix shellcode addrs
    loc_db.set_location_offset(loc_db.get_name_location("main"), addr_main)

    if generate_pe:
        loc_db.set_location_offset(
            loc_db.get_or_create_name_location("MessageBoxA"),
            pe.DirImport.get_funcvirt(
                'USER32.dll',
                'MessageBoxA'
            )
        )

    # Print and graph firsts blocks before patching it
    for block in asmcfg.blocks:
        print(block)
    with open("%s.dot" % output_path, "w") as graph:
        graph.write(asmcfg.dot())

    # Apply patches
    patches = asmblock.asm_resolve_final(
        machine.mn,
        asmcfg,
        dst_interval
    )
    if encrypt:
        # Encrypt code
        loc_start = loc_db.get_or_create_name_location(encrypt[0])
        loc_stop = loc_db.get_or_create_name_location(encrypt[1])
        ad_start = loc_db.get_location_offset(loc_start)
        ad_stop = loc_db.get_location_offset(loc_stop)

        for ad, val in list(viewitems(patches)):
            if ad_start <= ad < ad_stop:
                patches[ad] = b"".join(int_to_byte(ord(x) ^ 0x42) for x in iterbytes(val))

    print(patches)
    if isinstance(virt, StrPatchwork):
        for offset, raw in viewitems(patches):
            virt[offset] = raw
    else:
        for offset, raw in viewitems(patches):
            virt.set(offset, raw)

    # Produce output
    with open(output_path, 'wb') as file:
        file.write(bytes(output))

    return True


def shellcode_sample(source_path: str, architecture: str, output_path: str, generate_pe: bool = False,
                     encrypt: Optional[Tuple[str, str]] = None, force: bool = False) -> Tuple[str, bool]:
    """Same as 'shellcode', but the input is a path relative to the 'samples' directory instead of the current working directory."""

    current_path = os.path.abspath(os.path.dirname(__file__))
    source_path = os.path.join(current_path, "../samples/", source_path)
    output_path = os.path.join(current_path, "../samples/", output_path)

    return output_path, shellcode(source_path, architecture, output_path, generate_pe, encrypt, force)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Multi-arch (32 bits) assembler")
    parser.add_argument('architecture', help="architecture: " +
                                             ",".join(Machine.available_machine()))
    parser.add_argument("source", help="Source file to assemble")
    parser.add_argument("output", help="Output file")
    parser.add_argument("--PE", help="Create a PE with a few imports",
                        action="store_true")
    parser.add_argument("-e", "--encrypt",
                        help="Encrypt the code between <label_start> <label_stop>",
                        nargs=2)
    args = parser.parse_args()

    shellcode(args.source, args.architecture, args.output, args.PE, args.encrypt, force=True)
