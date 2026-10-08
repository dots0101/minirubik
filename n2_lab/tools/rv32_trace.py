"""Small independent RV32I interpreter for observing production MMIO and PCs.

This host-only checker is not Ripes and is never linked into the guest.
Unsupported opcodes fail rather than silently approximating ISA extensions.
"""
import struct
from collections import Counter

def sx(n,b):return n-(1<<b) if n&(1<<(b-1)) else n
def symbols(data):
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
    sections=[struct.unpack_from('<10I',data,h[6]+i*h[11]) for i in range(h[12])]
    result={}
    for s in sections:
        if s[1]!=2:continue
        strings=sections[s[6]];pool=data[strings[4]:strings[4]+strings[5]]
        for pos in range(s[4],s[4]+s[5],16):
            name,value,size,info,other,idx=struct.unpack_from('<IIIBBH',data,pos)
            if idx:result[pool[name:].split(b'\0')[0].decode()]=value
    return result

class CPU:
    def __init__(self,data):
        h=struct.unpack_from('<16sHHIIIIIHHHHHH',data);self.pc=h[4];self.r=[0]*32
        self.mem={};self.iret=0;self.exit=None;self.output='';self.pcs=Counter();self.write_hook=None
        for i in range(h[10]):
            p=struct.unpack_from('<8I',data,h[5]+i*h[9])
            if p[0]!=1:continue
            for j,v in enumerate(data[p[1]:p[1]+p[4]]):self.mem[p[2]+j]=v
            for j in range(p[4],p[5]):self.mem[p[2]+j]=0
    def load(self,a,n):return sum(self.mem.get((a+i)&0xffffffff,0)<<(8*i) for i in range(n))
    def store(self,a,n,v):
        a&=0xffffffff
        if self.write_hook:self.write_hook(a,n,v&((1<<(8*n))-1))
        for i in range(n):self.mem[(a+i)&0xffffffff]=(v>>(8*i))&255
    def step(self):
        old=self.pc;w=self.load(old,4);self.pc=(old+4)&0xffffffff;self.iret+=1;self.pcs[old]+=1
        op=w&127;rd=(w>>7)&31;f=(w>>12)&7;a=self.r[(w>>15)&31];b=self.r[(w>>20)&31];g=w>>25;im=sx(w>>20,12)
        val=None
        if op==0x37:val=w&0xfffff000
        elif op==0x17:val=old+(w&0xfffff000)
        elif op==0x6f:
            off=((w>>31)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1)
            val=self.pc;self.pc=(old+sx(off,21))&0xffffffff
        elif op==0x67:val=self.pc;self.pc=(a+im)&0xfffffffe
        elif op==0x63:
            off=((w>>31)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1)
            take={0:a==b,1:a!=b,4:sx(a,32)<sx(b,32),5:sx(a,32)>=sx(b,32),6:a<b,7:a>=b}[f]
            if take:self.pc=(old+sx(off,13))&0xffffffff
        elif op==3:
            n={0:1,1:2,2:4,4:1,5:2}[f];val=self.load((a+im)&0xffffffff,n)
            if f in (0,1):val=sx(val,n*8)
        elif op==0x23:
            off=sx(((w>>25)<<5)|((w>>7)&31),12);self.store(a+off,{0:1,1:2,2:4}[f],b)
        elif op==0x13:
            if f==0:val=a+im
            elif f==2:val=int(sx(a,32)<im)
            elif f==3:val=int(a<(im&0xffffffff))
            elif f==4:val=a^(im&0xffffffff)
            elif f==6:val=a|(im&0xffffffff)
            elif f==7:val=a&(im&0xffffffff)
            elif f==1:assert g==0;val=a<<((w>>20)&31)
            elif f==5:assert g in (0,0x20);val=(sx(a,32) if g else a)>>((w>>20)&31)
            else:raise AssertionError(hex(w))
        elif op==0x33:
            assert g==0 or g==0x20 and f in (0,5)
            if f==0:val=a-b if g else a+b
            elif f==1:val=a<<(b&31)
            elif f==2:val=int(sx(a,32)<sx(b,32))
            elif f==3:val=int(a<b)
            elif f==4:val=a^b
            elif f==5:val=(sx(a,32) if g else a)>>(b&31)
            elif f==6:val=a|b
            elif f==7:val=a&b
        elif w==0x73:
            service=self.r[17]
            if service in (10,93):self.exit=self.r[10] if service==93 else 0
            elif service==1:self.output+=str(sx(self.r[10],32))
            elif service==4:
                ptr=self.r[10]
                while self.load(ptr,1):self.output+=chr(self.load(ptr,1));ptr+=1
            else:raise AssertionError(('unsupported ecall',service))
        else:raise AssertionError(('unsupported instruction',hex(old),hex(w)))
        if val is not None and rd:self.r[rd]=val&0xffffffff
        self.r[0]=0
        assert self.iret<1000000,'Diagnostic bound exceeded'
