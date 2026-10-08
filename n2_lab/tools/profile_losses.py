"""Explain all manual losses with independent dynamic-PC counts.

Totals must agree with each actual Ripes ISS run. Function attribution is by
linked symbol interval, not a claim that the two compilers inline alike.
"""
import bisect,csv,hashlib,json,re
from build import ROOT,PREFIX,run
from measure_cases import patched,symbol_offsets
from rv32_trace import CPU

def main():
    cases={}
    for r in csv.DictReader((ROOT/'evidence/d11_per_case.csv').open()):cases.setdefault(r['dense'],{})[r['implementation']]=r
    losses=[(n,p) for n,p in cases.items() if int(p['solver_cli']['iret'])>int(p['gcc_reference']['iret'])]
    assert len(losses)==16
    bases={n:(ROOT/'build'/f'{n}.elf').read_bytes() for n in ('solver_cli','gcc_reference')}
    maps={}
    for n in bases:
        parsed=[]
        for line in run([PREFIX+'nm.exe','-n',ROOT/'build'/f'{n}.elf']).splitlines():
            m=re.fullmatch(r'([0-9a-f]+) [Tt] (.+)',line)
            if m:parsed.append((int(m[1],16),m[2]))
        # When several aliases share a PC, keep the last (function) label.
        unique=dict(parsed);maps[n]=sorted(unique.items())
    output=[]
    for dense,pair in losses:
        item=dict(dense=int(dense),input=pair['solver_cli']['input'],implementations={})
        for n in bases:
            source=patched(bases[n],symbol_offsets(bases[n]),pair[n]['input'],11);cpu=CPU(source)
            while cpu.exit is None:cpu.step()
            assert cpu.exit==0 and 'PASS cases=1' in cpu.output
            # The pinned ISS counter reports one more than decoded execution
            # through exit. This is an observed finalization offset, not an
            # invented instruction assigned to any solver function.
            assert cpu.iret+1==int(pair[n]['iret'])
            bounds=maps[n];addresses=[a for a,b in bounds];counts={}
            for pc,c in cpu.pcs.items():
                name=bounds[bisect.bisect_right(addresses,pc)-1][1];counts[name]=counts.get(name,0)+c
            item['implementations'][n]=dict(iret=int(pair[n]['iret']),decoded_execution_count=cpu.iret,
                                            ripes_counter_offset=1,by_symbol_interval=counts)
        item['excess']=item['implementations']['solver_cli']['iret']-item['implementations']['gcc_reference']['iret']
        output.append(item)
    (ROOT/'evidence/loss_profiles.json').write_text(json.dumps(dict(scope=__doc__,source_sha256={n:hashlib.sha256(b).hexdigest() for n,b in bases.items()},cases=output),indent=2)+'\n')
    print('PASS all 16 profiles agree exactly with actual Ripes ISS counts')
if __name__=='__main__':main()
