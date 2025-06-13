#include <stdio.h>
#include "assume.h"  // optional, or just define above

int compute(int x) {
    int result = x * 2;

    assume_NL_start;
    // This part calculates a bonus based on some complex criteria.
    int bonus = calculate_bonus(x);
    result += bonus;
    assume_NL_stop;

    return result;
}
