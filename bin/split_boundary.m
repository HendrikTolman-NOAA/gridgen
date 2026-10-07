function bound_ingrid = split_boundary(bound,lim)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file split_boundary.m
% @brief Splits boundary polygons across a specified polygon line segment.
% @details Modifies boundary polygons intersecting a user-defined polygon line segment.
%
% @param[in] bound Active boundary polygon structure array.
% @param[in] lim Splitting limit/threshold.
% @return bound_ingrid Updated boundary structure array.
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

eps = 1e-5;

N = length(bound);
in_coord = 1;
bound_ingrid = [];
itmp = 0;

for i = 1:N  
    if (bound(i).width > lim || bound(i).height > lim)
        low = floor(bound(i).west);
        high = ceil(bound(i).east);
        x_axis = [low:lim:high];
        if x_axis(end) < high
            x_axis(end+1) = high;
        end;
        low = floor(bound(i).south);
        high = ceil(bound(i).north);
        y_axis = [low:lim:high];
        if y_axis(end) < high
            y_axis(end+1) = high;
        end;
        
        Nx = length(x_axis);
        Ny = length(y_axis);
        for lx = 1:Nx-1
            for ly = 1:Ny-1
                lat_start = y_axis(ly);
                lon_start = x_axis(lx);
                lat_end = y_axis(ly+1);
                lon_end = x_axis(lx+1);
                
                [lat_start lon_start lat_end lon_end];
                [bt,Nb] = compute_boundary([lat_start lon_start lat_end ...
                    lon_end],bound(i),bound(i).level); 
                if (Nb > 0)
                    bound_ingrid = [bound_ingrid bt];
                    in_coord = in_coord + Nb;
                end;
                clear bt;
            end;
        end;
    else
        if (isempty(bound_ingrid))
            bound_ingrid = bound(i);
        else
            bound_ingrid(in_coord) = bound(i);
        end;
        in_coord = in_coord+1;
    end;
    itmp_prev = itmp;
    itmp = floor(i/N*100);
    if (mod(itmp,5)==0 && itmp_prev ~= itmp && N > 100)
        fprintf(1,'Completed %d per cent of %d boundaries and split into %d boundaries \n',...
            itmp,N,in_coord-1);
    end;
end;   

return;
