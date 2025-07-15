#include <klee/klee.h>

// Stub implementation for calculate_bonus
// Models that bonus is between 0-100 when x > 0, otherwise 0
int calculate_bonus(int x) {
    int bonus;
    klee_make_symbolic(&bonus, sizeof(bonus), "bonus");
    if (x > 0) {
        klee_assume(bonus >= 0 && bonus <= 100);
    } else {
        klee_assume(bonus == 0);
    }
    return bonus;
}

int compute(int x) {
    int result = x * 2;

    // This part calculates a bonus based on some complex criteria.
    int bonus = calculate_bonus(x);
    result += bonus;

    return result;
}