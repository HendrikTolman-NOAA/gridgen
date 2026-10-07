function m = read_mask(fname,Nx,Ny)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file read_mask.m
% @brief Reads a WAVEWATCH ASCII mask file into a 2D array.
% @details Parses an ASCII formatted land/sea mask file and returns a 2D matrix of size (Ny, Nx).
%
% @param[in] fname Path to input mask file.
% @param[in] Nx Number of grid columns.
% @param[in] Ny Number of grid rows.
% @return m 2D land/sea mask array.
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
   a = fscanf(fid,'%d');
   m = (reshape(a,Nx,Ny))';
else
   fprintf(1,'!!ERROR!!: %s \n',messg);
end;

fclose(fid);
return;
