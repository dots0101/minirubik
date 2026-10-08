#include <elf.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
#include <map>
extern "C" {
#include "n2_core_data.h"
}

static int32_t sx(uint32_t x,int bits){uint32_t m=1u<<(bits-1);return (int32_t)((x^m)-m);} 
struct Emu{
 std::vector<uint8_t> mem; uint32_t r[32]{}; uint32_t pc=0; uint32_t minsp=~0u; uint64_t retired=0; uint32_t stop=0xfffffff0u;
 Emu(size_t n):mem(n,0){}
 uint8_t rb(uint32_t a){if(a>=mem.size())throw std::runtime_error("rb oob");return mem[a];}
 uint16_t rh(uint32_t a){return (uint16_t)(rb(a)|(rb(a+1)<<8));}
 uint32_t rw(uint32_t a){return (uint32_t)rb(a)|((uint32_t)rb(a+1)<<8)|((uint32_t)rb(a+2)<<16)|((uint32_t)rb(a+3)<<24);}
 void wb(uint32_t a,uint8_t v){if(a>=mem.size())throw std::runtime_error("wb oob");mem[a]=v;}
 void wh(uint32_t a,uint16_t v){wb(a,v);wb(a+1,v>>8);} void ww(uint32_t a,uint32_t v){wb(a,v);wb(a+1,v>>8);wb(a+2,v>>16);wb(a+3,v>>24);}
 void wr(int rd,uint32_t v){if(rd)r[rd]=v;}
 bool step(){if(pc==stop)return false;uint32_t ins=rw(pc),opc=ins&0x7f,old=pc;pc+=4;retired++;uint32_t rd=(ins>>7)&31,f3=(ins>>12)&7,rs1=(ins>>15)&31,rs2=(ins>>20)&31,f7=ins>>25;uint32_t a=r[rs1],b=r[rs2];
  switch(opc){
   case 0x37: wr(rd,ins&0xfffff000u);break;
   case 0x17: wr(rd,old+(ins&0xfffff000u));break;
   case 0x6f:{uint32_t u=((ins>>31)&1)<<20|((ins>>12)&0xff)<<12|((ins>>20)&1)<<11|((ins>>21)&0x3ff)<<1;wr(rd,pc);pc=old+(uint32_t)sx(u,21);break;}
   case 0x67:{int32_t im=sx(ins>>20,12);uint32_t t=(a+(uint32_t)im)&~1u;wr(rd,pc);pc=t;break;}
   case 0x63:{uint32_t u=((ins>>31)&1)<<12|((ins>>7)&1)<<11|((ins>>25)&0x3f)<<5|((ins>>8)&0xf)<<1;int32_t im=sx(u,13);bool take=false;switch(f3){case 0:take=a==b;break;case 1:take=a!=b;break;case 4:take=(int32_t)a<(int32_t)b;break;case 5:take=(int32_t)a>=(int32_t)b;break;case 6:take=a<b;break;case 7:take=a>=b;break;default:throw std::runtime_error("branch f3");}if(take)pc=old+(uint32_t)im;break;}
   case 0x03:{int32_t im=sx(ins>>20,12);uint32_t ad=a+(uint32_t)im,v=0;switch(f3){case 0:v=(uint32_t)(int32_t)(int8_t)rb(ad);break;case 1:v=(uint32_t)(int32_t)(int16_t)rh(ad);break;case 2:v=rw(ad);break;case 4:v=rb(ad);break;case 5:v=rh(ad);break;default:throw std::runtime_error("load f3");}wr(rd,v);break;}
   case 0x23:{uint32_t u=((ins>>25)<<5)|((ins>>7)&0x1f);int32_t im=sx(u,12);uint32_t ad=a+(uint32_t)im;switch(f3){case 0:wb(ad,(uint8_t)b);break;case 1:wh(ad,(uint16_t)b);break;case 2:ww(ad,b);break;default:throw std::runtime_error("store f3");}break;}
   case 0x13:{int32_t im=sx(ins>>20,12);switch(f3){case 0:wr(rd,a+(uint32_t)im);break;case 2:wr(rd,(int32_t)a<im);break;case 3:wr(rd,a<(uint32_t)im);break;case 4:wr(rd,a^(uint32_t)im);break;case 6:wr(rd,a|(uint32_t)im);break;case 7:wr(rd,a&(uint32_t)im);break;case 1:wr(rd,a<<((ins>>20)&31));break;case 5:{uint32_t sh=(ins>>20)&31;if((ins>>30)&1)wr(rd,(uint32_t)((int32_t)a>>sh));else wr(rd,a>>sh);break;}default:throw std::runtime_error("opimm f3");}break;}
   case 0x33:{switch(f3){case 0:wr(rd,f7==0x20?a-b:a+b);break;case 1:wr(rd,a<<(b&31));break;case 2:wr(rd,(int32_t)a<(int32_t)b);break;case 3:wr(rd,a<b);break;case 4:wr(rd,a^b);break;case 5:wr(rd,f7==0x20?(uint32_t)((int32_t)a>>(b&31)):a>>(b&31));break;case 6:wr(rd,a|b);break;case 7:wr(rd,a&b);break;default:throw std::runtime_error("op f3");}break;}
   case 0x0f: break;
   case 0x73: throw std::runtime_error("system");
   default:{char buf[128];std::snprintf(buf,sizeof buf,"bad opcode pc=%08x ins=%08x op=%02x",old,ins,opc);throw std::runtime_error(buf);}
  }r[0]=0;if(r[2]<minsp)minsp=r[2];return true;
 }
 uint64_t run(uint64_t limit=100000000){while(pc!=stop){if(retired>=limit)throw std::runtime_error("iret limit");step();}return retired;}
};
static std::vector<uint8_t> readfile(const char*p){std::ifstream f(p,std::ios::binary);return std::vector<uint8_t>((std::istreambuf_iterator<char>(f)),{});} 
static void unrank_perm7(uint16_t rr,uint8_t p[7]){int d[7]={},n=7;uint8_t a[7]={0,1,2,3,4,5,6};for(int i=5;i>=0;i--){int base=7-i;d[i]=rr%base;rr/=base;}for(int i=0;i<6;i++){p[i]=a[d[i]];for(int j=d[i];j<n-1;j++)a[j]=a[j+1];n--;}p[6]=a[0];}
static void dense_state(uint32_t v,uint8_t out[13]){uint16_t pr=v/729u,orank=v%729u;unrank_perm7(pr,out);for(int i=5;i>=0;i--){out[7+i]=orank%3;orank/=3;}}

static bool replay(uint8_t st[13], const std::vector<uint8_t>& moves) {
 uint8_t p[8],o[8],q[8],v[8];unsigned sum=0;
 for(int i=0;i<7;i++)p[i]=st[i];p[7]=7;
 for(int i=0;i<6;i++){o[i]=st[7+i];sum+=o[i];}o[6]=(3-sum%3)%3;o[7]=0;
 for(auto m:moves){if(m>=9)return false;for(unsigned i=0;i<8;i++){unsigned src=n2_b8_move_src[m*8+i];q[i]=p[src];v[i]=(o[src]+n2_b8_move_delta[m*8+i])%3;}memcpy(p,q,8);memcpy(o,v,8);}
 for(int i=0;i<8;i++)if(p[i]!=i||o[i]!=0)return false;return true;
}
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"usage: %s elf distance.bin d11|stratified output.csv\n",argv[0]);return 2;}
 auto elf=readfile(argv[1]);if(elf.size()<sizeof(Elf32_Ehdr))return 3;
 auto*eh=(Elf32_Ehdr*)elf.data();if(memcmp(eh->e_ident,ELFMAG,SELFMAG))return 4;
 Emu base(0x500000);
 for(int i=0;i<eh->e_phnum;i++){auto*ph=(Elf32_Phdr*)(elf.data()+eh->e_phoff+i*eh->e_phentsize);if(ph->p_type==PT_LOAD){if((uint64_t)ph->p_vaddr+ph->p_memsz>base.mem.size())throw std::runtime_error("segment oob");memcpy(base.mem.data()+ph->p_vaddr,elf.data()+ph->p_offset,ph->p_filesz);memset(base.mem.data()+ph->p_vaddr+ph->p_filesz,0,ph->p_memsz-ph->p_filesz);}}
 if(std::string(argv[3])=="api"){
  std::map<std::string,uint32_t> fn;
  auto*sh=(Elf32_Shdr*)(elf.data()+eh->e_shoff);
  for(unsigned i=0;i<eh->e_shnum;i++)if(sh[i].sh_type==SHT_SYMTAB){
   const char*names=(const char*)elf.data()+sh[sh[i].sh_link].sh_offset;
   auto*sy=(Elf32_Sym*)(elf.data()+sh[i].sh_offset);
   for(unsigned j=0;j<sh[i].sh_size/sizeof(Elf32_Sym);j++)fn[names+sy[j].st_name]=sy[j].st_value;
  }
  const uint32_t in=0x200000,out=0x200100,cnt=0x200200,stats=0x200206,stack=0x4ff000;
  uint8_t solved[13]={0,1,2,3,4,5,6,0,0,0,0,0,0};unsigned checks=0;
  auto call=[&](const char*name,const uint8_t*st,std::array<uint32_t,4> args,unsigned expected,bool untouched){
   Emu e=base;for(unsigned i=0;i<13;i++)e.wb(in+i,st[i]);
   for(unsigned i=0;i<11;i++)e.wb(out+i,0xa5);e.wb(cnt,0xa5);e.ww(stats,0x78561234);
   const int saved[]={8,9,18,19,20,21,22,23,24,25,26,27};for(int r:saved)e.r[r]=0xa5100000u+r;
   e.r[1]=e.stop;e.r[2]=stack;e.minsp=stack;for(unsigned i=0;i<4;i++)e.r[10+i]=args[i];e.pc=fn.at(name);e.run();
   if(e.r[10]!=expected||e.r[2]!=stack)throw std::runtime_error("API return/stack");
   for(int r:saved)if(e.r[r]!=0xa5100000u+(unsigned)r)throw std::runtime_error("API saved register");
   if(untouched){for(unsigned i=0;i<13;i++)if(e.rb(in+i)!=st[i])throw std::runtime_error("API input changed");for(unsigned i=0;i<11;i++)if(e.rb(out+i)!=0xa5)throw std::runtime_error("API output changed");if(e.rb(cnt)!=0xa5||e.rw(stats)!=0x78561234)throw std::runtime_error("API metadata changed");}
   checks++;
  };
  unsigned invalid=0;
  for(unsigned pos=0;pos<13;pos++)for(unsigned v=0;v<256;v++){
   if(pos<7?v==solved[pos]:v<3)continue;
   uint8_t s[13];memcpy(s,solved,13);s[pos]=(uint8_t)v;
   call("n2_state_valid",s,{in,0,0,0},0,true);call("n2_solve",s,{in,out,cnt,stats},0,true);invalid++;
  }
  call("n2_state_valid",solved,{0,0,0,0},0,true);call("n2_state_valid",solved,{in,0,0,0},1,true);
  for(unsigned m=9;m<256;m++)call("n2_apply_move",solved,{in,m,0,0},0,true);
  call("n2_solve",solved,{0,out,cnt,stats},0,true);call("n2_solve",solved,{in,0,cnt,stats},0,true);call("n2_solve",solved,{in,out,0,stats},0,true);
  call("n2_solve",solved,{in,out,cnt,stats},1,false);
  printf("PASS RV32 ABI API calls=%u invalid_states=%u invalid_moves=247 null_solve_arguments=3 stats_alignment=2 callee_saved=PASS\n",checks,invalid);return 0;
 }
 auto dist=readfile(argv[2]);if(dist.size()!=3674160u)throw std::runtime_error("dist size");
 std::vector<uint32_t> cases;
 if(std::string(argv[3])=="d11"){
  for(uint32_t v=0;v<dist.size();v++)if(dist[v]==11)cases.push_back(v);
 }else if(std::string(argv[3])=="stratified"){
  // Complete shells 0..3; 128 evenly spaced state ranks in each shell 4..10.
  for(unsigned d=0;d<=10;d++){
   std::vector<uint32_t> shell;for(uint32_t v=0;v<dist.size();v++)if(dist[v]==d)shell.push_back(v);
   if(d<=3)cases.insert(cases.end(),shell.begin(),shell.end());
   else for(unsigned j=0;j<128;j++)cases.push_back(shell[(uint64_t)j*(shell.size()-1)/127u]);
  }
 }else return 6;
 FILE*csv=fopen(argv[4],"w");if(!csv)return 7;
 fprintf(csv,"state,depth,retired,stack_bytes,ok,path\n");
 uint64_t sum=0,maxi=0,mini=~0ull;uint32_t maxv=0,maxstack=0;int bad=0;
 const uint32_t in=0x200000,out=0x200100,cnt=0x200200,stats=0x200204,stack=0x4ff000;
 for(size_t ci=0;ci<cases.size();ci++){
  Emu e=base;uint8_t st[13];dense_state(cases[ci],st);
  for(int i=0;i<13;i++)e.wb(in+i,st[i]);
  // Guard output and input boundaries.
  for(int i=-1;i<=11;i++)e.wb(out+i,0xa5);
  for(int i=0;i<32;i++)e.r[i]=0;
  const int saved[]={8,9,18,19,20,21,22,23,24,25,26,27};
  for(int reg:saved)e.r[reg]=0xa5100000u+(unsigned)reg;
  e.r[1]=e.stop;e.r[2]=stack;e.minsp=stack;
  e.r[10]=in;e.r[11]=out;e.r[12]=cnt;e.r[13]=stats;e.pc=eh->e_entry;e.retired=0;
  try{e.run();}catch(const std::exception&ex){fprintf(stderr,"case %zu v=%u error %s\n",ci,cases[ci],ex.what());return 5;}
  uint8_t n=e.rb(cnt);std::vector<uint8_t>path;
  if(n<=11)for(unsigned i=0;i<n;i++)path.push_back(e.rb(out+i));
  bool ok=e.r[10]==1&&n==dist[cases[ci]]&&n<=11&&replay(st,path)
      &&e.rb(out-1)==0xa5&&e.rb(out+11)==0xa5
      &&e.rh(stats)==0&&e.rb(stats+2)==n&&e.rb(stats+3)==0;
  for(unsigned i=0;i<13;i++)if(e.rb(in+i)!=st[i])ok=false;
  for(int reg:saved)if(e.r[reg]!=0xa5100000u+(unsigned)reg)ok=false;
  if(e.r[2]!=stack)ok=false;
  if(!ok)bad++;
  uint32_t used=stack-e.minsp;maxstack=std::max(maxstack,used);
  fprintf(csv,"%u,%u,%llu,%u,%d,",cases[ci],dist[cases[ci]],(unsigned long long)e.retired,used,ok?1:0);
  for(auto m:path)fprintf(csv,"%u",m);fputc('\n',csv);
  sum+=e.retired;if(e.retired>maxi){maxi=e.retired;maxv=cases[ci];}if(e.retired<mini)mini=e.retired;
 }
 fclose(csv);
 printf("cases=%zu bad=%d avg=%.6f min=%llu max=%llu max_state=%u max_stack=%u\n",cases.size(),bad,cases.empty()?0.0:(double)sum/cases.size(),(unsigned long long)mini,(unsigned long long)maxi,maxv,maxstack);
 return bad?1:0;
}
