function [lon,lat] = read_ww3meta(fname)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file read_ww3meta.m
% @brief Reads grid metadata from a WAVEWATCH meta file.
% @details Parses grid metadata (.meta) file to reconstruct longitude and latitude coordinate arrays.
%
% @param[in] fname Path to input metadata file.
% @return lon Longitude coordinate vector or 2D matrix.
% @return lat Latitude coordinate vector or 2D matrix.
%
% @copyright © 2009-2026 National Weather Service, National Oceanic and Atmospheric
% Administration. WAVEWATCH IV (TM) and WW4 (TM) are trademarks of the National
% Weather Service.
% NWS often uses Generative AI (GenAI) for code development and refactoring.
% Whenever GenAI is used, NWS requires a full human review of code before it is
% added to its repositories.
%
% @author Main Author(s): Aldgisl (AI Persona), Hendrik L. Tolman
% @author Contributors: Jules (Agentic AI)
% @date Initial, 2009-01-01
% @date Last update : 2026-10-07
%
% @note Originally distributed with WAVEWATCH III gridgen package.
%

fid = fopen(fname,'r');

[messg,errno] = ferror(fid);

if (errno == 0)
   for i = 1:45
       tmp = fgetl(fid);
   end;
   
   % Grid Type
   tmp = fgetl(fid);
   gtype = sscanf(tmp,'%s',1);
   
   if (strmatch(gtype,'''RECT'''))
      Nx = fscanf(fid,'%d',1);
      Ny = fscanf(fid,'%d',1);
      dx = fscanf(fid,'%f',1);
      dy = fscanf(fid,'%f',1);
      scale = fscanf(fid,'%f',1);
      dx = dx/scale;
      dy = dy/scale;
      lons = fscanf(fid,'%f',1);
      lats = fscanf(fid,'%f',1);
      scale = fscanf(fid,'%f',1);

      lon1d = lons/scale + [0:(Nx-1)]*dx;
      lat1d = lats/scale + [0:(Ny-1)]*dy;

      [lon,lat] = meshgrid(lon1d,lat1d);

   else
 
      fprintf(1,' read_ww3meta has been designed for determining coordinates for rectlinwae grids only \n');
    
   end; 
      

else
   fprintf(1,'!!ERROR!!: %s \n',messg);
end;

fclose(fid);

return;
