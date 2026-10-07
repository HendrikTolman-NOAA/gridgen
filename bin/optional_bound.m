function [b,usr_cnt] = optional_bound(ref_dir,fname)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file optional_bound.m
% @brief Loads optional user-defined coastal polygon boundaries.
% @details Parses user_polygons.flag and loads active user-defined coastal boundary polygons into the boundary structure.
%
% @param[in] ref_dir Path to reference data directory.
% @param[in] fname Path to user polygon flag file.
% @return b Data structure array of user boundary polygons.
% @return usr_cnt Count of user boundary polygons.
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

load([ref_dir,'/optional_coastal_polygons.mat']);

N = length(user_bound);
usr_cnt = 0;

for i = 1:N
    a = fgetl(fid);    
    a1= sscanf(a,'%d%d');
    if (a1(2) == 1)
        b(usr_cnt+1) = user_bound(i);
        usr_cnt = usr_cnt+1;
        b(usr_cnt).west = min(b(usr_cnt).x);
        b(usr_cnt).east = max(b(usr_cnt).x);
    end;
end;
fclose(fid);

if (usr_cnt == 0)
  b(1) = -1;
end;

return
