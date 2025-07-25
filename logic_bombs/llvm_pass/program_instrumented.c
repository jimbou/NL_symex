#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "trace.h"

// Dummy implementations for instrumentation markers
void assume_NL_start() {}
void assume_NL_stop() {}

// {"s":{"length": 4}}
int logic_bomb(char* s) {
    assume_NL_start();
    int symvar = s[0] - 48;
    double d = log(symvar);
    assume_NL_stop(); 
    if(1.94 < d && d < 1.95){
    TRACE(0);
        return 1;
    } else {
    TRACE(1);
        return 0;
    }
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
    TRACE(2);
        fprintf(stderr, "Usage: %s <4-digit-input>\n", argv[0]);
        return 1;
    }

    char* input = argv[1];
    if (strlen(input) != 4) {
    TRACE(3);
        fprintf(stderr, "Input must be exactly 4 characters.\n");
        return 1;
    }

    int result = logic_bomb(input);
    printf("Result: %d\n", result);
    return 0;
}
