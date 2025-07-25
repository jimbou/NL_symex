#include<stdio.h>
#include <stdlib.h>
#include "a_tester.h"
#include "../../assume.h"


// {"s":{"length": 8}}
int logic_bomb(char* symvar) {
    assume_NL_start;
    float x = atof(symvar);
    x = x/10.0;
    x = x + 0.1;
    x = x * x;
    if (x > 0.1)
	x -= x;
    if(x != 0.02){
        x = x + 7.98;
        if(x == 8)
            return BOMB_ENDING;
    }
    return NORMAL_ENDING;
    assume_NL_stop;
}
