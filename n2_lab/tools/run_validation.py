"""Run representative T7 cases and the shared-code pipeline microscope."""
import concurrent.futures,json,struct
from pathlib import Path
from build import ROOT,GCC,SOURCES,run as shell,elf_sections,PREFIX
from run_ripes import run
from measure_cases import symbol_offsets,patched
def main():
    base=(ROOT/'build/solver_cli.elf').read_bytes();offsets=symbol_offsets(base)
    vectors=json.loads((ROOT/'evidence/test_vectors.json').read_text())
    jobs=[]
    for i,v in enumerate(vectors):
        f=ROOT/'build'/f'vector_{i:02}.elf';f.write_bytes(patched(base,offsets,v['input'],v['depth']))
        for model in ('RV32_ISS','RV32_5S'):jobs.append((i,v,f,model))
    def one(job):
        i,v,f,m=job;d=run(f,m,f'vector_{i:02}_{m}');assert d['pass_cases']==1
        return dict(**v,model=m,iret=d['# instructions retired'],cycles=d['cycles'],cpi=d['CPI'],exit=d['program_exit_code'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,jobs))
    (ROOT/'evidence/t7_matrix.json').write_text(json.dumps(rows,indent=2)+'\n')
    for name,cases in [('vectors',32)]:
        d=run(ROOT/'build'/f'{name}.elf',name=name+'_final_iss');assert d['pass_cases']==cases
    elf=ROOT/'build/pipeline_demo.elf'
    from build_pipeline import build_pipeline
    build_pipeline()
    for m in ('RV32_ISS','RV32_5S'):
        d=run(elf,m,'pipeline_'+m,extra=['--pipeline','--regs']);assert d['program_exit_code']==0
    print('PASS 32 cases x 2 processor models; batches; shared-code pipeline trace')
if __name__=='__main__':main()
