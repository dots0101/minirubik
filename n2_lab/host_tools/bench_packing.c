#include "h48_policy_data.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static volatile uint64_t sink;
int main(void){
 uint8_t *raw=malloc(77802);if(!raw)return 1;
 for(unsigned i=0;i<77802;i++)raw[i]=(h48_policy_dense[i>>1]>>((i&1)*4))&15;
 for(unsigned rep=0;rep<5;rep++){
  uint64_t sums[2]={0};double times[2];
  for(unsigned kind=0;kind<2;kind++){
   uint32_t x=0x12345678;clock_t begin=clock();uint64_t sum=0;
   for(unsigned n=0;n<16000000;n++){x=x*1664525u+1013904223u;unsigned i=x%77802u;sum+=kind?raw[i]:(h48_policy_dense[i>>1]>>((i&1)*4))&15;}
   times[kind]=(double)(clock()-begin)/CLOCKS_PER_SEC;sums[kind]=sum;sink=sum;
  }
  if(sums[0]!=sums[1])return 2;
  printf("rep=%u lookups=16000000 packed_seconds=%.6f byte_seconds=%.6f checksum=%llu\n",rep,times[0],times[1],(unsigned long long)sums[0]);
 }
 printf("PASS entries=77802 packed_bytes=38901 unpacked_bytes=77802 added_target_static_bytes=38901\n");free(raw);return 0;
}
