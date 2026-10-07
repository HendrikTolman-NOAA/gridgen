function [m1_out,m2_out] = reconcile_masks(m1,lon1,lat1,m2,lon2,lat2 )
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file reconcile_masks.m
% @brief Reconciles land/sea masks between two overlapping WAVEWATCH grids.
% @details Ensures consistency of active and dry cells in overlap regions between grid 1 and grid 2.
%
% @param[in] m1 Mask array of grid 1.
% @param[in] lon1 Longitudes of grid 1.
% @param[in] lat1 Latitudes of grid 1.
% @param[in] m2 Mask array of grid 2.
% @param[in] lon2 Longitudes of grid 2.
% @param[in] lat2 Latitudes of grid 2.
% @return m1_out Reconciled mask array for grid 1.
% @return m2_out Reconciled mask array for grid 2.
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

% Determine overlap points

[Nx1,Ny1] = size(m1);
[Nx2,Ny2] = size(m2);

if (Nx1*Ny1 <= Nx2*Ny2)
    px = [lon2(1) lon2(end) lon2(end) lon2(1) lon2(1)];
    py = [lat2(1) lat2(1) lat2(end) lat2(end) lat2(1)];
    [x,y] = meshgrid(lon1,lat1);
    lonb = lon2;
    latb = lat2;
    dx = lon1(2) - lon1(1);
    dy = lat1(2) - lat1(1);
    Nt = Nx1*Ny1;
    mt = m1;
    mb = m2;
else
    px = [lon1(1) lon1(end) lon1(end) lon1(1) lon1(1)];
    py = [lat1(1) lat1(1) lat1(end) lat1(end) lat1(1)];
    [x,y] = meshgrid(lon2,lat2);
    lonb = lon1;
    latb = lat1;
    dx = lon2(2) - lon2(1);
    dy = lat2(2) - lat2(1);
    Nt = Nx2*Ny2;
    mt = m2;
    mb = m1;
end

% Determine region of overlap

inout = inpolygon(x,y,px,py);
loc = find(inout > 0);
N = length(loc);

fprintf(1,' Found %d per cent of grid overlap points\n',round(N*100./Nt));

% Check masks for overlap points

for i = 1:N
    lon = x(loc(i));
    lat = y(loc(i));
    [xmin,jpos] = min(abs(lon-lonb));
    [ymin,ipos] = min(abs(lat-latb));
    if (max(abs(xmin),abs(ymin)) > min(abs(dx),abs(dy)))
        fprintf(1,' Error ! Closest points are too far ! \n');
        return;
    end;
    
    if (mt(loc(i)) ~= mb(ipos,jpos) )
        if (mt(loc(i)) ~=2 && mb(ipos,jpos) ~=2)
           mt(loc(i)) = 0;
           mb(ipos,jpos) = 0;
        end;
    end;
end;

if (Nx1*Ny1 <= Nx2*Ny2)
    m1_out = mt;
    m2_out = mb;
else
    m1_out = mb;
    m2_out = mt;
end;

return;

