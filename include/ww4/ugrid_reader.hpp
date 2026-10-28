// WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
//
// Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
// NWS often uses Generative AI (GenAI) for code development and refactoring.
// Whenever GenAI is used, NWS requires a full human review of code before it
// is added to its repositories.
//
// @file ugrid_reader.hpp
// @brief NetCDF-UGRID 1.0 grid file reader using netcdf-c for WAVEWATCH IV.
// @author Aldgisl (Agentic AI), Hendrik Tolman
// @author Jules (Agentic AI) (contributor)
// @date Initial: 2026-10-27
// @date Latest Update: 2026-10-28

#ifndef WW4_UGRID_READER_HPP
#define WW4_UGRID_READER_HPP

#include <cstdint>
#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace ww4::io {

/**
 * @brief Container structure holding data and metadata read from a WW4 NetCDF-UGRID grid file.
 */
struct UgridGrid {
    /// 2D grid y-dimension (number of rows)
    std::size_t ny{0};
    /// 2D grid x-dimension (number of columns)
    std::size_t nx{0};
    /// Number of mesh face cells (ny * nx)
    std::size_t n_faces{0};
    /// Number of mesh nodes
    std::size_t n_nodes{0};
    /// Maximum number of nodes per face cell (typically 4)
    std::size_t max_face_nodes{0};

    /// Global title attribute
    std::string title;
    /// Global source attribute
    std::string source;
    /// Global bathy_source attribute
    std::string bathy_source;
    /// Global bound_source attribute
    std::string bound_source;
    /// Global Conventions attribute
    std::string conventions;
    /// Global history attribute
    std::string history;

    /// Complete map of all global attributes
    std::map<std::string, std::string> global_attrs;

    /// Flag indicating whether subgrid x-obstruction array is present
    bool has_obsx{false};
    /// Flag indicating whether subgrid y-obstruction array is present
    bool has_obsy{false};

    /// 2D longitude grid coordinates (degrees_east), shape (ny, nx)
    std::vector<double> grid_lon;
    /// 2D latitude grid coordinates (degrees_north), shape (ny, nx)
    std::vector<double> grid_lat;
    /// 2D bathymetry depth grid (meters), shape (ny, nx)
    std::vector<float> grid_depth;
    /// 2D land/sea mask grid (0=dry, 1=wet), shape (ny, nx)
    std::vector<int32_t> grid_mask;
    /// Optional 2D subgrid x-obstruction grid, shape (ny, nx)
    std::vector<float> grid_ObsX;
    /// Optional 2D subgrid y-obstruction grid, shape (ny, nx)
    std::vector<float> grid_ObsY;

    /// 1D UGRID face center longitudes (n_faces)
    std::vector<double> face_lon;
    /// 1D UGRID face center latitudes (n_faces)
    std::vector<double> face_lat;
    /// 1D UGRID face depth values (n_faces)
    std::vector<float> depth;
    /// 1D UGRID face mask values (n_faces)
    std::vector<int32_t> mask;
    /// Optional 1D UGRID face x-obstruction values (n_faces)
    std::vector<float> ObsX;
    /// Optional 1D UGRID face y-obstruction values (n_faces)
    std::vector<float> ObsY;

    /// 1D UGRID mesh node longitudes (n_nodes)
    std::vector<double> node_lon;
    /// 1D UGRID mesh node latitudes (n_nodes)
    std::vector<double> node_lat;

    /// Face-node connectivity map (n_faces * max_face_nodes)
    std::vector<int32_t> face_node_connectivity;
};

/**
 * @brief Pure subroutine to read a WAVEWATCH IV NetCDF-UGRID 1.0 grid file using netcdf-c API.
 *
 * @details Opens the NetCDF file specified by `filepath` in read-only mode using netcdf-c API,
 * parses all global metadata attributes, grid dimensions, 2D curvilinear grid coordinate
 * and field arrays, and 1D UGRID mesh topology/coordinates/fields. All inputs and outputs
 * pass through the routine interface without stdio side effects.
 *
 * @param filepath Path to the NetCDF-UGRID file to read.
 * @return UgridGrid Struct containing all parsed metadata, 2D arrays, and 1D UGRID fields.
 * @pre File must exist and be a valid NetCDF / NetCDF-4 file.
 * @post Returned UgridGrid fields are populated with file contents.
 * @throws std::runtime_error If file opening fails or mandatory variables/dimensions are missing.
 */
[[nodiscard]] UgridGrid read_ugrid_nc(const std::filesystem::path& filepath);

} // namespace ww4::io

#endif // WW4_UGRID_READER_HPP
