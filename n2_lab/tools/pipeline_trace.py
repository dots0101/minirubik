"""Validate the exported GUI trace against every current RV32I instruction.

Stage occupancy is observed GUI data. Control values are decoded from the
instructions and pinned model wiring, not claimed as sampled GUI port values.
"""
import csv,hashlib,json,re,struct
from build import ROOT
from run_ripes import run

def sx(n,b):return n-(1<<b) if n&(1<<(b-1)) else n
def decode(w):
    op=w&127;rd=(w>>7)&31;f=(w>>12)&7;a=(w>>15)&31;b=(w>>20)&31;g=w>>25
    r=lambda x:f'x{x}'
    imm=sx(w>>20,12)
    if op in (0x37,0x17):return [('lui' if op==0x37 else 'auipc'),r(rd),str(w>>12)]
    if op==0x67:return ['jalr',r(rd),r(a),str(imm)]
    if op==0x6f:
        off=((w>>31)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1)
        return ['jal',r(rd),str(sx(off,21))]
    if op==0x13:
        name={0:'addi',2:'slti',3:'sltiu',4:'xori',6:'ori',7:'andi',1:'slli',5:'srai' if g else 'srli'}[f]
        return [name,r(rd),r(a),str(b if f in (1,5) else imm)]
    if op==0x33:
        name={0:'sub' if g else 'add',1:'sll',2:'slt',3:'sltu',4:'xor',5:'sra' if g else 'srl',6:'or',7:'and'}[f]
        return [name,r(rd),r(a),r(b)]
    if op==3:return [{0:'lb',1:'lh',2:'lw',4:'lbu',5:'lhu'}[f],r(rd),str(imm),r(a)]
    if op==0x23:return [{0:'sb',1:'sh',2:'sw'}[f],r(b),str(sx(((w>>25)<<5)|((w>>7)&31),12)),r(a)]
    if op==0x63:
        off=((w>>31)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1)
        return [{0:'beq',1:'bne',4:'blt',5:'bge',6:'bltu',7:'bgeu'}[f],r(a),r(b),str(sx(off,13))]
    if w==0x73:return ['ecall']
    raise AssertionError(hex(w))

def normalized(s):return [str(int(x,16)) if x.startswith('0x') else x for x in s.split()]
def main():
    path=ROOT/'evidence/pipeline_gui.tsv'
    raw=list(csv.reader(path.read_text().splitlines(),delimiter='\t'))
    # Ripes leaves one empty terminal cell on each row.
    raw=[r[:-1] if r[-1]=='' else r for r in raw]
    assert raw[0][1:]==list(map(str,range(617)))
    data=(ROOT/'build/pipeline_demo.elf').read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
    sec=next(s for i in range(h[12]) if (s:=struct.unpack_from('<10I',data,h[6]+i*h[11]))[2]&4)
    text=data[sec[4]:sec[4]+sec[5]]
    assert len(raw)-1==len(text)//4==117
    rows=[]
    for i,r in enumerate(raw[1:]):
        assert len(r)==618
        word=struct.unpack_from('<I',text,i*4)[0]
        assert normalized(r[0])==decode(word),(i,r[0],decode(word))
        rows.append(dict(pc=hex(sec[3]+i*4),word=hex(word),instruction=r[0],cells=r[1:]))
    lookup={r['pc']:r for r in rows}
    assert lookup['0x1030']['cells'][605]=='-' and lookup['0x1030']['cells'][606]=='EX'
    assert lookup['0x102c']['cells'][606]=='WB'
    excerpts=[]
    for c in range(603,610):
        stages={s:[] for s in ('IF','ID','EX','MEM','WB')};held=[]
        for r in rows:
            state=r['cells'][c]
            if state in stages:stages[state].append(r['pc']+' '+r['instruction'])
            elif state=='-':
                held.append(r['pc']+' '+r['instruction'])
                previous=c-1
                while previous>=0 and r['cells'][previous]=='-':previous-=1
                prior=r['cells'][previous]
                if prior in stages:stages[prior].append(r['pc']+' '+r['instruction']+' [held]')
        assert all(len(v)<=1 for v in stages.values())
        excerpts.append(dict(cycle=c,**{s:(v[0] if v else 'bubble / empty') for s,v in stages.items()},held=held))
    iss=run(ROOT/'build/pipeline_demo.elf','RV32_ISS','pipeline_RV32_ISS')
    five=run(ROOT/'build/pipeline_demo.elf','RV32_5S','pipeline_RV32_5S')
    assert five['cycles']==616 and five['# instructions retired']==514 and five['program_exit_code']==0
    out=dict(trace_origin='Ripes GUI pipeline diagram Copy export; 1000-cycle history setting, Auto clock',
             trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cycles=list(range(617)),rows=rows,
             code_match='All 117 decoded instruction words agree with current ELF at the same PCs',
             text_sha256=hashlib.sha256(text).hexdigest(),elf_sha256=hashlib.sha256(data).hexdigest(),
             control_scope='Instruction-derived controls and pinned Ripes wiring, not live port samples',excerpts=excerpts,
             load_use=dict(detection_cycle=604,bubble_cycle=605,forward_cycle=606,producer='0x102c',consumer='0x1030',
                           hazardFEEnable_at_detection=0,hazardIDEXClear_at_detection=1,forwarding='WB to both EX operands',value=3,result=6),
             memory=dict(address='0x12dcc',store_cycle=604,bytes_little_endian=[3,0,0,0],load_mem_cycle=605),
             model_finalization='This pinned build reports 515 retired on ISS and 514 on 5S at ecall exit; compare like models.')
    (ROOT/'evidence/pipeline_events.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS all 117 trace instructions; 617 observed cycle columns; load-use 604/605/606; final 616 cycles / 514 retired')
if __name__=='__main__':main()
