import argparse, json, os, re, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RIPES=Path(os.environ.get('N2_RIPES',ROOT.parents[1]/'work/toolchains/Ripes/Ripes.exe'))
def run(source,model='RV32_ISS',name=None,timeout=120000,kind=None,extra=()):
    source=Path(source).resolve();name=name or source.stem+'_'+model
    output=ROOT/'evidence'/(name+'.json');log=output.with_suffix('.log')
    output.unlink(missing_ok=True)
    cmd=[str(RIPES),'--mode','cli','--src',str(source),'-t',kind or ('elf' if source.suffix=='.elf' else 'asm'),'--proc',model,'--iret','--cycles','--cpi','--exectime','--runinfo','--json','--output',str(output),'--timeout',str(timeout),*extra]
    start=time.perf_counter();proc=subprocess.run(cmd,capture_output=True,timeout=timeout/1000+30)
    stdout=proc.stdout.decode(errors='replace').replace('\0','');stderr=proc.stderr.decode(errors='replace')
    log.write_text('COMMAND '+subprocess.list2cmdline(cmd)+'\n'+stdout+'\n'+stderr,encoding='utf-8')
    if not output.exists(): raise RuntimeError(name+' missing report: '+stdout+stderr)
    data=json.loads(output.read_text());data['wall_seconds']=time.perf_counter()-start;data['source_type']=kind or source.suffix[1:];data['model']=model;data['process_returncode']=proc.returncode
    data['program_exit_code']=int(re.search(r'Program exited with code:\s*(\d+)',stdout)[1]) if 'Program exited with code:' in stdout else None
    data['pass_cases']=int(re.search(r'PASS cases=(\d+)',stdout)[1]) if 'PASS cases=' in stdout else None
    if proc.returncode or 'ERROR:' in stderr or 'ERROR:' in stdout or data['program_exit_code'] not in (0,None): raise RuntimeError(name+' failed: '+stdout+stderr)
    output.write_text(json.dumps(data,indent=2)+'\n');return data
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--model',default='RV32_ISS');p.add_argument('--name');p.add_argument('--timeout',type=int,default=120000);a=p.parse_args()
    print(json.dumps(run(a.source,a.model,a.name,a.timeout)))
