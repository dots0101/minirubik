"""Measure every d=11 case independently in the actual Ripes CLI.

Only input_string and expected_depth bytes are patched in linked ELF files.
No instruction, lookup table, or processor setting is changed between cases.
"""
import argparse, concurrent.futures, csv, json, statistics, struct, subprocess, time
from pathlib import Path
from generate_vectors import ROOT, state_from_dense, upstream_string
from run_ripes import RIPES

def symbol_offsets(data):
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
    sections=[struct.unpack_from('<10I',data,h[6]+i*h[11]) for i in range(h[12])]
    result={}
    for sec in sections:
        if sec[1]!=2: continue
        ss=sections[sec[6]]; strings=data[ss[4]:ss[4]+ss[5]]
        for off in range(sec[4],sec[4]+sec[5],16):
            name,value,size,info,other,idx=struct.unpack_from('<IIIBBH',data,off)
            if 0<idx<len(sections):
                s=sections[idx]; result[strings[name:].split(b'\0')[0].decode()]=s[4]+value-s[3]
    return result

def patched(data,offsets,cube,depth):
    out=bytearray(data); k=offsets['input_string'];out[k:k+15]=cube.encode()+b'\0'
    out[offsets['expected_depth']]=depth
    return out

def main(workers=6):
    scratch=ROOT/'build/case_measurements'; scratch.mkdir(parents=True,exist_ok=True)
    dist=(ROOT/'reference/host_oracle/full_distance.bin').read_bytes()
    records=[]
    for n,d in enumerate(dist):
        if d==11:
            p,o=state_from_dense(n); records.append((n,upstream_string(p,o),d))
    assert len(records)==2644
    bases={name:(ROOT/'build'/f'{name}.elf').read_bytes() for name in ('solver_cli','gcc_reference')}
    offsets={name:symbol_offsets(data) for name,data in bases.items()}
    def one(task):
        i,(n,cube,depth),name=task
        source=scratch/f'{name}_{i}.elf'; report=source.with_suffix('.json')
        source.write_bytes(patched(bases[name],offsets[name],cube,depth))
        cmd=[str(RIPES),'--mode','cli','--src',str(source),'-t','elf','--proc','RV32_ISS','--iret','--cycles','--exectime','--json','--output',str(report),'--timeout','10000']
        r=subprocess.run(cmd,capture_output=True,timeout=40)
        stdout=r.stdout.decode(errors='replace').replace('\0','')
        assert r.returncode==0 and 'PASS cases=1' in stdout and 'Program exited with code: 0' in stdout,(cube,name,stdout,r.stderr)
        metrics=json.loads(report.read_text());source.unlink();report.unlink()
        return dict(dense=n,input=cube,depth=depth,implementation=name,iret=metrics['# instructions retired'],cycles=metrics['cycles'],execution_ms=metrics['execution time (ms)'])
    tasks=[(i,r,name) for i,r in enumerate(records) for name in bases]
    start=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        rows=[]
        for r in pool.map(one,tasks):
            rows.append(r)
            if len(rows)%500==0: print('completed',len(rows),'of',len(tasks),flush=True)
    with (ROOT/'evidence/d11_per_case.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={}
    for name in bases:
        vals=[r['iret'] for r in rows if r['implementation']==name]
        summary[name]=dict(cases=len(vals),min=min(vals),mean=statistics.mean(vals),max=max(vals),total=sum(vals),all_below_50m=all(v<50000000 for v in vals),pass_cases=len(vals))
    own=[r for r in rows if r['implementation']=='solver_cli'];ref=[r for r in rows if r['implementation']=='gcc_reference']
    assert all(a['input']==b['input'] for a,b in zip(own,ref))
    summary['manual_wins']=sum(a['iret']<b['iret'] for a,b in zip(own,ref))
    summary['manual_ties']=sum(a['iret']==b['iret'] for a,b in zip(own,ref))
    summary['wall_seconds']=time.perf_counter()-start
    summary['scope']='Full program: parse, solve, replay, print and exit. Renderer disabled. Independent process per state.'
    (ROOT/'evidence/d11_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=6);a=p.parse_args();main(a.workers)
