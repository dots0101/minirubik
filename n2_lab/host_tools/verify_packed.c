/* Compare packed accessors with unpacked data from the previous independently
 * verified representation. These host-only reference files are never linked. */
#include "n2_solver.c"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void fail(const char *what,unsigned at){fprintf(stderr,"FAIL %s %u\n",what,at);exit(1);}
static void read_exact(const char *path,uint8_t *out,size_t size){FILE *f=fopen(path,"rb");if(!f||fread(out,1,size,f)!=size||fgetc(f)!=EOF)fail("reference file",0);fclose(f);}
static void unrankp(unsigned r,WorkState *s){
 unsigned fac[7]={720,120,24,6,2,1,1},n=7;uint8_t a[7]={0,1,2,3,4,5,6};
 memset(s,0,sizeof *s);s->p[7]=7;
 for(unsigned i=0;i<7;i++){unsigned j=r/fac[i];r%=fac[i];s->p[i]=a[j];for(unsigned k=j;k+1<n;k++)a[k]=a[k+1];n--;}
}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 uint8_t *policy=malloc(131072),*sigma=malloc(15120);if(!policy||!sigma)return 3;
 read_exact(argv[1],policy,131072);read_exact(argv[2],sigma,15120);
 unsigned rank=0,even=0,odd=0;
 for(unsigned slot=0;slot<131072;slot++){
  if(!(slot&511u)&&h48_policy_prefix[slot>>9]!=rank)fail("prefix",slot);
  unsigned occupied=(h48_policy_used[slot>>5]>>(slot&31u))&1u;
  if(occupied){unsigned got=(h48_policy_dense[rank>>1]>>((rank&1u)*4u))&15u;if(got!=policy[slot])fail("dense policy parity",rank);if(rank&1u)odd++;else even++;rank++;}
 }
 if(rank!=77802||even!=38901||odd!=38901)fail("population",rank);
 unsigned sigma_even=0,sigma_odd=0;
 for(unsigned pr=0;pr<5040;pr++)for(unsigned twist=0;twist<3;twist++){
  WorkState s;unrankp(pr,&s);unsigned pos=0;while(s.p[pos]!=6)pos++;s.o[pos]=(uint8_t)twist;
  unsigned idx=pr*3+twist;if(t_sigma_code(&s)!=sigma[idx])fail("three bit sigma",idx);
  if(idx&1u)sigma_odd++;else sigma_even++;
 }
 for(unsigned e=0;e<56;e++){
  unsigned byte=n2_b8_exc_aid[e/2];unsigned want=e%2?byte/16:byte%16;
  if(exception_action(e)!=want)fail("exception parity",e);
 }
 if(h48_sigma_pr_3bit[5670]!=0)fail("guard byte",5670);
 printf("PASS policy_rank_slots=131072 populated=77802 even=%u odd=%u prefixes=256\n",even,odd);
 printf("PASS sigma_entries=15120 even=%u odd=%u bit_offsets=0..7 cross_byte=PASS guard=0\n",sigma_even,sigma_odd);
 puts("PASS exception_nibbles=56 even=28 odd=28; independent unpacked reference H4");
 free(policy);free(sigma);return 0;
}
