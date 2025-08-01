#include "/home/klee/llvm_pass/trace.h"
#include <klee/klee.h>

/*
TOY:
*/
#include <string.h> 
#include <math.h>

// {"s":{"length": 4}}
int logic_bomb(char* s) {
    int symvar = s[0] - 48;
    // assume_NL_start();
    double d = log(symvar); 
    // assume_NL_stop();
    if(2 < d && d < 4){
    TRACE(0);
        return 1;
    }else{
    TRACE(1);
        return 0;
    }
}

int main() {
    char s[4];
    klee_make_symbolic(s, sizeof(s), "s");
    // Ensure s is printable (optional) and s[0] >= '0'
    klee_assume(s[0] >= 0);
    logic_bomb(s);
    return 0;
}
