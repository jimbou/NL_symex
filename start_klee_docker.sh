#!/bin/bash
docker run -d -it \
    --name klee_logic_bombs \
    -v /home/jim/NL_constraints/logic_bombs:/home/klee \
    klee/klee:latest \
    tail -f /dev/null
