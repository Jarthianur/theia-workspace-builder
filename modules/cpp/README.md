# cpp

This module adds C++ support.

## Features

- gcc
- clang tools
- make/cmake
- doxygen
- valgrind
- gdb
- lcov
- cppcheck
- boost (optional)
- openmp (optional)

## Parameters

`with_omp` [`yes|no`]: Install openmp and openmpi. Default: no

`with_boost` [`yes|no`]: Install boost libraries. Default: no

`llvm_repo` [`stretch|buster|bullseye`] (debian): LLVM apt repo to use. Default: buster (stable)
