"""Rebuild host verification tools; keep actual logs and timing measurements."""
import json,os,struct,subprocess,time
from pathlib import Path
from build import ROOT,GCC,PREFIX,SOURCES,elf_sections
HOST=Path(os.environ.get('N2_HOST_CC','C:/msys64/ucrt64/bin/gcc.exe'))
CXX=Path(os.environ.get('N2_HOST_CXX','C:/msys64/ucrt64/bin/g++.exe'))
B=ROOT/'build/host';B.mkdir(exist_ok=True)
DATA=[ROOT/'reference'/x for x in SOURCES]
FLAGS=['-std=c11','-O3','-Wall','-Wextra','-Wpedantic','-Werror',f'-I{ROOT/"reference"}']
def run(cmd,name=None):
    t=time.perf_counter();r=subprocess.run([str(x) for x in cmd],capture_output=True)
    out=r.stdout.decode(errors='replace');err=r.stderr.decode(errors='replace')
    if name:
        (ROOT/'evidence'/f'{name}.txt').write_text(out,encoding='utf-8')
        if err:(ROOT/'evidence'/f'{name}_stderr.txt').write_text(err,encoding='utf-8')
    if r.returncode:raise RuntimeError(out+err)
    return out,time.perf_counter()-t
def buildhost(name,tool,core=True,flags=FLAGS):
    run([HOST,*flags,ROOT/tool,*([ROOT/'reference/n2_solver.c'] if core else []),*DATA,'-o',B/(name+'.exe')])
    return B/(name+'.exe')
def main():
    timings={}
    for name,tool,args,core,strict in [
      ('native_random','reference/test_n2_solver.c',[],True,True),
      ('host_full_domain','reference/test_full_domain.c',['0','3674160',ROOT/'reference/host_oracle/full_distance.bin'],True,True),
      ('adapter_test','host_tools/test_adapter.c',[],True,True),
      ('api_native','host_tools/test_api.c',[],True,True),
      ('distance_certificate','host_tools/check_distance_certificate.c',[ROOT/'reference/host_oracle/full_distance.bin'],False,False),
      ('structure','host_tools/verify_structure.c',[ROOT/'reference/host_oracle/full_distance.bin'],False,False),
      ('tables','host_tools/verify_tables.c',[],False,False),
      ('trace_examples','host_tools/trace_examples.c',[],False,False),
      ('packed_accessors','host_tools/verify_packed.c',[ROOT/'host_tools/unpacked_policy_slots.bin',ROOT/'host_tools/unpacked_sigma.bin'],False,True)]:
        flags=FLAGS if strict else ['-std=c11','-O3','-Wall','-Wextra','-Wno-misleading-indentation',f'-I{ROOT/"reference"}']
        exe=buildhost(name,tool,core,flags); out,t=run([exe,*args],name);timings[name]=t;print(name,round(t,4),out[-200:],flush=True)
    for name in ('verify_affine',):
        out,t=run([os.sys.executable,'-E','-B',ROOT/'host_tools'/f'{name}.py'],name);timings[name]=t;print(name,out[-200:],flush=True)
    run([HOST,'-O2','-c',ROOT/'reference/n2_core_data.c','-o',B/'core.o'])
    run([CXX,'-O2','-std=c++17',f'-I{ROOT/"reference"}',f'-I{ROOT/"host_tools"}',ROOT/'host_tools/rv32_verify.cpp',B/'core.o','-o',B/'rv32_verify.exe'])
    from measure_cases import symbol_offsets
    data=bytearray((ROOT/'build/solver_cli.elf').read_bytes());off=symbol_offsets(data)['n2_solve']
    # .text is the first loaded section; derive symbol VA using its ELF section header.
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
    sec=next(s for i in range(h[12]) if (s:=struct.unpack_from('<10I',data,h[6]+i*h[11]))[4]<=off<s[4]+s[5] and s[2]&4)
    struct.pack_into('<I',data,24,sec[3]+off-sec[4]);(B/'core_entry.elf').write_bytes(data)
    for suite in ('api','d11','stratified'):
        out,t=run([B/'rv32_verify.exe',B/'core_entry.elf',ROOT/'reference/host_oracle/full_distance.bin',suite,ROOT/'evidence'/f'rv32_abi_{suite}.csv'],f'rv32_abi_{suite}');timings['rv32_'+suite]=t;print(suite,out,flush=True)
    isa={}
    for name in ('solver_cli','gcc_reference','solver_gui'):
        f=ROOT/'build'/f'{name}.elf';data=f.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
        entries=[struct.unpack_from('<10I',data,h[6]+i*h[11]) for i in range(h[12])]
        violations=[];count=0
        for s in entries:
            if not s[2]&4:continue
            for i in range(s[4],s[4]+s[5],4):
                ins=struct.unpack_from('<I',data,i)[0];op=ins&127;f7=ins>>25
                if ins&3!=3 or op not in (0x37,0x17,0x6f,0x67,0x63,0x03,0x23,0x13,0x33,0x0f,0x73) or op==0x33 and f7 not in (0,0x20):violations.append(hex(ins))
                count+=1
        undefined,_=run([PREFIX+'nm.exe','-u',f]);assert not undefined.strip() and not violations
        isa[name]=dict(**elf_sections(f),instructions=count,non_rv32i=violations,undefined_symbols=undefined)
    (ROOT/'evidence/host_timings.json').write_text(json.dumps(timings,indent=2)+'\n')
    (ROOT/'evidence/isa_and_size.json').write_text(json.dumps(isa,indent=2)+'\n')
if __name__=='__main__':main()
