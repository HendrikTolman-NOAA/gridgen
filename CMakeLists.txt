# WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
#
# Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
# NWS often uses Generative AI (GenAI) for code development and refactoring.
# Whenever GenAI is used, NWS requires a full human review of code before it
# is added to its repositories.

cmake_minimum_required(VERSION 3.25)
project(ww4gridgen VERSION 3.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set default output directory for executables
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Options for strict warnings and testing matching WW4 conventions
option(WW4_STRICT_WARNINGS "Enable strict compiler warnings and treat as errors" OFF)
option(WW4_ENABLE_TESTING "Enable C++ unit test suite" ON)

# Define common compile options for WW4 targets
set(WW4_COMMON_COMPILE_OPTIONS "")

if(MSVC)
    if(WW4_STRICT_WARNINGS)
        list(APPEND WW4_COMMON_COMPILE_OPTIONS /W4 /WX)
    endif()
else()
    list(APPEND WW4_COMMON_COMPILE_OPTIONS -Wall -Wextra -Wpedantic)
    if(WW4_STRICT_WARNINGS)
        list(APPEND WW4_COMMON_COMPILE_OPTIONS -Werror)
        if(CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "IntelLLVM")
            list(APPEND WW4_COMMON_COMPILE_OPTIONS -Wno-unknown-warning-option -Wno-character-conversion)
        endif()
    endif()
endif()

# Find NetCDF C library (check system first, fallback to externals/netcdf-c if present)
find_library(NETCDF_LIBRARY NAMES netcdf)
find_path(NETCDF_INCLUDE_DIR NAMES netcdf.h)

if(NOT NETCDF_LIBRARY OR NOT NETCDF_INCLUDE_DIR)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/externals/netcdf-c/CMakeLists.txt")
        message(STATUS "NetCDF library not found in system paths; using externals/netcdf-c submodule.")

        # Check if HDF5 is available on the system
        find_package(HDF5 QUIET COMPONENTS C HL)
        if(NOT HDF5_FOUND)
            message(STATUS "HDF5 not found in system paths; building netcdf-c without HDF5 support.")
            set(NETCDF_ENABLE_HDF5 OFF CACHE BOOL "Disable HDF5 in netcdf-c submodule" FORCE)
            set(NETCDF_ENABLE_NETCDF4 OFF CACHE BOOL "Disable NetCDF4 in netcdf-c submodule" FORCE)
        endif()

        # Disable unneeded submodule features to ensure fast, clean builds
        set(NETCDF_BUILD_UTILITIES OFF CACHE BOOL "Disable netcdf utilities in submodule" FORCE)
        set(NETCDF_ENABLE_DAP OFF CACHE BOOL "Disable DAP in netcdf-c submodule" FORCE)
        set(NETCDF_ENABLE_NCZARR OFF CACHE BOOL "Disable NCZarr in netcdf-c submodule" FORCE)
        set(BUILD_TESTING OFF CACHE BOOL "Disable testing in submodules" FORCE)

        add_subdirectory(externals/netcdf-c EXCLUDE_FROM_ALL SYSTEM)
        set(NETCDF_LIBRARY netcdf)
        set(NETCDF_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/externals/netcdf-c/include")
    else()
        message(FATAL_ERROR "Could not find NetCDF C library in system paths or in externals/netcdf-c. Please run 'git submodule update --init --recursive'.")
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

target_compile_options(ww4_ugrid_reader PRIVATE ${WW4_COMMON_COMPILE_OPTIONS})

# Utility program to read and display NetCDF grid metadata
add_executable(ww4_read_grid
    src/read_grid.cpp
)

target_link_libraries(ww4_read_grid PRIVATE
    ww4_ugrid_reader
)

target_compile_options(ww4_read_grid PRIVATE ${WW4_COMMON_COMPILE_OPTIONS})

# Place the main program executable in the exe directory
set_target_properties(
    ww4_read_grid
    PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/exe
)

# Tests (skipped when WW4_ENABLE_TESTING is OFF)
if(WW4_ENABLE_TESTING)
    # Find GoogleTest (check system first, fallback to externals/googletest)
    find_package(GTest QUIET)

    if(NOT GTest_FOUND)
        if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/externals/googletest/CMakeLists.txt")
            message(STATUS "GoogleTest not found in system paths; using externals/googletest submodule.")
            set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
            set(BUILD_GMOCK OFF CACHE BOOL "Build gmock" FORCE)
            set(INSTALL_GTEST OFF CACHE BOOL "Install gtest" FORCE)
            add_subdirectory(externals/googletest EXCLUDE_FROM_ALL SYSTEM)
        else()
            message(FATAL_ERROR "Could not find GoogleTest in system paths or in externals/googletest. Please run 'git submodule update --init --recursive'.")
        endif()
    endif()

    enable_testing()
    include(GoogleTest)

    add_executable(test_ugrid_reader
        tests/test_ugrid_reader.cpp
    )

    target_compile_options(test_ugrid_reader PRIVATE ${WW4_COMMON_COMPILE_OPTIONS})

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

    gtest_discover_tests(test_ugrid_reader)
endif()
