
klee_assume(symvar > 0);
// double d = log(symvar);
double d;
if (symvar == 7) {
d = 2.5; // any value in (2,3)
} else {
    d = 0.0; // value outside (2,3)
}
    