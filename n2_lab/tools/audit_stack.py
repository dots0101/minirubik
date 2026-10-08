"""Conservative stack bound from the actual linked direct-call graph."""
import json,re
from build import ROOT,elf_sections
def one(name):
    text=(ROOT/'build'/f'{name}.disasm').read_text();functions={};current=None
    for line in text.splitlines():
        m=re.match(r'^[\da-f]+ <([^>]+)>:',line)
        if m:current=m[1];functions[current]=dict(frame=0,calls=[]);continue
        if current is None:continue
        # la sp expands into auipc+addi and is initialization, not a frame.
        if current not in ('_start','__image_start'):
            m=re.search(r'addi\s+sp,sp,-(\d+)',line)
            if m:functions[current]['frame']=max(functions[current]['frame'],int(m[1]))
        if re.search(r'\bjalr\b',line) and '(ra)' in line:
            m=re.search(r'#\s+[\da-f]+ <([^>]+)>',line)
            assert m,(name,line)
            callee=m[1].split('+')[0]
            if callee not in functions[current]['calls']:functions[current]['calls'].append(callee)
    def bound(fn,seen):
        assert fn not in seen,(name,'recursive call',fn)
        d=functions[fn];children=[bound(c,seen+[fn]) for c in d['calls']]
        best=max(children,key=lambda x:x[0]) if children else (0,[])
        return d['frame']+best[0],[fn]+best[1]
    values={fn:bound(fn,[]) for fn in functions}
    root='_start' if '_start' in functions else '__image_start'
    peak,path=values[root];reserve=elf_sections(ROOT/'build'/f'{name}.elf')['.stack']
    assert reserve>=peak,(name,peak,reserve,path)
    return dict(conservative_call_graph_bound=peak,reserved_bytes=reserve,deepest_path=path,functions=functions,
                scope='Fixed frame direct-call DAG; no recursion or variable frames. All branch paths conservatively included.')
if __name__=='__main__':
    records={n:one(n) for n in ('solver_cli','solver_gui','gcc_reference','pipeline_demo')}
    (ROOT/'evidence/stack_bounds.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({n:{k:v for k,v in r.items() if k!='functions'} for n,r in records.items()},indent=2))
