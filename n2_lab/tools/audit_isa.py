"""Audit the current linked executables without repeating runtime benchmarks."""
import hashlib,json,struct
from build import ROOT,PREFIX,elf_sections,run

def audit():
    result={}
    for name in ('solver_cli','gcc_reference','solver_gui','vectors','pipeline_demo'):
        path=ROOT/'build'/f'{name}.elf'; data=path.read_bytes()
        header=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
        assert header[0][:5]==b'\x7fELF\x01' and header[2]==243
        count=0; violations=[]
        for i in range(header[12]):
            section=struct.unpack_from('<10I',data,header[6]+i*header[11])
            if not section[2]&4: continue
            assert section[5]%4==0
            for offset in range(section[4],section[4]+section[5],4):
                word=struct.unpack_from('<I',data,offset)[0]
                op=word&127; funct3=(word>>12)&7; funct7=word>>25
                valid=(word&3==3 and op in (0x37,0x17,0x6f,0x67,0x63,0x03,0x23,0x13,0x33,0x0f,0x73))
                if op==0x33: valid &= funct7==0 or (funct7==0x20 and funct3 in (0,5))
                if op==0x13 and funct3 in (1,5): valid &= funct7==0 or (funct3==5 and funct7==0x20)
                if op==0x73: valid &= word==0x73
                if op==0x03: valid &= funct3 in (0,1,2,4,5)
                if op==0x23: valid &= funct3 in (0,1,2)
                if op==0x63: valid &= funct3 in (0,1,4,5,6,7)
                if op==0x67: valid &= funct3==0
                if not valid: violations.append(hex(word))
                count+=1
        undefined=run([PREFIX+'nm.exe','-u',path])
        sizes=elf_sections(path)
        assert not undefined.strip() and not violations
        assert sizes['allocated_image_bytes']+3500<=131072
        result[name]=dict(**sizes,instructions=count,non_rv32i=violations,undefined_symbols=undefined,sha256=hashlib.sha256(data).hexdigest())
    (ROOT/'evidence/isa_and_size.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS current ELF ISA, static budget, undefined-symbol audit:',json.dumps(result))
    return result
if __name__=='__main__': audit()
