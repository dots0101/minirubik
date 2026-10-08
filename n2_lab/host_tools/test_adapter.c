#include "n2_solver.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static const uint8_t map[7]={3,1,5,2,0,4,6};
static const uint8_t sources[3][7]={{1,4,2,0,3,5,6},{0,1,2,4,5,6,3},{0,2,5,3,1,4,6}};
static const uint8_t deltas[3][7]={{1,2,0,2,1,0,0},{0,0,0,1,2,1,2},{0,0,0,0,0,0,0}};
static const uint8_t move_map[9]={2,1,0,8,7,6,5,4,3};
typedef struct {uint8_t p[7],o[7];} Up;
static N2State adapt(const Up*u){N2State s;for(unsigned i=0;i<7;i++){s.perm[map[i]]=map[u->p[i]];if(map[i]<6)s.twist[map[i]]=u->o[i];}return s;}
static Up turn(Up u,unsigned m){for(unsigned t=0;t<m%3+1;t++){Up v;for(unsigned i=0;i<7;i++){v.p[i]=u.p[sources[m/3][i]];v.o[i]=(uint8_t)((u.o[sources[m/3][i]]+deltas[m/3][i])%3);}u=v;}return u;}
static int nextperm(uint8_t p[7]){int i=5,j=6;while(i>=0&&p[i]>=p[i+1])i--;if(i<0)return 0;while(p[j]<=p[i])j--;uint8_t t=p[i];p[i]=p[j];p[j]=t;for(int a=i+1,b=6;a<b;a++,b--){t=p[a];p[a]=p[b];p[b]=t;}return 1;}
static int check(const Up*u){N2State s=adapt(u);for(unsigned m=0;m<9;m++){N2State a=s,b=adapt(&(Up){0});Up v=turn(*u,m);b=adapt(&v);if(!n2_apply_move(&a,move_map[m])||memcmp(&a,&b,sizeof a))return 0;}return 1;}
int main(void){Up u={{0,1,2,3,4,5,6},{0}};unsigned np=0,no=0;do{if(!check(&u))return 1;np++;}while(nextperm(u.p));for(unsigned i=0;i<7;i++)u.p[i]=(uint8_t)i;for(unsigned n=0;n<729;n++){unsigned x=n,sum=0;for(int i=5;i>=0;i--){u.o[i]=(uint8_t)(x%3);sum+=u.o[i];x/=3;}u.o[6]=(uint8_t)((3-sum%3)%3);if(!check(&u))return 2;no++;}printf("PASS independent permutation=%u orientation=%u moves=9 graph_conjugacy=all_states\n",np,no);return 0;}
