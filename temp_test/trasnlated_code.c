#include <klee/klee.h>

int compute(int x) {
    int result = x * 2;

    // Replace external bonus calculation with symbolic variable
    int bonus;
    klee_make_symbolic(&bonus, sizeof(bonus), "bonus");
    // Add reasonable assumptions about bonus range
    klee_assume(bonus >= 0 && bonus <= 100);
    result += bonus;

    return result;
}