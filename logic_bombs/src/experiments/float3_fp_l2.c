#include<stdio.h>
#include <stdlib.h>
#include "a_tester.h"
#include "../../assume.h"


// {"s":{"length": 8}}
int logic_bomb(char* symvar) {
    assume_NL_start;
    float x = atof(symvar);
    x = x/10000.0;
    if(1024+x == 1024 && x>0)
        return BOMB_ENDING;
    else
        return NORMAL_ENDING;
    assume_NL_stop;
}
