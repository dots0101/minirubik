"""Host-only packed/byte lookup benchmark with identical query sequences."""
import json,os,re,statistics,subprocess
from pathlib import Path
from build import ROOT

def main():
    compiler=Path(os.environ.get('N2_HOST_CC','C:/msys64/ucrt64/bin/gcc.exe'))
    exe=ROOT/'build/host/bench_packing.exe'; exe.parent.mkdir(exist_ok=True)
    subprocess.run([str(compiler),'-O3','-std=c11','-Wall','-Wextra','-Werror',f'-I{ROOT/"reference"}',str(ROOT/'host_tools/bench_packing.c'),str(ROOT/'reference/h48_policy_data.c'),'-o',str(exe)],check=True,capture_output=True)
    result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
    (ROOT/'evidence/packing_benchmark.txt').write_text(result.stdout)
    rows=[]
    for line in result.stdout.splitlines():
        if line.startswith('rep='):
            fields=dict(re.findall(r'(\w+)=([\d.]+)',line))
            rows.append({k:float(v) if 'seconds' in k else int(v) for k,v in fields.items()})
    assert len(rows)==5 and 'PASS entries=77802' in result.stdout
    summary=dict(scope='Host-only microbenchmark; clock() timer; not Ripes whole-solver performance',rows=rows,
                 packed_median_seconds=statistics.median(r['packed_seconds'] for r in rows),
                 byte_median_seconds=statistics.median(r['byte_seconds'] for r in rows))
    (ROOT/'evidence/packing_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(result.stdout)
if __name__=='__main__': main()
