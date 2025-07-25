/*
TOY:
Solution: 30
*/
#include <string.h> 
#include <math.h>
#include "utils.h"
#include "../../assume.h"

#define PI 3.14159265358979323846264338327

#include "a_tester.h"

// {"s":{"length": 4}}

int logic_bomb(char* s) {
    assume_NL_start;
    int symvar = s[0];
    float v = sin(symvar*PI/30);
    assume_NL_stop;
    if(v > 0.5){
        return BOMB_ENDING;
    }else{
        return NORMAL_ENDING;
    }
}
