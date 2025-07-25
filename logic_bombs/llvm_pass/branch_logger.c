#include <stdio.h>

void __record_branch_hit(int id) {
    printf("Branch taken: %d\n", id);
}
