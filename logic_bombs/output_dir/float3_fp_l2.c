#include<stdio.h>
#include <stdlib.h>
#include "a_tester.h"

// {"s":{"length": 8}}
int logic_bomb(char* symvar) {
    float x = atof(symvar);
    x = x/10000.0;
    if(1024+x == 1024 && x>0)
        return BOMB_ENDING;
    else
        return NORMAL_ENDING;
}

int main(int argc, char** argv) {
char symvar[1];
klee_make_symbolic(&symvar, sizeof(symvar), "symvar");
klee_assume(symvar[0]=='\0');
return logic_bomb(symvar);
}
