// WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
//
// Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
// NWS often uses Generative AI (GenAI) for code development and refactoring.
// Whenever GenAI is used, NWS requires a full human review of code before it
// is added to its repositories.
//
// @file test_ugrid_reader.cpp
// @brief Unit tests for NetCDF-UGRID C++ reader using GoogleTest.
// @author Aldgisl (Agentic AI), Hendrik Tolman
// @author Jules (Agentic AI) (contributor)
// @date Initial: 2026-10-27
// @date Latest Update: 2026-10-30

#include "UQ_read_grid.h"

#include <gtest/gtest.h>

#include <cstdlib>
#include <fstream>
#include <filesystem>
#include <stdexcept>
#include <string>

namespace {

/**
 * @brief Helper function to generate a test NetCDF-UGRID file using Python ww4gridgen package.
 */
void create_test_ugrid_nc(const std::filesystem::path& filepath, const bool include_obstructions) {
    std::string python_cmd =
        "python3 -c \"import numpy as np; from gridgen.io.ugrid import create_ugrid_dataset, write_ugrid_nc; "
        "x = np.array([[0.0, 1.0], [0.0, 1.0]], dtype=float); "
        "y = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=float); "
        "depth = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=float); "
        "mask = np.array([[1, 1], [0, 1]], dtype=int); ";

    if (include_obstructions) {
        python_cmd +=
            "obsx = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float); "
            "obsy = np.array([[0.5, 0.6], [0.7, 0.8]], dtype=float); "
            "ds = create_ugrid_dataset(x, y, depth, mask, obsx, obsy, bathy_source='etopo2', grid_type='regular', coord_type='spherical', global_closure=True); ";
    } else {
        python_cmd +=
            "ds = create_ugrid_dataset(x, y, depth, mask, bathy_source='etopo2', grid_type='stereographic', coord_type='cartesian', global_closure=False); ";
    }

    python_cmd += "write_ugrid_nc(ds, '" + filepath.string() + "')\"";

    const int status = std::system(python_cmd.c_str());
    if (status != 0) {
        throw std::runtime_error("Failed to execute python command to generate test UGRID file.");
    }
}

} // namespace

class UgridReaderTest : public ::testing::Test {
protected:
    std::filesystem::path test_nc_file_with_obs;
    std::filesystem::path test_nc_file_no_obs;
    std::filesystem::path invalid_file;

    void SetUp() override {
        test_nc_file_with_obs = std::filesystem::temp_directory_path() / "test_ugrid_with_obs.nc";
        test_nc_file_no_obs = std::filesystem::temp_directory_path() / "test_ugrid_no_obs.nc";
        invalid_file = std::filesystem::temp_directory_path() / "invalid_file.txt";

        create_test_ugrid_nc(test_nc_file_with_obs, true);
        create_test_ugrid_nc(test_nc_file_no_obs, false);

        std::ofstream ofs(invalid_file);
        ofs << "This is not a NetCDF file." << std::endl;
        ofs.close();
    }

    void TearDown() override {
        std::error_code ec;
        std::filesystem::remove(test_nc_file_with_obs, ec);
        std::filesystem::remove(test_nc_file_no_obs, ec);
        std::filesystem::remove(invalid_file, ec);
    }
};

TEST_F(UgridReaderTest, ReadUgridNcFileWithObstructions) {
    ww4::io::UgridGrid grid;
    EXPECT_EQ(ww4::io::readUQgrid(test_nc_file_with_obs, grid), 0);

    // Verify dimensions
    EXPECT_EQ(grid.ny, 2u);
    EXPECT_EQ(grid.nx, 2u);
    EXPECT_EQ(grid.n_faces, 4u);
    EXPECT_EQ(grid.max_face_nodes, 4u);
    EXPECT_EQ(grid.n_nodes, 9u);

    // Verify metadata attributes
    EXPECT_FALSE(grid.conventions.empty());
    EXPECT_FALSE(grid.source.empty());
    EXPECT_EQ(grid.grid_type, "regular");
    EXPECT_EQ(grid.coord_type, "spherical");
    EXPECT_EQ(grid.global_closure, "true");
    EXPECT_EQ(grid.bathy_source, "etopo2");
    EXPECT_FALSE(grid.global_attrs.empty());
    EXPECT_EQ(grid.global_attrs.at("bathy_source"), "etopo2");
    EXPECT_EQ(grid.global_attrs.at("grid_type"), "regular");
    EXPECT_EQ(grid.global_attrs.at("coord_type"), "spherical");
    EXPECT_EQ(grid.global_attrs.at("global_closure"), "true");

    // Verify obstruction flags
    EXPECT_TRUE(grid.has_obsx);
    EXPECT_TRUE(grid.has_obsy);

    // Verify 2D arrays
    EXPECT_EQ(grid.grid_lon.size(), 4u);
    EXPECT_EQ(grid.grid_lat.size(), 4u);
    EXPECT_EQ(grid.grid_depth.size(), 4u);
    EXPECT_EQ(grid.grid_mask.size(), 4u);
    EXPECT_EQ(grid.grid_ObsX.size(), 4u);
    EXPECT_EQ(grid.grid_ObsY.size(), 4u);

    EXPECT_FLOAT_EQ(grid.grid_depth[0], 10.0f);
    EXPECT_FLOAT_EQ(grid.grid_depth[3], 40.0f);
    EXPECT_EQ(grid.grid_mask[0], 1);
    EXPECT_EQ(grid.grid_mask[2], 0);

    EXPECT_FLOAT_EQ(grid.grid_ObsX[0], 0.1f);
    EXPECT_FLOAT_EQ(grid.grid_ObsY[3], 0.8f);

    // Verify 1D UGRID face arrays
    EXPECT_EQ(grid.face_lon.size(), 4u);
    EXPECT_EQ(grid.face_lat.size(), 4u);
    EXPECT_EQ(grid.depth.size(), 4u);
    EXPECT_EQ(grid.mask.size(), 4u);
    EXPECT_EQ(grid.ObsX.size(), 4u);
    EXPECT_EQ(grid.ObsY.size(), 4u);

    // Verify node and connectivity
    EXPECT_EQ(grid.node_lon.size(), 9u);
    EXPECT_EQ(grid.node_lat.size(), 9u);
    EXPECT_EQ(grid.face_node_connectivity.size(), 16u);
}

TEST_F(UgridReaderTest, ReadUgridNcFileWithoutObstructions) {
    ww4::io::UgridGrid grid;
    EXPECT_EQ(ww4::io::readUQgrid(test_nc_file_no_obs, grid), 0);

    EXPECT_EQ(grid.ny, 2u);
    EXPECT_EQ(grid.nx, 2u);
    EXPECT_EQ(grid.n_faces, 4u);

    EXPECT_EQ(grid.grid_type, "stereographic");
    EXPECT_EQ(grid.coord_type, "cartesian");
    EXPECT_EQ(grid.global_closure, "false");

    EXPECT_FALSE(grid.has_obsx);
    EXPECT_FALSE(grid.has_obsy);

    EXPECT_TRUE(grid.grid_ObsX.empty());
    EXPECT_TRUE(grid.grid_ObsY.empty());
    EXPECT_TRUE(grid.ObsX.empty());
    EXPECT_TRUE(grid.ObsY.empty());
}

TEST_F(UgridReaderTest, FileNotFoundFailure) {
    const std::filesystem::path non_existent = std::filesystem::temp_directory_path() / "non_existent_grid_file_12345.nc";
    ww4::io::UgridGrid grid;
    EXPECT_EQ(ww4::io::readUQgrid(non_existent, grid), 1);
}

TEST_F(UgridReaderTest, InvalidNcFileFailure) {
    ww4::io::UgridGrid grid;
    EXPECT_NE(ww4::io::readUQgrid(invalid_file, grid), 0);
}
