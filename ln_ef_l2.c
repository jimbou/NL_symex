/*
TOY:
*/
#include <string.h> 
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

