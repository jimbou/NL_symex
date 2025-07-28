/*
TOY:
*/
#include <string.h> 
#include <klee/klee.h>
#include <math.h>

// {"s":{"length": 4}}
int logic_bomb(char* s) {
    int symvar = s[0] - 48;
    double d = log(symvar); 
    if(2 < d && d < 3){
        return 1;
    }else{
        return 0;
    }
}

int main(int argc, char** argv) {
char s[5];
klee_make_symbolic(&s, sizeof(s), "s");
klee_assume(s[4]=='\0');
return logic_bomb(s);
}
