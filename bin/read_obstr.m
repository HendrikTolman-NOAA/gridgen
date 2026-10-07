function [m1,m2] = read_obstr(fname,Nx,Ny)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file read_obstr.m
% @brief Reads sub-grid obstruction factors from a WAVEWATCH ASCII obstruction file.
% @details Parses 2D obstruction factors (sx, sy) of size (Ny, Nx) from a formatted ASCII file.
%
% @param[in] fname Path to input obstruction file.
% @param[in] Nx Number of grid columns.
% @param[in] Ny Number of grid rows.
% @return m1 2D sub-grid obstruction array in x direction (sx).
% @return m2 2D sub-grid obstruction array in y direction (sy).
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
   a = fscanf(fid,'%d',Nx*Ny);
   m1 = (reshape(a,Nx,Ny))';
   a = fscanf(fid,'%d',Nx*Ny);
   m2 = (reshape(a,Nx,Ny))';
else
   fprintf(1,'!!ERROR!!: %s \n',messg);
end;

fclose(fid);
return;
