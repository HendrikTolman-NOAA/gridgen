// WAVEWATCH III (WW3) / WAVEWATCH IV (WW4) Gridgen Package
//
// Copyright 2026 National Weather Service (NWS), NOAA. All rights reserved.
// NWS often uses Generative AI (GenAI) for code development and refactoring.
// Whenever GenAI is used, NWS requires a full human review of code before it
// is added to its repositories.
//
// @file read_grid.cpp
// @brief Utility program to read a NetCDF grid file and print all metadata.
// @author Aldgisl (Agentic AI), Hendrik Tolman
// @author Jules (Agentic AI) (contributor)
// @date Initial: 2026-10-28
// @date Latest Update: 2026-10-28

#include "ww4/ugrid_reader.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <limits>

namespace {

/**
 * @brief Utility function to print a section header banner.
 */
void print_header(const std::string& title) {
    std::cout << "\n========================================================================\n"
              << " " << title << "\n"
              << "========================================================================\n";
}

} // namespace

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <path_to_grid_file.nc>\n";
        return 1;
    }

    const std::filesystem::path filepath(argv[1]);

    try {
        const ww4::io::UgridGrid grid = ww4::io::read_ugrid_nc(filepath);

        print_header("WW4 NetCDF-UGRID Grid Metadata Summary");
        std::cout << " File Path            : " << filepath.string() << "\n";
        std::cout << " Title                : " << (grid.title.empty() ? "(none)" : grid.title) << "\n";
        std::cout << " Source               : " << (grid.source.empty() ? "(none)" : grid.source) << "\n";
        std::cout << " Bathymetry Source    : " << (grid.bathy_source.empty() ? "(none)" : grid.bathy_source) << "\n";
        std::cout << " Boundary Source      : " << (grid.bound_source.empty() ? "(none)" : grid.bound_source) << "\n";
        std::cout << " Conventions          : " << (grid.conventions.empty() ? "(none)" : grid.conventions) << "\n";
        std::cout << " History              : " << (grid.history.empty() ? "(none)" : grid.history) << "\n";

        print_header("Global Attributes (" + std::to_string(grid.global_attrs.size()) + ")");
        for (const auto& [key, value] : grid.global_attrs) {
            std::cout << " " << key << " = " << value << "\n";
        }

        print_header("Grid Dimensions");
        std::cout << " NY (Latitude/Y rows) : " << grid.ny << "\n";
        std::cout << " NX (Longitude/X cols): " << grid.nx << "\n";
        std::cout << " Faces (ny * nx)      : " << grid.n_faces << "\n";
        std::cout << " Mesh Nodes           : " << grid.n_nodes << "\n";
        std::cout << " Max Nodes per Face   : " << grid.max_face_nodes << "\n";

        print_header("Field Characteristics & Statistics");
        if (!grid.grid_depth.empty()) {
            float min_depth = std::numeric_limits<float>::max();
            float max_depth = std::numeric_limits<float>::lowest();
            for (const float d : grid.grid_depth) {
                if (!std::isnan(d)) {
                    min_depth = std::min(min_depth, d);
                    max_depth = std::max(max_depth, d);
                }
            }
            std::cout << " Depth Range          : " << min_depth << " m to " << max_depth << " m\n";
        }

        std::size_t wet_count = 0;
        std::size_t dry_count = 0;
        for (const int32_t m : grid.grid_mask) {
            if (m != 0) {
                ++wet_count;
            } else {
                ++dry_count;
            }
        }
        std::cout << " Mask Cells           : " << wet_count << " wet, " << dry_count << " dry\n";
        std::cout << " Has Obstructions     : ObsX=" << (grid.has_obsx ? "Yes" : "No")
                  << ", ObsY=" << (grid.has_obsy ? "Yes" : "No") << "\n";

        std::cout << "\nGrid file read successfully.\n";
        return 0;

    } catch (const std::exception& ex) {
        std::cerr << "Error reading grid file '" << filepath.string() << "': " << ex.what() << "\n";
        return 1;
    }
}
