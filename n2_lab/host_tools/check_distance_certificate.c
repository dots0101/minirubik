#include "n2_core_data.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define N 3674160u
static const unsigned fact[7]={1,1,2,6,24,120,720};
static void perm(unsigned r,uint8_t p[8]){
 uint8_t a[7]={0,1,2,3,4,5,6};unsigned n=7;
 for(unsigned i=0;i<7;i++){unsigned j=r/fact[6-i];r%=fact[6-i];p[i]=a[j];for(unsigned k=j;k+1<n;k++)a[k]=a[k+1];n--;}p[7]=7;
}
static unsigned rank(const uint8_t p[8]){unsigned r=0;for(unsigned i=0;i<6;i++){unsigned c=0;for(unsigned j=i+1;j<7;j++)if(p[j]<p[i])c++;r+=c*fact[6-i];}return r;}
int main(int argc,char**argv){
 if(argc!=2)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;
 uint8_t*d=malloc(N);if(!d||fread(d,1,N,f)!=N||fgetc(f)!=EOF)return 4;fclose(f);
 static uint16_t pt[5040][9],ot[729][9];
 for(unsigned r=0;r<5040;r++){
  uint8_t p[8],q[8];perm(r,p);if(rank(p)!=r)return 5;
  for(unsigned m=0;m<9;m++){for(unsigned j=0;j<8;j++)q[j]=p[n2_b8_move_src[m*8+j]];if(q[7]!=7)return 6;pt[r][m]=(uint16_t)rank(q);}
 }
 for(unsigned r=0;r<729;r++){
  uint8_t o[8],q[8];unsigned a=r,sum=0;
  for(int i=5;i>=0;i--){o[i]=a%3;a/=3;sum+=o[i];}o[6]=(3-sum%3)%3;o[7]=0;
  for(unsigned m=0;m<9;m++){
   unsigned rank0=0,total=0;for(unsigned j=0;j<8;j++){q[j]=(o[n2_b8_move_src[m*8+j]]+n2_b8_move_delta[m*8+j])%3;total+=q[j];}
   if(q[7]||total%3)return 7;for(unsigned j=0;j<6;j++)rank0=rank0*3+q[j];ot[r][m]=(uint16_t)rank0;
  }
 }
 uint64_t bad_edge=0,bad_descent=0,edges=0;unsigned zeros=0;uint64_t hist[256]={0};
 for(unsigned v=0;v<N;v++){
  unsigned p=v/729,o=v%729;int down=v==0;
  hist[d[v]]++;if(d[v]==0)zeros++;
  for(unsigned m=0;m<9;m++){
   unsigned w=(unsigned)pt[p][m]*729+ot[o][m];int delta=(int)d[v]-(int)d[w];
   if(delta<-1||delta>1)bad_edge++;if(delta==1)down=1;edges++;
  }
  if(!down)bad_descent++;
 }
 printf("vertices=%u directed_edges=%llu root_distance=%u zero_count=%u bad_edge_lipschitz=%llu bad_descent=%llu\n",N,(unsigned long long)edges,d[0],zeros,(unsigned long long)bad_edge,(unsigned long long)bad_descent);
 for(unsigned i=0;i<256;i++)if(hist[i])printf("distance[%u]=%llu\n",i,(unsigned long long)hist[i]);
 free(d);return bad_edge||bad_descent||zeros!=1?1:0;
}
