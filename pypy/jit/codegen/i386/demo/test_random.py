import py
from pypy.rlib.rarithmetic import intmask
from pypy.jit.codegen.i386.demo.support import rundemo, Random, udir
from pypy.jit.codegen.i386.demo import conftest as demo_conftest


def test_random_function(nb_blocks=15, max_block_length=20):
    #py.test.skip("in-progress")
    blocklabels = range(nb_blocks)
    r = Random()
    vars = list("abcdefghijklmnopqrstuvwxyz")
    varlist = ', '.join(vars)
    magicsum = '+'.join(['%s*%d' % (v, hash(v)) for v in vars])
    operations = ['%s + %s',
                  '%s + %s',
                  '%s - %s',
                  '%s - %s',
                  '%s * %s',
                  '%s & %s',
                  '%s | %s',
                  '%s ^ %s',
                  '%s << (%s & 0x0000067f)',
                  '%s >> (%s & 0x1234567f)',
                  'abs(%s)',
                  '-%s',
                  '~%s',
                  '%s // ((%s & 0xfffff) + 1)',
                  '%s // (-((%s & 0xfffff) + 1))',
                  '%s %% ((%s & 0xfffff) + 1)',
                  '%s %% (-((%s & 0xfffff) + 1))',
                  '!%s or %s',
                  '!%s and %s',
                  '!not %s',
                  '!bool(%s)',
                  '!%s <  %s',
                  '!%s <= %s',
                  '!%s == %s',
                  '!%s != %s',
                  '!%s >  %s',
                  '!%s >= %s',
                  ]
    lines = ["def dummyfn(counter, %(varlist)s):" % locals(),
             "  goto = 0",
             "  while True:",
             ]
    for blocklabel in blocklabels:
        lines.append("    if goto == %d:" % blocklabel)
        for j in range(r.randrange(0, max_block_length)):
            v1 = r.choice(vars)
            constbytes = r.randrange(-15, 5)
            if constbytes <= 0:
                v2 = r.choice(vars)
                op = r.choice(operations)
                if op.count('%s') == 1:
                    op = op % (v2,)
                else:
                    v3 = r.choice(vars)
                    op = op % (v2, v3)
                if op.startswith('!'):
                    op = op[1:]
                else:
                    op = 'intmask(%s)' % op
                lines.append("      %s = %s" % (v1, op))
            else:
                constant = r.randrange(-128, 128)
                for i in range(1, constbytes):
                    constant = constant << 8 | r.randrange(0, 256)
                lines.append("      %s = %d" % (v1, constant))
        v1 = r.choice(vars)
        for line in ["      if %s:" % v1,
                     "      else:"]:
            lines.append(line)
            j = r.choice(blocklabels)
            if j <= blocklabel:
                lines.append("        counter -= 1")
                lines.append("        if not counter: break")
            lines.append("        goto = %d" % j)
    lines.append("  return intmask(%(magicsum)s)" % locals())

    args = [r.randrange(-99, 100) for v1 in vars]

    src = py.code.Source('\n'.join(lines))
    print src
    udir.join('generated.py').write(
        'from pypy.rlib.rarithmetic import intmask\n\n'
        '%s\n\n'
        'args=%r\n'
        'print dummyfn(10000, *args)\n' % (src, args))
    exec src.compile()

    rundemo(dummyfn, 10000, *args)
