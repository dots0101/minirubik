#include "n2_solver.c"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NN 3674160u
static const unsigned fact[7]={1,1,2,6,24,120,720};
static void die(const char *x,unsigned i){fprintf(stderr,"FAIL %s %u\n",x,i);exit(1);}
static void unrank(unsigned v,WorkState*s){unsigned pr=v/729,or=v%729,n=7,sum=0;uint8_t a[7]={0,1,2,3,4,5,6};for(unsigned i=0;i<7;i++){unsigned j=pr/fact[6-i];pr%=fact[6-i];s->p[i]=a[j];for(unsigned k=j;k+1<n;k++)a[k]=a[k+1];n--;}for(int i=5;i>=0;i--){s->o[i]=or%3;or/=3;sum+=s->o[i];}s->o[6]=(3-sum%3)%3;s->p[7]=7;s->o[7]=0;}
static unsigned drank(WorkState*s){unsigned r=0,o=0;for(unsigned i=0;i<6;i++){unsigned c=0;for(unsigned j=i+1;j<7;j++)c+=s->p[j]<s->p[i];r+=c*fact[6-i];o=3*o+s->o[i];}return r*729+o;}
static unsigned chi(unsigned i){return ((i&1)+((i>>1)&1)+((i>>2)&1))%2;}
int main(void){
 const int eps[6]={1,2,2,1,1,2},beta[6]={0,1,2,2,1,0};
 for(unsigned h=0;h<6;h++)for(unsigned p=0;p<8;p++)for(unsigned c=0;c<8;c++)for(unsigned o=0;o<3;o++){int v=(eps[h]*o+beta[h]*((int)chi(p)-(int)chi(c))+6)%3;if(n2_b8_sym_twist[((h*8+p)*8+c)*3+o]!=v)die("sym formula",h);}
 puts("symmetry_orientation_formula 1152/1152 PASS");
 unsigned reps[870],sizes[870]={0},stabdist[7]={0},fixedp[6]={0};memset(reps,255,sizeof reps);
 for(unsigned r=0;r<5040;r++){WorkState s,d;unrank(r*729,&s);unsigned meta=quotient_perm_meta(&s),oi=meta>>3,bs=meta&7;if(oi>=870||bs>=6)die("pmeta range",r);symmetry_apply(&s,bs,&d);unsigned rep=perm_rank7(d.p);if(reps[oi]==~0u)reps[oi]=rep;else if(reps[oi]!=rep)die("pmeta rep",r);sizes[oi]++;
  unsigned min=r,stab=0;for(unsigned h=0;h<6;h++){symmetry_apply(&s,h,&d);unsigned rr=perm_rank7(d.p);if(rr<min)min=rr;if(rr==r){stab++;fixedp[h]++;}}
  stabdist[stab]++;if(rep!=min)die("rep not min",r);
 }
 printf("permutation_orbits=870 common=814 exceptional=56\n");for(unsigned i=1;i<=6;i++)if(stabdist[i])printf("permutation_stabilizer_size=%u raw_permutations=%u\n",i,stabdist[i]);printf("permutation_fixed_counts");for(unsigned h=0;h<6;h++)printf(" %u",fixedp[h]);puts("");
 unsigned *key_to_raw=malloc(700000*4),*raw_to_key=malloc((size_t)NN*4);unsigned qcount=0,maxkey=0;uint64_t fixedx[6]={0};if(!key_to_raw||!raw_to_key)die("allocation",0);memset(key_to_raw,255,700000*4);memset(raw_to_key,255,(size_t)NN*4);
 uint8_t *hkeys=calloc(700000,1);if(!hkeys)die("allocation hkeys",0);unsigned hcount=0;
 for(unsigned v=0;v<NN;v++){WorkState s,d;unrank(v,&s);unsigned mn=v;for(unsigned h=0;h<6;h++){symmetry_apply(&s,h,&d);unsigned y=drank(&d);if(y<mn)mn=y;fixedx[h]+=y==v;}
  CanonInfo ci=quotient_rank_from_meta(&s,quotient_perm_meta(&s));unsigned k=ci.qidx;if(k>=700000)die("qkey range",v);if(k>maxkey)maxkey=k;if(key_to_raw[k]==~0u){key_to_raw[k]=mn;qcount++;}else if(key_to_raw[k]!=mn)die("S3 key merge",v);if(raw_to_key[mn]==~0u)raw_to_key[mn]=k;else if(raw_to_key[mn]!=k)die("S3 key split",v);
  H48Canon hc=h48_canonicalize(&s,quotient_perm_meta(&s));if(hc.key>=700000)die("H key range",v);if(!hkeys[hc.key]){hkeys[hc.key]=1;hcount++;}
 }
 printf("S3_state_orbits=%u max_dense_quotient_key=%u\n",qcount,maxkey);if(qcount!=612630||maxkey!=612629)die("S3 quotient count/range",qcount);
 printf("S3_state_fixed_counts");for(unsigned h=0;h<6;h++)printf(" %llu",(unsigned long long)fixedx[h]);puts("");
 for(unsigned e=0;e<56;e++){
  unsigned aid=exception_action(e),n=0;WorkState s,d;unrank(reps[814+e]*729,&s);unsigned sm=0;for(unsigned h=0;h<6;h++){symmetry_apply(&s,h,&d);if(!memcmp(s.p,d.p,8))sm|=1u<<h;}if(sm!=stabilizer_mask(aid))die("stabilizer mask",e);
  for(unsigned o=0;o<729;o++){unrank(reps[814+e]*729+o,&s);unsigned mn=729;for(unsigned h=0;h<6;h++)if(sm>>h&1){symmetry_apply(&s,h,&d);unsigned x=drank(&d)%729;if(x<mn)mn=x;}unsigned bit=(n2_b8_action_mask[action_offset[aid]+o/32]>>(o%32))&1;if(bit!=(mn==o))die("orientation mask",e);n+=bit;}
  unsigned next=e+1<56?h48_exc_base[e+1]:qcount;if(next-h48_exc_base[e]!=n)die("exc base",e);
 }
 puts("pmeta stabilizers orientation_masks all_entries PASS");
 int *owner=malloc(131072*sizeof(int));if(!owner)die("allocation owner",0);for(unsigned i=0;i<131072;i++)owner[i]=-1;unsigned slots=0,collisions=0,conflicts=0;
 for(unsigned k=0;k<700000;k++)if(hkeys[k]){uint32_t x=k^(k>>13)^(k<<7),b=x&0x3fff,y=k^(k>>7)^(k<<9);y^=y>>5;unsigned slot=((y>>2)+h48_policy_disp[b])&0x1ffff;unsigned p=policy_lookup(k);if(owner[slot]<0){slots++;owner[slot]=(int)k;}else{collisions++;if(policy_lookup(owner[slot])!=p)conflicts++;}}
 printf("policy_hash valid_keys=%u used_slots=%u same_slot_extra_keys=%u stored_value_conflicts=%u\n",hcount,slots,collisions,conflicts);
 if(hcount!=77802||slots!=77802||collisions!=0||conflicts!=0)die("policy perfect hash",hcount);
 WorkState e;unrank(0,&e);CanonInfo ci=quotient_rank_from_meta(&e,quotient_perm_meta(&e));H48Canon hc=h48_canonicalize(&e,quotient_perm_meta(&e));printf("identity dense=0 permutation_meta=%u S3_key=%u H48_key=%u policy=%u\n",quotient_perm_meta(&e),ci.qidx,hc.key,policy_lookup(hc.key));
 puts("ALL_TABLE_CHECKS_PASS");free(owner);free(hkeys);free(key_to_raw);free(raw_to_key);return 0;
}
