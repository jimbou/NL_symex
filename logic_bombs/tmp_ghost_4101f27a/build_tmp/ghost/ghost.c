void assume_NL_stop() {}
void assume_NL_start() {}
#include <klee/klee.h>

/*
TOY:
*/
#include <string.h> 
#include <math.h>

// {"s":{"length": 4}}
int logic_bomb(char* s) {
    int symvar = s[0] - 48;
    assume_NL_start();
    double d = symvar;
    assume_NL_stop();
    if(2 < d && d < 3){
        return 1;
    }else{
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
