// #include <stdio.h>

// void __record_branch_hit(int id) {
//     printf("Branch taken: %d\n", id);
// }
#include <klee/klee.h>
void __record_branch_hit(int id) {
    klee_print_expr("Branch taken:", id);  // This logs to KLEE’s messages.txt
}
