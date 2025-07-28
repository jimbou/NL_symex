cmake_minimum_required(VERSION 3.4.3)
project(BranchTracePass)

find_package(LLVM REQUIRED CONFIG)
list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")
include(AddLLVM)

add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})
link_directories(${LLVM_LIBRARY_DIRS})

add_library(BranchTracePass MODULE BranchTracePass.cpp)

set_target_properties(BranchTracePass PROPERTIES
    COMPILE_FLAGS "-fno-rtti"
)
