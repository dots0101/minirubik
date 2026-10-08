import hashlib,json,re
from build import ROOT,GCC,SOURCES,PREFIX,run,expand_macros,single_sections,table_source,elf_sections
def build_pipeline():
    source=(ROOT/'target/solver_rv32.S').read_text()
    excerpt=source[source.index('policy_lookup:\n'):source.index('work_solved:\n')]
    excerpt+=source[source.index('popcount32:\n'):source.index('mask_rank:\n')]
    (ROOT/'build/policy_excerpt.S').write_text(excerpt)
    elf=ROOT/'build/pipeline_demo.elf'
    run([GCC,'-march=rv32i','-mabi=ilp32','-mno-relax','-O2','-nostdlib','-nostartfiles','-Wl,--no-relax','-Wl,--defsym,__stack_reserve=32',f'-Wl,-T,{ROOT/"target/rv32.ld"}',f'-I{ROOT/"build"}',ROOT/'target/pipeline_demo.S',ROOT/'reference/h48_policy_data.c','-o',elf])
    (ROOT/'build/pipeline_demo.disasm').write_text(run([PREFIX+'objdump.exe','-d',elf]))
    flat=(ROOT/'target/pipeline_demo.S').read_text().replace('.include "policy_excerpt.S"',excerpt)
    policy_names={'h48_policy_disp','h48_policy_used','h48_policy_prefix','h48_policy_dense'}
    (ROOT/'build/pipeline_demo.s').write_text(single_sections(expand_macros(flat)+table_source(policy_names)))
    (ROOT/'evidence/pipeline_source.json').write_text(json.dumps(dict(excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),source='target/solver_rv32.S',function='policy_lookup',exact_source_slice=True,**elf_sections(elf)),indent=2)+'\n')
if __name__=='__main__':build_pipeline()
