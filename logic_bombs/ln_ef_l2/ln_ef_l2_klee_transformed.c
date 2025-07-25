/*
TOY:
*/
#include <string.h> 
#include <math.h>
#include <klee/klee.h>
// #include "utils.h"
// #include "a_tester.h"

// {"s":{"length": 4}}
int logic_bomb(char* s) {
    int symvar = s[0] - 48;
    // Only allow symvar in the valid domain of log(), i.e., symvar > 0
    klee_assume(symvar > 0);
    // double d = log(symvar);
    double d;
    if (symvar == 7) {
    d = 1.945; // any value in (1.94, 1.95)
    } else {
        d = 0.0; // value outside (1.94, 1.95)
    }
    if(1.94 < d && d < 1.95){
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
