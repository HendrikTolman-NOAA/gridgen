#+ -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
#| WAVEWATCH IV, open source, code management by NOAA / NWS |
#+ -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
#
#@file CMakeLists.txt
#@brief CMake build configuration for WAVEWATCH IV (WW4) Gridgen C++ utilities.
#@details This file defines the project structure, submodules (netcdf-c, googletest),
#and build targets for local WAVEWATCH IV C++ reader library, utilities, and tests.
#
#@copyright © 2026 National Weather Service, National Oceanic and Atmospheric
#Administration. WAVEWATCH IV (TM) and WW4 (TM) are trademarks
#of the National Weather Service.
#NWS often uses Generative AI (GenAI) for code development and refactoring.
#Whenever GenAI is used, NWS requires a full human review of code before it
#is added to its repositories.
#@author Main Author(s) : Aldgisl (AI Persona), Hendrik L. Tolman
#@author Contributors : Jules (Agentic AI), Kit Stokes, Jessica Meixner
#@date Initial : 2026-07-09
#@date Last update : 2026-10-29

cmake_minimum_required(VERSION 3.25)

project(ww4gridgen VERSION 3.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set default output directory for executables
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Options for strict warnings, sanitizers, and testing
option(WW4_STRICT_WARNINGS "Enable strict compiler warnings and treat as errors" OFF)
option(WW4_USE_SANITIZERS "Enable address and undefined behavior sanitizers" OFF)
option(WW4_ENABLE_TESTING "Enable WAVEWATCH IV test suite" ON)

# Define common compile options for WW4 targets
set(WW4_COMMON_COMPILE_OPTIONS "")
set(WW4_COMMON_LINK_OPTIONS "")

if(MSVC)
    if(WW4_STRICT_WARNINGS)
        list(APPEND WW4_COMMON_COMPILE_OPTIONS /W4 /WX)
    endif()
else()
    list(APPEND WW4_COMMON_COMPILE_OPTIONS -Wall -Wextra -Wpedantic)
    if(WW4_STRICT_WARNINGS)
        list(APPEND WW4_COMMON_COMPILE_OPTIONS -Werror)
        # Suppress unknown warning option and conversion errors for LLVM-based compilers (Clang, IntelLLVM)
        if(CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "IntelLLVM")
            list(APPEND WW4_COMMON_COMPILE_OPTIONS -Wno-unknown-warning-option -Wno-character-conversion)
            # Suppress Intel LLVM driver warning about unsupported options (e.g., -Winline)
            if(CMAKE_CXX_COMPILER_ID STREQUAL "IntelLLVM")
                list(APPEND WW4_COMMON_COMPILE_OPTIONS -diag-disable=10430)
            endif()
        endif()
    endif()
    if(WW4_USE_SANITIZERS)
        list(APPEND WW4_COMMON_COMPILE_OPTIONS -fsanitize=address,undefined)
        list(APPEND WW4_COMMON_LINK_OPTIONS -fsanitize=address,undefined)
    endif()
endif()

# yaml-cpp for configuration parsing (if present)
if(EXISTS "${CMAKE_SOURCE_DIR}/externals/yaml-cpp/CMakeLists.txt")
    add_subdirectory(externals/yaml-cpp EXCLUDE_FROM_ALL SYSTEM)
endif()

# netcdf-c for NetCDF / UGRID file reading
if(EXISTS "${CMAKE_SOURCE_DIR}/externals/netcdf-c/CMakeLists.txt")
    find_package(HDF5 QUIET COMPONENTS C)
    find_package(ZLIB QUIET)

    if(HDF5_FOUND AND ZLIB_FOUND)
        message(STATUS "NetCDF-4 dependencies found (HDF5 ${HDF5_VERSION}, ZLIB). Enabling NetCDF-4 support.")
        set(NETCDF_ENABLE_HDF5 ON CACHE BOOL "" FORCE)
        set(NETCDF_ENABLE_NETCDF_4 ON CACHE BOOL "" FORCE)
    else()
        message(STATUS "HDF5/ZLIB not found in local environment. Enabling NetCDF-3 classic support.")
        set(NETCDF_ENABLE_HDF5 OFF CACHE BOOL "" FORCE)
        set(NETCDF_ENABLE_NETCDF_4 OFF CACHE BOOL "" FORCE)
    endif()

    set(NETCDF_ENABLE_DAP OFF CACHE BOOL "" FORCE)
    set(NETCDF_ENABLE_NCZARR OFF CACHE BOOL "" FORCE)
    set(NETCDF_ENABLE_UTILITIES OFF CACHE BOOL "" FORCE)
    set(NETCDF_ENABLE_TESTS OFF CACHE BOOL "" FORCE)
    set(NETCDF_ENABLE_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
    set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
    unset(ENABLE_DAP CACHE)
    unset(ENABLE_EXAMPLES CACHE)
    unset(ENABLE_HDF5 CACHE)
    unset(ENABLE_NCZARR CACHE)
    unset(ENABLE_NETCDF_4 CACHE)
    unset(ENABLE_TESTS CACHE)
    add_subdirectory(externals/netcdf-c EXCLUDE_FROM_ALL SYSTEM)
else()
    message(FATAL_ERROR "netcdf-c submodule not found in externals/netcdf-c. Please run: git submodule update --init --recursive")
endif()

# Library: ww4_ugrid_reader
add_library(
    ww4_ugrid_reader
    src/ugrid_reader.cpp
)

target_include_directories(ww4_ugrid_reader PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(ww4_ugrid_reader PUBLIC
    netcdf
)

target_compile_options(ww4_ugrid_reader PRIVATE ${WW4_COMMON_COMPILE_OPTIONS})
target_link_options(ww4_ugrid_reader PRIVATE ${WW4_COMMON_LINK_OPTIONS})

# Executable: ww4_read_grid
add_executable(
    ww4_read_grid
    src/read_grid.cpp
)

target_link_libraries(ww4_read_grid PRIVATE
    ww4_ugrid_reader
)

target_compile_options(ww4_read_grid PRIVATE ${WW4_COMMON_COMPILE_OPTIONS})
target_link_options(ww4_read_grid PRIVATE ${WW4_COMMON_LINK_OPTIONS})

# Place the main program in the exe directory
set_target_properties(
    ww4_read_grid
    PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/exe
)

# Tests (skipped when WW4_ENABLE_TESTING is OFF for operational builds)
if(WW4_ENABLE_TESTING)
    if(EXISTS "${CMAKE_SOURCE_DIR}/externals/googletest/CMakeLists.txt")
        # For Windows: Prevent overriding the parent project's compiler/linker settings
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
        add_subdirectory(externals/googletest EXCLUDE_FROM_ALL SYSTEM)
    else()
        message(FATAL_ERROR "googletest submodule not found in externals/googletest. Please run: git submodule update --init --recursive")
    endif()

    # Suppress warnings from GTest itself for Clang/IntelLLVM during compilation
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "IntelLLVM")
        set(GTEST_SUPPRESS_FLAGS -Wno-unknown-warning-option -Wno-character-conversion)
        if(CMAKE_CXX_COMPILER_ID STREQUAL "IntelLLVM")
            list(APPEND GTEST_SUPPRESS_FLAGS -diag-disable=10430)
        endif()
        foreach(target gtest gtest_main gmock gmock_main)
            if(TARGET ${target})
                target_compile_options(${target} INTERFACE ${GTEST_SUPPRESS_FLAGS})
                target_compile_options(${target} PRIVATE ${GTEST_SUPPRESS_FLAGS})
            endif()
        endforeach()
    endif()

    enable_testing()
    include(GoogleTest)

    add_executable(test_ugrid_reader
        tests/test_ugrid_reader.cpp
    )

    target_compile_options(test_ugrid_reader PRIVATE ${WW4_COMMON_COMPILE_OPTIONS})
    target_link_options(test_ugrid_reader PRIVATE ${WW4_COMMON_LINK_OPTIONS})

    if(TARGET GTest::gtest_main)
        target_link_libraries(test_ugrid_reader PRIVATE
            ww4_ugrid_reader
            GTest::gtest_main
        )
    else()
        target_link_libraries(test_ugrid_reader PRIVATE
            ww4_ugrid_reader
            gtest_main
        )
    endif()

    gtest_discover_tests(test_ugrid_reader)
endif()
