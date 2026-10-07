function depth_sub = generate_grid(x,y,ref_dir,bathy_source,limit,cut_off,dry,varargin)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file generate_grid.m
% @brief Generates a 2D bathymetry dataset from high-resolution global reference datasets.
% @details Interpolates or averages depth values from ETOPO1 or ETOPO2 global bathymetry onto target grid coordinates.
%
% @param[in] x 2D array specifying cell longitudes.
% @param[in] y 2D array specifying cell latitudes.
% @param[in] ref_dir Path to directory where global reference bathymetry datasets are stored.
% @param[in] bathy_source Bathymetry source identifier ('etopo1', 'etopo2', or custom).
% @param[in] limit Fraction (0 to 1) of wet base cells required to mark grid cell as wet.
% @param[in] cut_off Cut-off depth distinguishing between wet and dry cells.
% @param[in] dry Depth value assigned to dry cells.
% @param[in] varargin Optional custom variable names for NetCDF lon, lat, and depth.
% @return depth_sub 2D array of grid bathymetry depths.
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
% Octave Friendly
vers=ver;
for i1=1:1:length(vers)
    if strcmpi (vers(i1).Name, 'Octave')
        pkg load netcdf;
        import_netcdf;
    end
end

% Read additional input variables if they exist (read arbitrary base depth)
narg=nargin;

% Determine if third input variable present (requesting inland features)
if narg == 10 % Extra 3 arguments define the lat, lon and depth var names
    var_x = varargin{1};
    var_y = varargin{2};
    var_z = varargin{3};
    bathy_custom = bathy_source;    
elseif narg == 7
    bathy_custom='none';
elseif narg < 7
  disp('Too few input arguments, exiting')
else
  disp('Too many input arguments, exiting')
end

% Initialize the corners of the grid domain and the depth values

lats = min(min(y));
lons = min(min(x));
late = max(max(y));
lone = max(max(x));

depth_sub = zeros(size(x));

% Compute cell corners

[Ny,Nx] = size(x);

cell = repmat(struct('px',[],'py',[],'width',[],'height',[]),Nx,Ny);

for j = 1:Nx
    for k = 1:Ny    
        [c1,c2,c3,c4,wdth,hgt] = compute_cellcorner(x,y,j,k,Nx,Ny);
        cell(k,j).px = [c4(1) c1(1) c2(1) c3(1) c4(1)]';
        cell(k,j).py = [c4(2) c1(2) c2(2) c3(2) c4(2)]';
        cell(k,j).width = wdth;
        cell(k,j).height = hgt;        
    end;
end;

dx = max([cell(:).width]);
dy = max([cell(:).height]);

% Determine the file name for source bathymetry

if (strcmp(bathy_source,'etopo2'))
    fname_base = [ref_dir,'/etopo2.nc'];
    var_x = 'x';
    var_y = 'y';
    var_z = 'z';    
elseif (strcmp(bathy_source,'etopo1'))
    fname_base = [ref_dir,'/etopo1.nc'];
    var_x = 'lon';
    var_y = 'lat';
    var_z = 'z';    
elseif (strcmp(bathy_source,bathy_custom))
    fname_base = [ref_dir,'/',bathy_custom,'.nc'];
else
    fprintf(1,'Unrecognized source bathymetry option \n');
    return;
end;

% Determine dimensions and ranges of base bathymetry coords

f = netcdf.open(fname_base,'nowrite');

varid_lon = netcdf.inqVarID(f,var_x);
varid_lat = netcdf.inqVarID(f,var_y);
varid_dep = netcdf.inqVarID(f,var_z);

[~,Nx_base]=netcdf.inqDim(f,varid_lon);
[~,Ny_base]=netcdf.inqDim(f,varid_lat);

lat_range= netcdf.getAtt(f,varid_lat,'actual_range');
dy_base = diff(lat_range)/(Ny_base-1);

lats_base=lat_range(1);
late_base=lat_range(2);

lon_range= netcdf.getAtt(f,varid_lon,'actual_range');
dx_base = diff(lon_range)/(Nx_base-1);

lons_base=lon_range(1);
lone_base=lon_range(2); 

if (lats < lats_base || lats > late_base || late < lats_base || late > ...
        late_base)
    fprintf(1,'ERROR : Lattitudes (%d,%d) beyond range (%d,%d) \n',lats,...
        late,lats_base,late_base);
    return;
end;
  
if (lons < lons_base || lons > lone_base || lone < lons_base || lone > ...
        lone_base)
    fprintf(1,'ERROR : Longitudes (%d,%d) beyond range (%d,%d) \n',lons,...
        lone,lons_base,lone_base);
    return;
end;

% Determine the starting and end points for extracting lattitude data
% from NETCDF

lat_start = floor(( (lats-2*dy) - lats_base)/dy_base);

if (lat_start < 1)
    lat_start = 1;
end;
 
lat_end = ceil(((late+2*dy) - lats_base)/dy_base) +1;

if (lat_end > Ny_base)
    lat_end = Ny_base;
end;

% Determine the starting and end points for extracting longitude data
% from NETCDF

lon_start = floor(((lons-2*dx) - lons_base)/dx_base);
lon_end = ceil(((lone+2*dx) - lons_base)/dx_base) +1;

if (lon_start < 1)
    lon_start = 1;
end;

if (lon_start > Nx_base)
    lon_start = Nx_base;
end;

if (lon_end < 1)
    lon_end = 1;
end;

if (lon_end >Nx_base)
    lon_end = Nx_base;
end;    

% Extract data from Netcdf files
% The next few lines assume that your Matlab
% version has ability to read NETCDF files
% !! NOTE: Indexing from 0 for these functions!!


count_lat = (lat_end - lat_start) + 1;
lat_base = netcdf.getVar(f,varid_lat,lat_start-1,count_lat);             
                                                                  
if (lon_end <= lon_start)
    count_lon1 = (Nx_base - lon_start) + 1;                       
    count_lon2 = (lon_end - 2) + 1;                               
    lon1 = netcdf.getVar(f,varid_lon,lon_start-1,count_lon1);    
    lon2 = netcdf.getVar(f,varid_lon,1,count_lon2);               
    lon_base = [lon1;lon2];
    dep1 = ( netcdf.getVar(f,varid_dep,...
          [lon_start-1 lat_start-1],[count_lon1 count_lat]) )';   
    dep2 = ( netcdf.getVar(f,varid_dep,...
          [1 lat_start-1],[count_lon2 count_lat]) )';             
    depth_base = [dep1 dep2];
else
    count_lon = (lon_end - lon_start) + 1;                        
    lon_base = netcdf.getVar(f,varid_lon,lon_start-1,count_lon);  
    depth_base = ( netcdf.getVar(f,varid_dep,...
            [lon_start-1 lat_start-1],[count_lon count_lat]) )';  
end;

fprintf(1,'read in the base bathymetry \n');
netcdf.close(f);

%loc = find(lon_base < 0);
%lon_base(loc) = lon_base(loc)+360;
%if (lon_base(end) == 0)
%    lon_base(end) = lon_base(end)+360;
%end;

%Remove overlapped regions (occurs when longitudes wrap around)

clear lon_base_tmp depth_base_tmp ib;
lon_base_tmp = unique(lon_base);
[~,~,ib] = intersect(lon_base_tmp,lon_base);
depth_base_tmp = depth_base(:,ib);

clear lon_base depth_base;
lon_base = lon_base_tmp;
depth_base = depth_base_tmp;

% Obtaining data from base bathymetry. If desired grid is coarser than
% base grid then 2D averaging of bathymetry else grid is interpolated
% from base grid. Checks if grid cells wrap around in Longitudes. Does
% not do so for Lattitudes

itmp_prev = 0;
Nb = Nx*Ny;

fprintf(1,'Generating grid bathymetry ....\n');

for j = 1:Nx
    for k = 1:Ny
   
        ndx = round(cell(k,j).width/dx_base);
        ndy = round(cell(k,j).height/dy_base);

        if (ndx <= 1 && ndy <= 1)
    
        % Interpolating from base grid
        
            den = dx_base*dy_base;
%            [lon_prev,~] = min(abs(lon_base-x(k,j)));
%For very fine grids
            [lon_prev,tmp] = min(abs(lon_base-x(k,j)));
            if ( round(lon_prev) == 0 )
              lon_prev = tmp-1;
            end;
%
            if ( lon_base(lon_prev) > x(k,j) )
                lon_prev = lon_prev - 1;
            end;
            lon_next = lon_prev + 1;
            if (lon_prev == 0 ) 
                lon_prev = Nx_base - 1;
            end;
            if (lon_next > Nx_base)
                lon_next = 2;
            end;
%            [lat_prev,~] = min(abs(lat_base-y(k,j)));
%For very fine grids
             [lat_prev,tmp] = min(abs(lat_base-y(k,j)));
             if ( round(lat_prev) == 0 )
               lat_prev = tmp-1;
             end;
%            
            if ( lat_base(lat_prev) > y(k,j) )
                lat_prev = lat_prev - 1;
            end;
            lat_next = lat_prev + 1;
    
            dx1 = double(min(abs(x(k,j)-lon_base(lon_prev)),abs(x(k,j)-...
                lon_base(lon_prev)-360*sign(x(k,j)-lon_base(lon_prev)))));
            dx2 = double(dx_base - dx1);
            dy1 = double(y(k,j) - lat_base(lat_prev));
            dy2 = double(dy_base - dy1);
            
            % Four point interpolation
            
            a11 = double(depth_base(lat_prev,lon_prev));
            a12 = double(depth_base(lat_prev,lon_next));
            a21 = double(depth_base(lat_next,lon_prev));
            a22 = double(depth_base(lat_next,lon_next));
            depth_sub(k,j) = (a11*dy2*dx2 + a12*dy2*dx1 + a21*dy1*dx2 + ...
                a22*dx1*dy1)/den;
            
        else
            
            % Cell averaging
            % Determine the base bathymetry region that covers the cell
            
            lon_start = min(cell(k,j).px);
            lon_end = max(cell(k,j).px);
            lat_start = min(cell(k,j).py);
            lat_end = max(cell(k,j).py);
            
            overlap = 0; 
            if (lon_end > 360)
                overlap = 1;
                lon_end = lon_end - 360;
            end;
            if (lon_start < 0)
                overlap = 2;
                lon_start = lon_start + 360;
            end;
            
            clear depth_tmp lon_tmp lat_tmp lon1 lon2 depth_tmp1 depth_tmp2;
            
            [~,lat_start_pos] = min(abs(lat_base-lat_start));
            [~,lat_end_pos] = min(abs(lat_base-lat_end));
            lat_tmp = lat_base(lat_start_pos:lat_end_pos);
            [~,lon_start_pos] = min(abs(lon_base-lon_start));
            [~,lon_end_pos] = min(abs(lon_base-lon_end));
            
            switch overlap
                case 0                
                    depth_tmp = depth_base(lat_start_pos:lat_end_pos,...
                        lon_start_pos:lon_end_pos);
                    lon_tmp = lon_base(lon_start_pos:lon_end_pos);
                case 1
                    depth_tmp1 = depth_base(lat_start_pos:lat_end_pos,...
                        lon_start_pos:end);
                    depth_tmp2 = depth_base(lat_start_pos:lat_end_pos,...
                        2:lon_end_pos);
                    lon1 = lon_base(lon_start_pos:end);
                    lon2 = lon_base(2:lon_end_pos)+360.0;
                    lon_tmp = [lon1;lon2];
                    depth_tmp = [depth_tmp1 depth_tmp2];
                case 2
                    depth_tmp1 = depth_base(lat_start_pos:lat_end_pos,...
                       lon_start_pos:end);
                    depth_tmp2 = depth_base(lat_start_pos:lat_end_pos,...
                        2:lon_end_pos);
                    lon1 = lon_base(lon_start_pos:end) - 360;
                    lon2 = lon_base(2:lon_end_pos);
                    lon_tmp = [lon1;lon2];
                    depth_tmp = [depth_tmp1 depth_tmp2];                    
            end;
            
            % Compute the average depth from points that lie inside the
            % the cell and are below the cut off
            
            
            clear lon_tmp2d lat_tmp2d in_cell depth_tmp_incell;
            [lon_tmp2d,lat_tmp2d] = meshgrid(lon_tmp,lat_tmp);
            in_cell = inpolygon(lon_tmp2d,lat_tmp2d,cell(k,j).px,cell(k,j).py);
            depth_tmp_incell = depth_tmp(in_cell > 0);
            Nt = numel(depth_tmp_incell);
            clear loc;
            loc = find(depth_tmp_incell <= cut_off);
            if (~isempty(loc))
                Ntt = length(loc);
                if (Ntt/Nt > limit)
                    depth_sub(k,j) = mean(depth_tmp_incell(loc));
                else
                    depth_sub(k,j) = dry;
                end;
            else
                depth_sub(k,j) = dry;
            end;              
            
        end % End of check to see if it will interpolate or average
    
        % Counter to check proportion of cells completed

        Nl = (j-1)*Ny+k;
        itmp = floor(Nl/Nb*100);
        if (mod(itmp,5) == 0 && itmp_prev ~= itmp)
            fprintf(1,'Completed %d per cent of the cells \n',itmp);
        end;
        itmp_prev = itmp;
    end; % Loop through lattitudes
        
end; % Loop through longitudes

return;
            
    

    

