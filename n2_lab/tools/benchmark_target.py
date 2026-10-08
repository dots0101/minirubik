"""Isolated RV32I packing and bounded-modulo experiments, outside the solver."""
import json,re
from build import ROOT,GCC,PREFIX,run,elf_sections
from run_ripes import run as simulate

def program(body,expected,count,extra=''):
    return f'''.option norvc
.option norelax
.text
.globl _start
_start:
    li s0,0
    li s1,{count}
    li s2,0
loop:
{body}
    add s2,s2,a0
    addi s0,s0,1
    addi s1,s1,-1
    bnez s1,loop
    li t0,{expected}
    bne s2,t0,fail
    li a0,0
    li a7,93
    ecall
fail:
    li a0,1
    li a7,93
    ecall
{extra}
'''

def main():
    out={}
    count=5000
    # Identical input generator: 0,1,2,3,4 repeatedly, with no division.
    generator='''    mv t3,s0
    li t2,5
    bltu t3,t2,input_ready
    li s0,0
    li t3,0
input_ready:'''
    branch=generator+'''\n    mv a0,t3
    addi t0,a0,-3
    bltz t0,reduced
    mv a0,t0
reduced:'''
    branchless=generator+'''\n    addi t0,t3,-3
    srai t1,t0,31
    andi t1,t1,3
    add a0,t0,t1'''
    specs={'mod3_branch':program(branch,4000,count),'mod3_branchless':program(branchless,4000,count)}
    txt=(ROOT/'reference/h48_policy_data.c').read_text()
    body=re.search(r'h48_policy_dense\[38901\]\s*=\s*\{(.*?)\};',txt,re.S)[1]
    packed=bytes(int(v,0) for v in re.findall(r'0x[\da-fA-F]+|\d+',body))
    raw=bytes((packed[i>>1]>>((i&1)*4))&15 for i in range(77802))
    expected=sum(raw)
    for name,data in [('packed',packed),('byte',raw)]:
        path=ROOT/'build'/f'bench_{name}.bin';path.write_bytes(data)
        extra=f'.section .rodata\n.balign 4\nlookup_data:\n.incbin "{path.as_posix()}"'
        access=('    srli t0,s0,1\n' if name=='packed' else '    mv t0,s0\n')
        access+='    la t1,lookup_data\n    add t0,t0,t1\n    lbu a0,0(t0)'
        if name=='packed':access+='\n    andi t1,s0,1\n    slli t1,t1,2\n    srl a0,a0,t1\n    andi a0,a0,15'
        specs['dense_'+name]=program(access,expected,77802,extra)
    for name,source in specs.items():
        path=ROOT/'build'/f'bench_{name}.S';path.write_text(source)
        elf=path.with_suffix('.elf')
        run([GCC,'-march=rv32i','-mabi=ilp32','-mno-relax','-nostdlib','-nostartfiles','-Wl,--no-relax','-Wl,-Ttext=0x1000',path,'-o',elf])
        out[name]={'sections':elf_sections(elf),'models':{}}
        for model in ('RV32_ISS','RV32_5S'):
            d=simulate(elf,model,'bench_'+name+'_'+model)
            assert d['program_exit_code']==0
            out[name]['models'][model]={k:d[k] for k in ('# instructions retired','cycles','program_exit_code')}
    out['scope']='Isolated kernels including a shared driver and checksum assertion. Every value 0..4 repeats 1000 times for mod3; every dense entry is read once for packing. These are not whole-solver speed claims. No kernel or byte-expanded table is linked into solver_cli or solver_gui.'
    (ROOT/'evidence/target_microbenchmarks.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
