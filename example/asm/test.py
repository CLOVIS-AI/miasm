# This file contains automated tests for this module.
# You can use these tests as usage examples.
# To run these, see the 'Testing' section in the README.

from .shellcode import shellcode_sample
from .simple import disassemble


def test_shellcode_avoid_recompile():
    assert shellcode_sample("x86_32_dead.S", "x86_32", "x86_32_dead.bin", force=True)[1]
    assert not shellcode_sample("x86_32_dead.S", "x86_32", "x86_32_dead.bin", force=False)[1]


def test_disassemble():
    disassemble()
