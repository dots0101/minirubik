/* Exact finite certificate for the supplied solver.  No probabilistic equality.
 * Compile with -I candidate this file + the six data C files, not n2_solver.c.
 * Host-only: stores up to 64 maps X -> X; target code is unchanged. */
#include "n2_solver.c"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#define NN 3674160u
#define MAXG 64u
static const unsigned fac[7]={1,1,2,6,24,120,720};
static uint16_t pt[5040][9],ot[729][9];
static void fail(const char *s,unsigned a,unsigned b){fprintf(stderr,"FAIL %s %u %u\n",s,a,b);exit(1);}
static void unrank(unsigned v,WorkState *s){
 unsigned r=v/729u,o=v%729u,n=7,sum=0;uint8_t a[7]={0,1,2,3,4,5,6};
 for(unsigned i=0;i<7;i++){unsigned k=r/fac[6-i];r%=fac[6-i];s->p[i]=a[k];for(unsigned j=k;j+1<n;j++)a[j]=a[j+1];--n;}
 for(int i=5;i>=0;i--){s->o[i]=o%3;o/=3;sum+=s->o[i];}s->o[6]=(3-sum%3)%3;s->p[7]=7;s->o[7]=0;
}
static unsigned rankp(const uint8_t *p){unsigned r=0;for(unsigned i=0;i<6;i++){unsigned c=0;for(unsigned j=i+1;j<7;j++)c+=p[j]<p[i];r+=c*fac[6-i];}return r;}
static unsigned dense(const WorkState *s){unsigned r=0,sum=0,bits=0;for(unsigned i=0;i<7;i++){if(s->p[i]>=7||s->o[i]>=3)fail("state range",i,s->p[i]);bits|=1u<<s->p[i];sum+=s->o[i];if(i<6)r=r*3+s->o[i];}if(bits!=127||sum%3||s->p[7]!=7||s->o[7])fail("state invariant",bits,sum);return rankp(s->p)*729+r;}
static unsigned mv(unsigned v,unsigned m){return (unsigned)pt[v/729][m]*729+ot[v%729][m];}
static uint64_t hash_map(const uint32_t *a){uint64_t h=1469598103934665603ULL;for(unsigned i=0;i<NN;i++){h^=a[i];h*=1099511628211ULL;}return h;}
static uint32_t *allocmap(void){uint32_t *r=malloc((size_t)NN*sizeof *r);if(!r)fail("malloc",NN,0);return r;}
int main(int argc,char **argv){
 if(argc!=2){fprintf(stderr,"usage: verify_structure full_distance.bin\n");return 2;}
 uint8_t *dist=malloc(NN),*tc=malloc(NN);FILE *f=fopen(argv[1],"rb");if(!dist||!tc||!f||fread(dist,1,NN,f)!=NN||fgetc(f)!=EOF)fail("distance input",0,0);fclose(f);
 for(unsigned r=0;r<5040;r++){WorkState s,d;unrank(r*729,&s);if(rankp(s.p)!=r||perm_rank7(s.p)!=r)fail("rank",r,0);for(unsigned m=0;m<9;m++){state_move(&s,m,&d);pt[r][m]=rankp(d.p);}}
 for(unsigned r=0;r<729;r++){WorkState s,d;unrank(r,&s);for(unsigned m=0;m<9;m++){state_move(&s,m,&d);ot[r][m]=dense(&d)%729;}}
 uint32_t *gen[3]={allocmap(),allocmap(),allocmap()};uint64_t hist[12]={0};unsigned zeros=0;
 for(unsigned v=0;v<NN;v++){
  WorkState s,d;unrank(v,&s);if(dense(&s)!=v)fail("rank inverse",v,0);
  if(dist[v]>11)fail("distance range",v,dist[v]);hist[dist[v]]++;zeros+=dist[v]==0;
  unsigned down=(v==0);for(unsigned m=0;m<9;m++){unsigned w=mv(v,m);int delta=(int)dist[v]-(int)dist[w];if(delta<-1||delta>1)fail("distance edge",v,m);down|=delta==1;}if(!down)fail("distance descent",v,0);
  symmetry_apply(&s,1,&d);gen[0][v]=dense(&d);symmetry_apply(&s,3,&d);gen[1][v]=dense(&d);compact_T(&s,&d);gen[2][v]=dense(&d);tc[v]=t_sigma_code(&s);if(tc[v]>=6)fail("T sigma code",v,tc[v]);
 }
 if(dist[0]||zeros!=1)fail("unique root",zeros,dist[0]);
 printf("distance_certificate vertices=%u directed_edges=%u zero_count=%u PASS\n",NN,NN*9,zeros);
 for(unsigned g=0;g<3;g++)if(gen[g][0])fail("root fixed",g,gen[g][0]);
 for(unsigned v=0;v<NN;v++)if(gen[0][gen[0][v]]!=v||gen[1][gen[1][gen[1][v]]]!=v||gen[2][gen[2][v]]!=v)fail("generator orders",v,0);
 uint8_t forward[12][9];for(unsigned c=0;c<12;c++){unsigned seen=0;for(unsigned m=0;m<9;m++){unsigned a=move_pullback[c][m];if(a>=9||(seen>>a&1))fail("label permutation",c,m);seen|=1u<<a;forward[c][a]=m;}}
 for(unsigned v=0;v<NN;v++)for(unsigned g=0;g<3;g++){unsigned c=g==0?1:g==1?3:6+tc[v];for(unsigned m=0;m<9;m++)if(gen[g][mv(v,m)]!=mv(gen[g][v],forward[c][m]))fail("edge equivariance",v,g*9+m);}
 printf("generators S1^2=S3^3=T^2=id root_fixed legal_images edge_checks=%llu PASS\n",(unsigned long long)NN*27);fflush(stdout);
 /* Generate all transformations, compare full arrays whenever hashes agree.
  * A hash collision cannot merge unequal maps: memcmp is compulsory. */
 uint32_t *maps[MAXG];uint64_t hashes[MAXG];char words[MAXG][32];unsigned trans[MAXG][3];unsigned count=1;
 maps[0]=allocmap();for(unsigned v=0;v<NN;v++)maps[0][v]=v;hashes[0]=hash_map(maps[0]);words[0][0]=0;
 for(unsigned i=0;i<count;i++)for(unsigned g=0;g<3;g++){
  uint32_t *t=allocmap();for(unsigned v=0;v<NN;v++)t[v]=gen[g][maps[i][v]];uint64_t hh=hash_map(t);unsigned j;
  for(j=0;j<count;j++)if(hashes[j]==hh&&!memcmp(maps[j],t,(size_t)NN*4))break;
  if(j==count){if(count>=MAXG)fail("group larger than cap",count,0);maps[count]=t;hashes[count]=hh;snprintf(words[count],32,"%s%c",words[i],"ABT"[g]);count++;}else free(t);trans[i][g]=j;
 }
 printf("exact_generated_group_order=%u PASS\n",count);if(count!=48)fail("expected order",count,0);
 /* Derive S_a R_i from runtime words. These must enumerate the group once. */
 unsigned sid[6]={0},all[48],used=0;
 for(unsigned a=0;a<6;a++)for(unsigned b=0;b<6;b++){
  unsigned c;for(c=0;c<6;c++){unsigned ok=1;for(unsigned j=0;j<8;j++)ok&=n2_b8_sym_pos[c*8+j]==n2_b8_sym_pos[a*8+n2_b8_sym_pos[b*8+j]];if(ok)break;}if(c==6)fail("S3 closure",a,b);
 }
 sid[1]=trans[0][0];sid[3]=trans[0][1];sid[4]=trans[sid[3]][1];sid[2]=trans[sid[3]][0];sid[5]=trans[sid[4]][0];
 /* Resolve IDs robustly via all-state equality, not just the position permutation. */
 for(unsigned a=0;a<6;a++){
  uint32_t *t=allocmap();for(unsigned v=0;v<NN;v++){WorkState s,d;unrank(v,&s);symmetry_apply(&s,a,&d);t[v]=dense(&d);}unsigned j;for(j=0;j<count;j++)if(!memcmp(t,maps[j],(size_t)NN*4))break;free(t);if(j==count)fail("S3 map missing",a,0);sid[a]=j;
 }
 for(unsigned i=0;i<8;i++){
  unsigned id=0;for(unsigned k=0;k<h48_len[i];k++){unsigned op=h48_word[i][k];if(op!=1&&op!=3&&op!=6)fail("unexpected word",i,op);id=trans[id][op==1?0:op==3?1:2];}
  for(unsigned a=0;a<6;a++){
   uint32_t *t=allocmap();for(unsigned v=0;v<NN;v++)t[v]=maps[sid[a]][maps[id][v]];unsigned j;for(j=0;j<count;j++)if(!memcmp(t,maps[j],(size_t)NN*4))break;free(t);if(j==count)fail("coset map missing",i,a);all[used++]=j;
  }
 }
 for(unsigned i=0;i<48;i++)for(unsigned j=0;j<i;j++)if(all[i]==all[j])fail("cosets duplicate",i,j);
 printf("runtime_coset_words 8x6 distinct exact full-domain maps PASS\n");
 printf("S3_group_IDs");for(unsigned a=0;a<6;a++)printf(" %u",sid[a]);puts("");
 printf("group_transitions rows: id word S1_left S3_left T_left\n");for(unsigned i=0;i<count;i++)printf("%u %s %u %u %u\n",i,*words[i]?words[i]:"I",trans[i][0],trans[i][1],trans[i][2]);
 uint64_t fixsum=0,orbits=0,shell_orbit[12]={0},orbit_sizes[49]={0};
 for(unsigned v=0;v<NN;v++){
  unsigned mn=v,stab=0;for(unsigned g=0;g<count;g++){unsigned y=maps[g][v];if(y<mn)mn=y;stab+=y==v;}fixsum+=stab;
  if(mn==v){orbits++;shell_orbit[dist[v]]++;if(!stab||48%stab)fail("stabilizer",v,stab);orbit_sizes[48/stab]++;}
 }
 printf("orbits=%llu burnside_fixsum=%llu fixsum_div_48=%llu\n",(unsigned long long)orbits,(unsigned long long)fixsum,(unsigned long long)(fixsum/48));
 for(unsigned d=0;d<12;d++)printf("shell %u states=%llu orbits=%llu\n",d,(unsigned long long)hist[d],(unsigned long long)shell_orbit[d]);
 for(unsigned n=1;n<=48;n++)if(orbit_sizes[n])printf("orbit_size %u count=%llu\n",n,(unsigned long long)orbit_sizes[n]);
 /* Check quotient key identifies exactly each orbit and each emitted policy edge descends. */
 uint32_t *key_to_orbit=malloc(700000*4),*orbit_to_key=malloc((size_t)NN*4);uint8_t *keys=calloc(700000,1);if(!key_to_orbit||!orbit_to_key||!keys)fail("malloc quotient",0,0);memset(key_to_orbit,255,700000*4);memset(orbit_to_key,255,(size_t)NN*4);
 unsigned keycount=0;uint64_t policy_checks=0;
 for(unsigned v=0;v<NN;v++){
  WorkState s;unrank(v,&s);H48Canon h=h48_canonicalize(&s,quotient_perm_meta(&s));unsigned key=h.key;if(key>=700000)fail("key range",v,key);unsigned mn=v;for(unsigned g=0;g<48;g++)if(maps[g][v]<mn)mn=maps[g][v];
  if(key_to_orbit[key]==UINT32_MAX){key_to_orbit[key]=mn;keys[key]=1;keycount++;}else if(key_to_orbit[key]!=mn)fail("key mixes orbits",v,key);
  if(orbit_to_key[mn]==UINT32_MAX)orbit_to_key[mn]=key;else if(orbit_to_key[mn]!=key)fail("key splits orbit",v,key);
  if(v){unsigned pol=policy_lookup(key);if(pol>=9)fail("policy",v,pol);unsigned m=lift_policy_move(&s,&h,pol);if(m>=9||dist[mv(v,m)]+1!=dist[v])fail("lifted descent",v,m);policy_checks++;}
 }
 printf("canonical_keys=%u exact_orbit_equivalence=PASS lifted_policy_descent=%llu PASS\n",keycount,(unsigned long long)policy_checks);
 /* T cannot act with one global move relabeling: print two witnesses. */
 for(unsigned v=1;v<NN;v++)if(tc[v]!=tc[0]){printf("state_dependent_T_witness dense0=0 code0=%u dense1=%u code1=%u\n",tc[0],v,tc[v]);break;}
 if(orbits!=77802||fixsum!=3734496||keycount!=77802||policy_checks!=NN-1)fail("final counts",keycount,(unsigned)orbits);
 printf("ALL_STRUCTURAL_CHECKS_PASS\n");
 for(unsigned g=0;g<count;g++)free(maps[g]);for(unsigned g=0;g<3;g++)free(gen[g]);free(dist);free(tc);free(key_to_orbit);free(orbit_to_key);free(keys);return 0;
}
