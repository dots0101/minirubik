#define main old_test_main
#include "test_full_domain.c"
#undef main
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    FILE *f=fopen(argv[1],"rb"),*g=fopen(argv[2],"w");
    if(!f||!g)return 3;
    for(uint32_t v=0;v<N2_STATE_COUNT;++v) {
        int d=fgetc(f); if(d==EOF)return 4; if(d!=11)continue;
        N2State s;uint8_t out[11],n=0;from_dense(v,&s);
        if(!n2_solve(&s,out,&n,NULL)||n!=11)return 5;
        fprintf(g,"%u",v);for(unsigned j=0;j<11;++j)fprintf(g,",%u",out[j]);fputc('\n',g);
    }
    fclose(f);fclose(g);return 0;
}
