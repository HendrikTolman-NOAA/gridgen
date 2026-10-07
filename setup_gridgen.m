function setup_gridgen
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file setup_gridgen.m
% @brief Setup function for the WAVEWATCH grid generation package.
% @details Downloads ETOPO1 and ETOPO2 reference datasets, uncompresses the tarball archive, and adds gridgen directories to the MATLAB search path.
%
% @copyright © 2009-2026 National Weather Service, National Oceanic and Atmospheric
% Administration. WAVEWATCH IV (TM) and WW4 (TM) are trademarks of the National
% Weather Service.
% NWS often uses Generative AI (GenAI) for code development and refactoring.
% Whenever GenAI is used, NWS requires a full human review of code before it is
% added to its repositories.
%
% @author Main Author(s): Aldgisl (AI Persona), Hendrik L. Tolman
% @author Contributors: Jules (Agentic AI), Stylianos Flampouris
% @date Initial, 2009-01-01
% @date Last update : 2026-10-07
%
% @note Originally distributed with WAVEWATCH III gridgen package.
%
%%
display('grid_gen installation!')
%% Define paths, files and ftp server and paths
home = fileparts(which(mfilename)); % grid_gen directory
path_tar='reference_data';          % reference data path
path_bin='bin';                     % bin path
path_exm='examples';                % examples path
%
ftp_svr='polar.ncep.noaa.gov';      % ftp server of reference data
ftp_pth='/waves/gridgen';           % ftp path for reference data
bathy_file='gridgen_addit.tar.gz';     % reference data tarball
%% Downloading
if exist([home,'/',path_tar,'/etopo1.nc'], 'file') ~= 2
    ftp_ind=ftp(ftp_svr);
    cd(ftp_ind,ftp_pth);
    mget(ftp_ind,bathy_file,home);
    close(ftp_ind);
%% Untar the reference data
    untar([home,'/',bathy_file],path_tar);
%
    delete([home,'/',bathy_file]);
end
%% Add the bin, reference path and examples to the user's matlab path
addpath(fullfile(home, path_bin))
addpath(fullfile(home, path_tar));
addpath(fullfile(home, path_exm));

%% Install NetCDF package for octave
vers=ver;
% interpreter='Matlab';
% netcdf_install='false';
for i1=1:1:length(vers)
    if strcmpi (vers(i1).Name, 'Octave')
        pkg install -forge netcdf
    end
end
