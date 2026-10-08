"""Build GNU ELF programs and flat Ripes assembly from the same authored source."""
import argparse, json, os, re, subprocess, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parents[1]/'work'
GCC=Path(os.environ.get('N2_RV_GCC',WORK/'toolchains/gcc/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-gcc.exe'))
PREFIX=str(GCC).replace('gcc.exe','')
SOURCES=['n2_core_data.c','h48_policy_data.c','h48_t_simple_data.c','h48_s3_base.c','h48_sigma_pr_data.c']
BUILD=ROOT/'build'; BUILD.mkdir(exist_ok=True)
def run(cmd):
    r=subprocess.run([str(x) for x in cmd],capture_output=True,text=True)
    if r.returncode: raise RuntimeError(' '.join(map(str,cmd))+'\n'+r.stdout+r.stderr)
    return r.stdout
def preprocess(path,defs):
    return run([GCC,'-E','-P','-x','assembler-with-cpp',*[f'-D{k}={v}' for k,v in defs.items()],path])
def expand_macros(text):
    macros={}
    def register(m):
        name=m[1]; args=[x.strip() for x in m[2].split(',')]; macros[name]=(args,m[3]); return ''
    text=re.sub(r'^\.macro\s+(\w+)\s+([^\n]+)\n(.*?)^\.endm\s*$',register,text,flags=re.M|re.S)
    lines=[]
    for line in text.splitlines():
        fields=line.strip().split(None,1)
        if fields and fields[0] in macros:
            names,body=macros[fields[0]]; values=[x.strip() for x in fields[1].split(',')]
            for n,v in zip(names,values): body=body.replace('\\'+n,v)
            lines.extend(body.splitlines())
        else: lines.append(line)
    # Evaluate constant assembler .if in expanded macros.
    out=[]; stack=[]; active=True
    for line in lines:
        s=line.strip()
        if s.startswith('.if '):
            truth=bool(eval(s[4:],{'__builtins__':{}},{})); stack.append([active,truth]); active=active and truth
        elif s.startswith('.elseif '):
            parent,taken=stack[-1]; truth=bool(eval(s[8:],{'__builtins__':{}},{})); active=parent and not taken and truth; stack[-1][1]|=truth
        elif s=='.else': parent,taken=stack[-1]; active=parent and not taken; stack[-1][1]=True
        elif s=='.endif': active=stack.pop()[0]
        elif active: out.append(line)
    text='\n'.join(out)+'\n'
    text=re.sub(r'^\.option.*\n','',text,flags=re.M)
    text=text.replace('.section .rodata','.data').replace('.section .bss','.data')
    text=re.sub(r'\.balign\s+4', '.align 2',text)
    text=re.sub(r'\.balign\s+2', '.align 1',text)
    # Ripes uses .string rather than .asciz.
    text=re.sub(r'\.space\s+(\d+)',lambda m:'.byte '+','.join(['0']*int(m[1])),text)
    return text.replace('.asciz','.string')
def single_sections(text):
    sections={'.text':[],'.data':[]}; current='.text'
    for line in text.splitlines():
        if line.strip() in sections: current=line.strip()
        else: sections[current].append(line)
    return '\n'.join(['.text',*sections['.text'],'.data',*sections['.data']])+'\n'
def table_source(names=None):
    chunks=['.data']
    for fn in SOURCES:
        txt=(ROOT/'reference'/fn).read_text()
        for m in re.finditer(r'const\s+(uint(?:8|16|32)_t)\s+(\w+)\s*(?:\[[^\]]*\])+\s*=\s*\{(.*?)\};',txt,re.S):
            kind,name,body=m.groups(); body=re.sub(r'/\*.*?\*/','',body,flags=re.S)
            if names is not None and name not in names: continue
            vals=re.findall(r'0x[0-9a-fA-F]+|\d+',body)
            directive={'uint8_t':'.byte','uint16_t':'.half','uint32_t':'.word'}[kind]
            chunks.extend(['.align 2',name+':'])
            for i in range(0,len(vals),16): chunks.append(directive+' '+','.join(vals[i:i+16]))
    return '\n'.join(chunks)+'\n'
def elf_sections(path):
    data=path.read_bytes(); hdr=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
    off,size,count,names=hdr[6],hdr[11],hdr[12],hdr[13]
    entries=[struct.unpack_from('<10I',data,off+i*size) for i in range(count)]
    ns=entries[names]; pool=data[ns[4]:ns[4]+ns[5]]
    result={}; static_data=0; allocated=[]
    for e in entries:
        name=pool[e[0]:].split(b'\0')[0].decode()
        if name in ('.text','.rodata','.data','.bss') or e[2]&2: result[name]=e[5]
        # Count every allocated non-executable section, including any orphan
        # small-data section introduced by future source/compiler changes.
        if e[2]&2 and not e[2]&4: static_data+=e[5]
        if e[2]&2 and e[5]: allocated.append((e[3],e[3]+e[5]))
    result['static_data']=static_data
    result['allocated_image_bytes']=max(b for a,b in allocated)-min(a for a,b in allocated)
    result['section_bytes']=sum(b-a for a,b in allocated)
    result['alignment_gap_bytes']=result['allocated_image_bytes']-result['section_bytes']
    result['course_static_data']=sum(result.get(k,0) for k in ('.rodata','.data','.bss'))
    return result
def build(name,mode=0,renderer=0,expected=11,reference=False):
    defs=dict(MODE=mode,RENDER=renderer,EXPECTED=expected,TEST_VECTOR_COUNT=32)
    runtime=BUILD/(name+'_runtime.S'); runtime.write_text(preprocess(ROOT/'target/runtime.S',defs))
    if renderer:
        # GNU ELF binds the named I/O exports to the verified device configuration.
        runtime.write_text('.equ LED_MATRIX_0_BASE,0xf0000000\n.equ LED_MATRIX_0_WIDTH,35\n.equ LED_MATRIX_0_HEIGHT,25\n'+runtime.read_text())
    flags=['-march=rv32i','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-Wall','-Wextra','-Werror',f'-I{ROOT / "reference"}',f'-Wl,-T,{ROOT / "target/rv32.ld"}','-Wl,--no-relax',f'-Wl,-Map,{BUILD / (name+".map")}']
    flags.append('-Wl,--defsym,__stack_reserve='+str(512 if reference else 400))
    core=ROOT/'reference/n2_solver.c' if reference else ROOT/'target/solver_rv32.S'
    elf=BUILD/(name+'.elf')
    files=[runtime,core,*[ROOT/'reference'/f for f in SOURCES]]
    if mode==2: files.append(ROOT/'target/test_vectors.S')
    run([GCC,*flags,*files,'-o',elf])
    (BUILD/(name+'.disasm')).write_text(run([PREFIX+'objdump.exe','-d',elf]))
    (BUILD/(name+'.sections.txt')).write_text(run([PREFIX+'size.exe','-A',elf]))
    if not reference:
        gui_defs=dict(defs)
        if renderer:
            # GUI exported values were verified in the I/O panel. The pinned
            # GUI assembler misresolved external I/O symbols in our tests.
            # Resolve these platform bindings before exporting the flat file;
            # the authored runtime retains all three symbolic export names.
            gui_defs.update(LED_MATRIX_0_BASE='0xf0000000',LED_MATRIX_0_WIDTH=35,LED_MATRIX_0_HEIGHT=25)
        flat=expand_macros(preprocess(ROOT/'target/runtime.S',gui_defs)+'\n'+preprocess(ROOT/'target/solver_rv32.S',defs))+table_source()
        if mode==2: flat+=(ROOT/'target/test_vectors.S').read_text().replace('.section .rodata','.data')
        note='/* Inspection export from authored GNU sources.\n * Direct Ripes assembly is not a verified execution route; load the GNU-built ELF.\n * GUI device bindings: BASE=0xf0000000, WIDTH=35, HEIGHT=25. */\n'
        (BUILD/(name+'.s')).write_text(note+single_sections(flat))
    info=elf_sections(elf); info['reference']=reference
    info['total_guest_with_led_reservation']=info['allocated_image_bytes']+3500
    if info['total_guest_with_led_reservation']>131072: raise RuntimeError(f'{name}: total budget exceeded: {info}')
    return info
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--name',default='solver_cli'); p.add_argument('--mode',type=int,default=0);p.add_argument('--render',type=int,default=0);p.add_argument('--expected',type=int,default=11);p.add_argument('--reference',action='store_true');a=p.parse_args()
    result=build(a.name,a.mode,a.render,a.expected,a.reference)
    (BUILD/(a.name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
