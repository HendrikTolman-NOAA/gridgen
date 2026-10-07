function [lat,lon]=stereographic_lon_lat(lat_min,resolution,earth_radius,eccentricity,north)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file stereographic_lon_lat.m
% @brief Generates polar stereographic grid coordinates (lat, lon).
% @details Calculates latitude and longitude matrices for a polar stereographic grid defined by resolution and minimum latitude.
%
% @param[in] lat_min Minimum latitude bound (degrees).
% @param[in] resolution Grid resolution (m).
% @param[in] earth_radius Radius of Earth (m).
% @param[in] eccentricity Ellipsoid eccentricity.
% @param[in] north Hemisphere flag (1 for North, 0 for South).
% @return lat 2D matrix of latitude coordinates.
% @return lon 2D matrix of longitude coordinates.
%
% @copyright © 2021-2026 National Weather Service, National Oceanic and Atmospheric
% Administration. WAVEWATCH IV (TM) and WW4 (TM) are trademarks of the National
% Weather Service.
% NWS often uses Generative AI (GenAI) for code development and refactoring.
% Whenever GenAI is used, NWS requires a full human review of code before it is
% added to its repositories.
%
% @author Main Author(s): Aldgisl (AI Persona), Hendrik L. Tolman
% @author Contributors: Jules (Agentic AI), Ali Abdolali
% @date Initial, 2021-03-26
% @date Last update : 2026-10-07
%
% @note Originally written by Ali Abdolali (EMC/NCEP/NOAA) for WAVEWATCH grid generation.
%

%WGS84 - radius: 6378137.0 eccentricity: 0.08181919
%  command in Matlab: axes2ecc(6378137.0, 6356752.3142)
%Hughes ellipsoid - radius: 6378.273 km eccentricity: 0.081816153
%earth_radius=6378137.0; %radius of ellipsoid, WGS84
%eccentricity=0.08181919; %eccentricity, WGS84
%north=1;%if south, north=0
%resolution=9000; %km
%lat_min=49.9058; %the min abs(latitude) in the north/south hemisphere 

%determine the size of cartesian grid
lat1=lat_min*pi/180;
lat2=90*pi/180;
lon1=90*pi/180;
lon2=90*pi/180;
deltaLat=lat2-lat1;
deltaLon=lon2-lon1;
a=sin((deltaLat)/2).^2 + cos(lat1).*cos(lat2).*sin(deltaLon/2).^2;
c=2*atan2(sqrt(a),sqrt(1-a));
dist(:,1)=earth_radius*c;    %Haversine distance
   
   
%create the mesh in cartesian (m)   
xx=-(floor(dist/resolution)+0.5)*resolution:resolution:(floor(dist/resolution)+0.5)*resolution;
yy=-(floor(dist/resolution)+0.5)*resolution:resolution:(floor(dist/resolution)+0.5)*resolution;
[XX,YY]=meshgrid(xx,yy);
xxx=XX(:);
yyy=YY(:);

[LAT,LON]=cart2ll_polarstereo(xxx,yyy,earth_radius,eccentricity,north);

lat=reshape(LAT,size(XX));
lon=reshape(LON,size(XX));

dx=min(max(abs(diff(lon))));
dy=min(max(abs(diff(lat))));




