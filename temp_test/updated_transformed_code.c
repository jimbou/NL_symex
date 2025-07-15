#include <klee/klee.h>

// Improved stub implementation for calculate_bonus
// Models more complex criteria for bonus calculation:
// 1. For x < 0: bonus is always 0
// 2. For 0 <= x < 10: bonus is between 0-10
// 3. For 10 <= x < 100: bonus is between 10-50
// 4. For x >= 100: bonus is between 50-100
int calculate_bonus(int x) {
    int bonus;
    klee_make_symbolic(&bonus, sizeof(bonus), "bonus");
    
    if (x < 0) {
        klee_assume(bonus == 0);
    } else if (x < 10) {
        klee_assume(bonus >= 0 && bonus <= 10);
    } else if (x < 100) {
        klee_assume(bonus >= 10 && bonus <= 50);
    } else {
        klee_assume(bonus >= 50 && bonus <= 100);
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