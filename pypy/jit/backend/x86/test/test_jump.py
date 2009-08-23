from pypy.jit.backend.x86.ri386 import *
from pypy.jit.backend.x86.jump import remap_stack_layout

class MockAssembler:
    def __init__(self):
        self.ops = []

    def regalloc_load(self, from_loc, to_loc):
        self.ops.append(('load', from_loc, to_loc))

    def regalloc_store(self, from_loc, to_loc):
        self.ops.append(('store', from_loc, to_loc))

    def regalloc_push(self, loc):
        self.ops.append(('push', loc))

    def regalloc_pop(self, loc):
        self.ops.append(('pop', loc))

    def got(self, expected):
        print '------------------------ comparing ---------------------------'
        for op1, op2 in zip(self.ops, expected):
            print '%-38s| %-38s' % (op1, op2)
            if op1 == op2:
                continue
            assert len(op1) == len(op2)
            for x, y in zip(op1, op2):
                if isinstance(x, MODRM) and isinstance(y, MODRM):
                    assert x.byte == y.byte
                    assert x.extradata == y.extradata
                else:
                    assert x == y
        assert len(self.ops) == len(expected)
        return True


def test_trivial():
    assembler = MockAssembler()
    remap_stack_layout(assembler, [], [])
    assert assembler.ops == []
    remap_stack_layout(assembler, [eax, ebx, ecx, edx, esi, edi],
                                  [eax, ebx, ecx, edx, esi, edi])
    assert assembler.ops == []
    s8 = mem(ebp, -8)
    s12 = mem(ebp, -12)
    s20 = mem(ebp, -20)
    remap_stack_layout(assembler, [eax, ebx, ecx, s20, s8, edx, s12, esi, edi],
                                  [eax, ebx, ecx, s20, s8, edx, s12, esi, edi])
    assert assembler.ops == []

def test_simple_registers():
    assembler = MockAssembler()
    remap_stack_layout(assembler, [eax, ebx, ecx], [edx, esi, edi])
    assert assembler.ops == [('load', eax, edx),
                             ('load', ebx, esi),
                             ('load', ecx, edi)]

def test_simple_stacklocs():
    assembler = MockAssembler()
    s8 = mem(ebp, -8)
    s12 = mem(ebp, -12)
    s20 = mem(ebp, -20)
    s24 = mem(ebp, -24)
    remap_stack_layout(assembler, [s8, eax, s12], [s20, s24, edi], [edx, esi])
    assert assembler.ops == [('load', s8, edx),
                             ('store', edx, s20),
                             ('store', eax, s24),
                             ('load', s12, edi)]

def test_simple_stacklocs_no_free_reg():
    assembler = MockAssembler()
    s8 = mem(ebp, -8)
    s12 = mem(ebp, -12)
    s20 = mem(ebp, -20)
    s24 = mem(ebp, -24)
    remap_stack_layout(assembler, [s8, ebx, s12], [s20, s24, edi], [])
    assert assembler.ops == [('push', eax),
                             ('load', s8, eax),
                             ('store', eax, s20),
                             ('store', ebx, s24),
                             ('load', s12, edi),
                             ('pop', eax)]

def test_simple_stacklocs_no_free_reg_2():
    assembler = MockAssembler()
    s8 = mem(ebp, -8)
    s12 = mem(ebp, -12)
    s20 = mem(ebp, -20)
    s24 = mem(ebp, -24)
    p0 = mem(esp, 0)
    remap_stack_layout(assembler, [s8, eax, s12], [s20, s24, edi], [])
    assert assembler.got([('push', eax),
                          ('load', s8, eax),
                          ('store', eax, s20),
                          ('load', p0, eax),
                          ('store', eax, s24),
                          ('load', s12, edi),
                          ('pop', eax)])
