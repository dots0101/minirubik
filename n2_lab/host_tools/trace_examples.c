#include "n2_solver.c"
#include <stdio.h>
static void stateprint(const WorkState *s){printf("p=[");for(unsigned i=0;i<7;i++)printf("%s%u",i?",":"",s->p[i]);printf("] o=[");for(unsigned i=0;i<7;i++)printf("%s%u",i?",":"",s->o[i]);puts("]");}
static unsigned ord(const WorkState *s){unsigned o=0;for(unsigned i=0;i<6;i++)o=3*o+s->o[i];return o;}
int main(void){N2State z={{0,1,2,3,4,5,6},{0,0,0,0,0,0}},s=z;uint8_t scramble[]={0,3,6,1,4,8};for(unsigned i=0;i<6;i++)n2_apply_move(&s,scramble[i]);WorkState a,b;expand_public(&s,&a);puts("NORMAL_INITIAL");stateprint(&a);printf("pr=%u orientation=%u dense=%u key=%u\n",perm_rank7(a.p),ord(&a),perm_rank7(a.p)*729u+ord(&a),(perm_rank7(a.p)<<10)|ord(&a));
 uint8_t out[11],n=0;n2_solve(&s,out,&n,0);printf("solution len=%u:",n);for(unsigned i=0;i<n;i++)printf(" %u",out[i]);puts("");
 for(unsigned step=0;!work_solved(&a);step++){
  H48Canon h=h48_canonicalize(&a,quotient_perm_meta(&a));unsigned p=policy_lookup(h.key),m=lift_policy_move(&a,&h,p);printf("step=%u pr=%u ori=%u Hkey=%u frame=(%u,%u,%u) pol=%u move=%u\n",step,perm_rank7(a.p),ord(&a),h.key,h.rep,h.perm_sym,h.stab_sym,p,m);
  if(step==0){for(unsigned r=0;r<8;r++){WorkState w=a,v;for(unsigned k=0;k<h48_len[r];k++){unsigned op=h48_word[r][k];if(op==6)compact_T(&w,&v);else symmetry_apply(&w,op,&v);w=v;}unsigned mt=quotient_perm_meta(&w);CanonInfo ci=quotient_rank_from_meta(&w,mt);printf("  rep=%u permclass=%u qkey=%u bs=%u hs=%u\n",r,mt>>3,ci.qidx,ci.perm_sym,ci.stab_sym);}}
  state_move(&a,m,&b);a=b;stateprint(&a);
 }
 s=z;s.perm[1]=3;s.perm[3]=1;expand_public(&s,&a);puts("OFFICIAL_POLICY_EXAMPLE");stateprint(&a);n2_solve(&s,out,&n,0);printf("solution len=%u:",n);for(unsigned i=0;i<n;i++)printf(" %u",out[i]);puts("");
 for(unsigned i=0;i<n;i++){H48Canon h=h48_canonicalize(&a,quotient_perm_meta(&a));unsigned pol=policy_lookup(h.key),m=lift_policy_move(&a,&h,pol);printf("official step=%u Hkey=%u frame=(%u,%u,%u) pol=%u move=%u\n",i,h.key,h.rep,h.perm_sym,h.stab_sym,pol,m);state_move(&a,out[i],&b);a=b;}printf("official_replay_solved=%d\n",work_solved(&a));
 return 0;}
