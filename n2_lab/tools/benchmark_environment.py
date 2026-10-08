"""Actual guest-memory and processor-throughput measurements in pinned Ripes.

PeakWorkingSetSize is a Windows process measurement, not guest memory capacity.
Guest words are explicitly touched by sw, in a fixed bounded RV32I loop.
"""
import ctypes,json,os,platform,statistics,subprocess,time
from pathlib import Path
from build import ROOT,GCC
from run_ripes import RIPES
class Counters(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),*[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]]
psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
def bench(size,passes,model,rep):
    tag=f'memory_{size}_{passes}_{model}_{rep}';src=ROOT/'build'/f'{tag}.S';elf=src.with_suffix('.elf');report=ROOT/'evidence'/f'{tag}.json'
    src.write_text(f'''.option norvc
.option norelax
.text
.globl _start
_start:
    li s0, {passes}
    li s1, {size//4}
    beqz s1, done
outer:
    li t0, 0x20000000
    mv t1, s1
loop:
    sw t1, 0(t0)
    lw t2, 0(t0)
    addi t0, t0, 4
    addi t1, t1, -1
    bnez t1, loop
    addi s0, s0, -1
    bnez s0, outer
done:
    li a0, 0
    li a7, 93
    ecall
''')
    subprocess.run([str(GCC),'-march=rv32i','-mabi=ilp32','-nostdlib','-Wl,--no-relax',f'-Wl,-T,{ROOT/"target/rv32.ld"}',str(src),'-o',str(elf)],check=True,capture_output=True)
    cmd=[str(RIPES),'--mode','cli','--src',str(elf),'-t','elf','--proc',model,'--iret','--cycles','--exectime','--json','--output',str(report),'--timeout','120000']
    start=time.perf_counter();proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);peak=0;counter=Counters();counter.cb=ctypes.sizeof(counter)
    while proc.poll() is None:
        if psapi.GetProcessMemoryInfo(int(proc._handle),ctypes.byref(counter),counter.cb):peak=max(peak,counter.PeakWorkingSetSize)
        time.sleep(.002)
    out,err=proc.communicate();assert proc.returncode==0 and b'Program exited with code: 0' in out,(out,err)
    metrics=json.loads(report.read_text());metrics.update(guest_bytes_touched=size,passes=passes,peak_working_set_bytes=peak,model=model,rep=rep,wall_seconds=time.perf_counter()-start)
    report.write_text(json.dumps(metrics,indent=2)+'\n');return metrics
def main():
    rows=[]
    for size in (0,4096,131072,1048576,4194304):
        for rep in range(3):rows.append(bench(size,1,'RV32_ISS',rep))
        print('memory',size,flush=True)
    for model in ('RV32_ISS','RV32_5S'):
        for rep in range(3):rows.append(bench(131072,8,model,rep))
        print('throughput',model,flush=True)
    summary=dict(platform=platform.platform(),cpu=os.environ.get('PROCESSOR_IDENTIFIER'),logical_cpus=os.cpu_count(),rows=rows,memory=[],throughput=[])
    baseline=statistics.median(r['peak_working_set_bytes'] for r in rows if r['guest_bytes_touched']==0)
    for size in (0,4096,131072,1048576,4194304):
        group=[r for r in rows if r['guest_bytes_touched']==size and r['passes']==1]
        median=statistics.median(r['peak_working_set_bytes'] for r in group)
        summary['memory'].append(dict(guest_bytes=size,median_peak_bytes=median,delta_from_control_bytes=median-baseline,repeats=3))
    for model in ('RV32_ISS','RV32_5S'):
        group=[r for r in rows if r['passes']==8 and r['model']==model]
        rates=[r['# instructions retired']/(r['execution time (ms)']/1000) for r in group]
        summary['throughput'].append(dict(model=model,median_retired_per_second=statistics.median(rates),iret=group[0]['# instructions retired'],cycles=group[0]['cycles'],repeats=3))
    (ROOT/'evidence/environment_benchmark.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('memory','throughput')},indent=2))
if __name__=='__main__':main()
