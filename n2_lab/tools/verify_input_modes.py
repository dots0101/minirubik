"""Exercise the unknown-distance input contract on actual Ripes models."""
import hashlib,json
from build import ROOT
from measure_cases import symbol_offsets,patched
from run_ripes import run

def main():
    selected=[r for r in json.loads((ROOT/'evidence/test_vectors.json').read_text())
              if r['role'] in ('distance-0','distance-6','official')]
    assert len(selected)==3
    records=[]
    for name in ('solver_cli','gcc_reference'):
        elf=ROOT/'build'/f'{name}.elf';data=elf.read_bytes();offsets=symbol_offsets(data)
        for row in selected:
            source=ROOT/'build'/f'unknown_{name}_{row["depth"]}.elf'
            source.write_bytes(patched(data,offsets,row['input'],255))
            for model in ('RV32_ISS','RV32_5S'):
                report=run(source,model,source.stem+'_'+model)
                assert report['pass_cases']==1 and report['program_exit_code']==0
                records.append(dict(implementation=name,input=row['input'],oracle_depth=row['depth'],
                                    expected_byte=255,source_sha256=hashlib.sha256(data).hexdigest(),**report))
            source.unlink()
    for name,out in [('solver_cli','official_final_iss'),('gcc_reference','gcc_official_final_iss')]:
        report=run(ROOT/'build'/f'{name}.elf','RV32_ISS',out)
        assert report['pass_cases']==1 and report['program_exit_code']==0
    gui=run(ROOT/'build/solver_gui.elf','RV32_5S','gui_final_5s_cli')
    assert gui['pass_cases']==1 and gui['program_exit_code']==0
    payload=dict(scope='Unknown EXPECTED=255 on two implementations and two models; oracle lengths shown for context. Driver checks replay and <=11, not equality to an unknown distance.',
                 records=records,renderer_cli_check=dict(scope='ELF renderer writes are executed by CLI RAM; no GUI peripheral is instantiated.',**gui))
    (ROOT/'evidence/unknown_input_mode.json').write_text(json.dumps(payload,indent=2)+'\n')
    print('PASS 12 unknown-distance runs, fresh official pair, and renderer 5S CLI')

if __name__=='__main__':main()
