function [messg,errno] = write_ww3obstr(fname,d1,d2)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file write_ww3obstr.m
% @brief Writes sub-grid obstruction factors (sx, sy) to a WAVEWATCH ASCII obstruction file.
% @details Outputs 2D sx and sy obstruction matrices to an ASCII grid file.
%
% @param[in] fname Output filename path.
% @param[in] d1 2D sub-grid obstruction array in x direction (sx).
% @param[in] d2 2D sub-grid obstruction array in y direction (sy).
% @return messg Status or error message string.
% @return errno Error flag (0 for success).
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

[Ny,Nx] = size(d1);

fid = fopen(fname,'w');

[messg,errno] = ferror(fid);

if (errno == 0)
   for i = 1:Ny
       a = d1(i,:);
       fprintf(fid,' %d ',a);
       fprintf(fid,'\n');
   end;
   fprintf(fid,'\n');
   for i = 1:Ny
       a = d2(i,:);
       fprintf(fid,' %d ',a);
       fprintf(fid,'\n');
   end;
else
   fprintf(1,'!!ERROR!!: %s \n',messg);
end;

fclose(fid);

return;
