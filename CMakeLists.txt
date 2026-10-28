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

# Find NetCDF C library (check system first, fallback to externals/netcdf-c if present)
find_library(NETCDF_LIBRARY NAMES netcdf)
find_path(NETCDF_INCLUDE_DIR NAMES netcdf.h)

if(NOT NETCDF_LIBRARY OR NOT NETCDF_INCLUDE_DIR)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/externals/netcdf-c/CMakeLists.txt")
        message(STATUS "NetCDF library not found in system paths; using externals/netcdf-c submodule.")
        add_subdirectory(externals/netcdf-c)
        set(NETCDF_LIBRARY netcdf)
        set(NETCDF_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/externals/netcdf-c/include")
    else()
        message(FATAL_ERROR "Could not find NetCDF C library in system paths or in externals/netcdf-c. Please run 'git submodule update --init --recursive'.")
    endif()
endif()

# Find GoogleTest (check system first, fallback to externals/googletest)
find_package(GTest QUIET)

if(NOT GTest_FOUND)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/externals/googletest/CMakeLists.txt")
        message(STATUS "GoogleTest not found in system paths; using externals/googletest submodule.")
        set(BUILD_GMOCK OFF CACHE BOOL "Build gmock" FORCE)
        set(INSTALL_GTEST OFF CACHE BOOL "Install gtest" FORCE)
        add_subdirectory(externals/googletest)
    else()
        message(FATAL_ERROR "Could not find GoogleTest in system paths or in externals/googletest. Please run 'git submodule update --init --recursive'.")
    endif()
endif()

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

if(TARGET GTest::gtest_main)
    target_link_libraries(test_ugrid_reader PRIVATE
        ww4_ugrid_reader
        GTest::gtest
        GTest::gtest_main
    )
else()
    target_link_libraries(test_ugrid_reader PRIVATE
        ww4_ugrid_reader
        gtest
        gtest_main
    )
endif()

include(GoogleTest)
gtest_discover_tests(test_ugrid_reader)
