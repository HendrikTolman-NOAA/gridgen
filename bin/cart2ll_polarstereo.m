function [LAT,LON]=cart2ll_polarstereo(x,y,earth_radius,eccentricity,north)
%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file cart2ll_polarstereo.m
% @brief Transforms Cartesian map coordinates to latitude/longitude for a polar stereographic system.
% @details Computes geographic coordinates (latitude and longitude) given Cartesian (x,y) positions, Earth radius, eccentricity, and hemisphere indicator.
%
% @param[in] x Cartesian x-coordinate (m).
% @param[in] y Cartesian y-coordinate (m).
% @param[in] earth_radius Radius of ellipsoid (m).
% @param[in] eccentricity Eccentricity of ellipsoid.
% @param[in] north Hemisphere flag (1 for North, 0 for South).
% @return LAT 2D array of latitudes (degrees).
% @return LON 2D array of longitudes (degrees).
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
%This script transforms map coordinates to lat/lon data for a polar stereographic system
%Equations are taken form: Map Projections - A Working manual - by J.P. Snyder. 1987 

%earth_radius=6378137.0; %radius of ellipsoid, WGS84
%eccentricity=0.08181919; %eccentricity, WGS84
%north=1;%if south, north=0

if north==1
LAT_C=70; %latitude of true scale in the north hemisphere
else
LAT_C=-70; %latitude of true scale in the south hemisphere
end

LON_C=0; %meridian along positive Y axis

%convert to radians
LAT_C=deg2rad(LAT_C);
LON_C=deg2rad(LON_C);

%plus in the north or minus in the south

    pm=sign(LAT_C); 
    LAT_C=pm*LAT_C;
    LON_C=pm*LON_C;
    x=pm*x;
    y=pm*y;

THETA=(sqrt(x.^2+y.^2))*(tan(pi/4-LAT_C/2)/((1-eccentricity*sin(LAT_C))...
    /(1+eccentricity*sin(LAT_C)))^(eccentricity/2))/(earth_radius*...
    (cos(LAT_C)/sqrt(1-eccentricity^2*(sin(LAT_C))^2)));

% find LAT with a series intiated from, a first guess for phi =pi/2 - 2 * 
%atan(t) with a threshold of pi*1e-8

LAT=(pi/2 - 2 * atan(THETA))+(eccentricity^2/2 + 5*eccentricity^4/24 + ...
    eccentricity^6/12 + 13*eccentricity^8/360)*sin(2*(pi/2 - 2 * atan(THETA)))...
    + (7*eccentricity^4/48 + 29*eccentricity^6/240 + ...
    811*eccentricity^8/11520)*sin(4*(pi/2 - 2 * atan(THETA)))...
    + (7*eccentricity^6/120+81*eccentricity^8/1120)*sin(6*(pi/2 - 2 * atan(THETA)))...
    + (4279*eccentricity^8/161280)*sin(8*(pi/2 - 2 * atan(THETA)));

LON=LON_C + atan2(x,-y);
% correct the signs and phase
LAT=pm*LAT;
% LAT_alt=pm*LAT_alt;
LON=pm*LON;
LON=mod(LON+pi,2*pi)-pi; %want longitude in the range -pi to pi
%convert back to degrees
LAT=rad2deg(LAT);
LON=rad2deg(LON);

LON(LON<0)=LON(LON<0)+360; %make sure longitude is from 0-360 deg

