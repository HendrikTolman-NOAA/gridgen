function [c1,c2,c3,c4,wdth,hgt] = compute_cellcorner(x,y,j,k,Nx,Ny)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file compute_cellcorner.m
% @brief Computes cell corner coordinates and cell dimensions for a grid cell.
% @details Calculates four corner coordinates and physical width and height for cell (j,k) in a 2D grid.
%
% @param[in] x 2D array specifying cell longitudes.
% @param[in] y 2D array specifying cell latitudes.
% @param[in] j Column index.
% @param[in] k Row index.
% @param[in] Nx Number of grid columns.
% @param[in] Ny Number of grid rows.
% @return c1 Corner 1 coordinates [lon, lat].
% @return c2 Corner 2 coordinates [lon, lat].
% @return c3 Corner 3 coordinates [lon, lat].
% @return c4 Corner 4 coordinates [lon, lat].
% @return wdth Cell width in longitude degrees.
% @return hgt Cell height in latitude degrees.
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

% Initialize variables

c1 = [];
c2 = [];
c3 = [];
c4 = [];

x0 = x(k,j);
% Compute the corners of the cell

if ( j > 1 && j < Nx && k > 1 && k < Ny )
    
    % Internal points
    
    xt = x(k-1,j+1);
    if (abs(xt - x0) > 270)
        xt = xt - 360*sign(xt-x0);
    end;
    c1(1) = 0.5*(xt+x0);
    c1(2) = 0.5*(y(k-1,j+1) + y(k,j));
    xt = x(k+1,j+1);
    if (abs(xt - x0) > 270)
        xt = xt - 360*sign(xt-x0);
    end;
    c2(1) = 0.5*(xt+x0);
    c2(2) = 0.5*(y(k+1,j+1) + y(k,j));
    xt = x(k+1,j-1);
    if (abs(xt - x0) > 270)
        xt = xt - 360*sign(xt-x0);
    end;
    c3(1) = 0.5*(xt+x0);
    c3(2) = 0.5*(y(k+1,j-1) + y(k,j));
    xt = x(k-1,j-1);
    if (abs(xt - x0) > 270)
        xt = xt - 360*sign(xt-x0);
    end;
    c4(1) = 0.5*(xt+x0);
    c4(2) = 0.5*(y(k-1,j-1) + y(k,j));
    
    
else
    
    if ( j == 1 )
        
        % Left edge
        
        switch k
            case 1
                xt = x(k+1,j+1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c2(1) = 0.5*(xt+x0);
                c2(2) = 0.5*(y(k+1,j+1) + y(k,j));
                c4(1) = 2*x0 - c2(1);
                c4(2) = 2*y(k,j) - c2(2);
                c3(1) = x0 - (c2(2)-y(k,j));
                c3(2) = y(k,j) + (c2(1)-x(k,j));
                c1(1) = 2*x0 - c3(1);
                c1(2) = 2*y(k,j) - c3(2);
            case Ny
                xt = x(k-1,j+1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c1(1) = 0.5*(xt+x0);
                c1(2) = 0.5*(y(k-1,j+1) + y(k,j));
                c3(1) = 2*x0 - c1(1);
                c3(2) = 2*y(k,j) - c1(2);
                c2(1) = x0 - (y(k,j)-c1(2));
                c2(2) = y(k,j) + (x0-c1(1));
                c4(1) = 2*x0 - c2(1);
                c4(2) = 2*y(k,j) - c2(2);
            otherwise
                xt = x(k-1,j+1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c1(1) = 0.5*(xt+x0);
                c1(2) = 0.5*(y(k-1,j+1) + y(k,j));
                xt = x(k+1,j+1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c2(1) = 0.5*(xt+x0);
                c2(2) = 0.5*(y(k+1,j+1) + y(k,j));
                c3(1) = 2*x0 - c1(1);
                c3(2) = 2*y(k,j) - c1(2);
                c4(1) = 2*x0 - c2(1);
                c4(2) = 2*y(k,j) - c2(2);
        end;
        
    else
        
        if ( j == Nx )
            
            % Right edge
            
            switch k
                case 1
                    xt = x(k+1,j-1);
                    if (abs(xt - x0) > 270)
                        xt = xt - 360*sign(xt-x0);
                    end;
                    c3(1) = 0.5*(xt+x0); 
                    c3(2) = 0.5*(y(k+1,j-1) + y(k,j));
                    c2(1) = x0 - (c3(2)-y(k,j));
                    c2(2) = y(k,j) + (c3(1)-x0);
                    c1(1) = 2*x0 - c3(1);
                    c1(2) = 2*y(k,j) - c3(2);
                    c4(1) = 2*x0 - c2(1);
                    c4(2) = 2*y(k,j) - c2(2);
                case Ny
                    xt = x(k-1,j-1);
                    if (abs(xt - x0) > 270)
                        xt = xt - 360*sign(xt-x0);
                    end;
                    c4(1) = 0.5*(xt+x0);
                    c4(2) = 0.5*(y(k-1,j-1) + y(k,j));
                    c3(1) = x0 - (c4(2)-y(k,j));
                    c3(2) = y(k,j) + (c4(1)-x0);
                    c1(1) = 2*x0 - c3(1);
                    c1(2) = 2*y(k,j) - c3(2);
                    c2(1) = 2*x0 - c4(1);
                    c2(2) = 2*y(k,j) - c4(2);
                otherwise
                    xt = x(k+1,j-1);
                    if (abs(xt - x0) > 270)
                        xt = xt - 360*sign(xt-x0);
                    end;
                    c3(1) = 0.5*(xt+x0);
                    c3(2) = 0.5*(y(k+1,j-1) + y(k,j));
                    xt = x(k-1,j-1);
                    if (abs(xt - x0) > 270)
                        xt = xt - 360*sign(xt-x0);
                    end;
                    c4(1) = 0.5*(xt+x0);
                    c4(2) = 0.5*(y(k-1,j-1) + y(k,j));
                    c1(1) = 2*x0 - c3(1);
                    c1(2) = 2*y(k,j) - c3(2);
                    c2(1) = 2*x0 - c4(1);
                    c2(2) = 2*y(k,j) - c4(2);
            end;
            
        else
            
            if ( k == 1 )
                
                % Bottom edge
                
                xt = x(k+1,j+1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c2(1) = 0.5*(xt+x0); 
                c2(2) = 0.5*(y(k+1,j+1) + y(k,j));
                xt = x(k+1,j-1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c3(1) = 0.5*(xt+x0);
                c3(2) = 0.5*(y(k+1,j-1) + y(k,j));
                c4(1) = 2*x0 - c2(1);
                c4(2) = 2*y(k,j) - c2(2);
                c1(1) = 2*x0 - c3(1);
                c1(2) = 2*y(k,j) - c3(2);
                
            else
                
                % Top edge
                
                xt = x(k-1,j-1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c4(1) = 0.5*(xt+x0);
                c4(2) = 0.5*(y(k-1,j-1) + y(k,j));
                xt = x(k-1,j+1);
                if (abs(xt - x0) > 270)
                    xt = xt - 360*sign(xt-x0);
                end;
                c1(1) = 0.5*(xt+x0);
                c1(2) = 0.5*(y(k-1,j+1) + y(k,j));
                c2(1) = 2*x0 - c4(1);
                c2(2) = 2*y(k,j) - c4(2);
                c3(1) = 2*x0 - c1(1);
                c3(2) = 2*y(k,j) - c1(2);
                
            end;
            
        end;
        
    end;
    
end;

dx = c1(1)-c4(1);
%argd = min([1 (cosd(c1(2))*cosd(c4(2))*cosd(dx) + sind(c1(2))*sind(c4(2)))]);
%wdth = acosd(argd);
wdth = sqrt((c1(1)-c4(1))^2+(c1(2)-c4(2))^2);
%dx = c2(1)-c1(1);
%argd = min([1 (cosd(c2(2))*cosd(c1(2))*cosd(dx) + sind(c2(2))*sind(c1(2)))]);
%hgt = acosd(argd);
hgt = sqrt((c2(1)-c1(1))^2+(c2(2)-c1(2))^2);

return;
