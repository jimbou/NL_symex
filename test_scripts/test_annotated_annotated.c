#include <klee/klee.h>


/*
TOY:
*/
#include <string.h> 
#include <math.h>

// {"s":{"length": 4}}
int logic_bomb(char* s) {
    int symvar = s[0] - 48;
    double d = log(symvar); 
    if(2 < d && d < 4){
        return 1;
    }else{
        return 0;
    }
}

int main() {
    char input[4];
    klee_make_symbolic(input, sizeof(input), "input");
    klee_assume(input[3] == '\0'); // Ensure null-termination for string
    logic_bomb(input);
    return 0;
}
