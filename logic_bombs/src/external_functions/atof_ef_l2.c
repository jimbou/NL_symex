/*
TOY:
*/
#include <string.h> 
#include <math.h>
#include "utils.h"
#include "a_tester.h"
#include "../../assume.h"
// {"s":{"length": 3}}
int logic_bomb(char* symvar) {
    assume_NL_start;
    float i = atof(symvar);
    assume_NL_stop;
    if(i - 7 == 0){
        return BOMB_ENDING;
    }else{
        return NORMAL_ENDING;
    }
}
