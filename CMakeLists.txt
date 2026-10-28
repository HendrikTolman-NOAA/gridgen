# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.

cmake_minimum_required(VERSION 3.20)
project(ww4gridgen CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Strict compiler warnings and safety flags
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Find NetCDF C library
find_library(NETCDF_LIBRARY NAMES netcdf REQUIRED)
find_path(NETCDF_INCLUDE_DIR NAMES netcdf.h REQUIRED)

# Find GoogleTest
find_package(GTest REQUIRED)

# NetCDF-UGRID reader library
add_library(ww4_ugrid_reader
    src/ugrid_reader.cpp
)

target_include_directories(ww4_ugrid_reader PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    ${NETCDF_INCLUDE_DIR}
)

target_link_libraries(ww4_ugrid_reader PRIVATE
    ${NETCDF_LIBRARY}
)

# Utility program to read and display NetCDF grid metadata
add_executable(ww4_read_grid
    src/read_grid.cpp
)

target_link_libraries(ww4_read_grid PRIVATE
    ww4_ugrid_reader
)

# Test target
enable_testing()
add_executable(test_ugrid_reader
    tests/test_ugrid_reader.cpp
)

target_link_libraries(test_ugrid_reader PRIVATE
    ww4_ugrid_reader
    GTest::gtest
    GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(test_ugrid_reader)
