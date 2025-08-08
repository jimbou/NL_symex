#include <assert.h>
#include <klee/klee.h>

/*
TOY:
*/
#include <string.h> 
#include <math.h>
int reached_NL = 0;

// {"s":{"length": 4}}
int logic_bomb(char* s) {
  
   
    int symvar = s[0] - 48;
    // inserted klee_assume relaxation factor = 1.0
    klee_assume(fabs(s[0] - 0) <= 10.0);
    // assume_NL_start();
    reached_NL = 1;
    klee_assert(0);
    double d = log(symvar); 
    // assume_NL_stop();
   
    if(2 < d && d < 4){
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
    if (!reached_NL) klee_silent_exit(0);
    return 0;
}