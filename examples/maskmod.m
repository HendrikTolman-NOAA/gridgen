%       +--------------------------------------------------------+
%       | WAVEWATCH IV, open source, code management by NOAA/NWS |
%       +--------------------------------------------------------+
%
% @file maskmod.m
% @brief Example script for modifying a grid mask for multi-grid WAVEWATCH setups.
% @details Reads existing grid meta and mask files, parses computational area polygon,
% and modifies mask boundary values using modify_mask.
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
% 0. Define paths

  bin_dir = '/$HOME/gridgen/bin';       % matlab scripts location
  in_dir  = '/OUTPUT-PATH/data';        % input directory (for grid files)
  out_dir = '/OUTPUT-PATH/data';        % output directory (for grid files)

  addpath(bin_dir,'-END');

% 1. Read particulars from grid to be modified
 
  fname = 'Alaska_reg';                                  % file name prefix
  [lon,lat] = read_ww3meta([in_dir,'/',fname,'.meta']);  % read meta file
  [Ny,Nx] = size(lon);
  m = read_mask([in_dir,'/',fname,'.maskorig_ascii'],Nx,Ny); % read mask file

% 2. Read particulars from base grid (grid with which data has to be exchanged) 

  fnameb = 'Global';
  [lonb,latb] = read_ww3meta([in_dir,'/',fnameb,'.meta']);
  [Nyb,Nxb] = size(lonb);
  mb = read_mask([in_dir,'/',fnameb,'.maskorig_ascii'],Nxb,Nyb);


% 3. Define the polygon that describes the computational area 

  fid = fopen('alaska_10minzone.ascii','r');
  [a1,count] = fscanf(fid,'%f');
  px = a1(1:2:count);
  py = a1(2:2:count);

% 4. Compute the new mask

  m_new = modify_mask(m,lon,lat,mb,lonb,latb,1,px,py);   

% 5. You can have multiple polygons if needed

  px1 = [178 184 184 178 178];
  py1 = [70.5 70.5 72 72 70.5];

  m_tmp = modify_mask(m,lon,lat,mb,lonb,latb,1,px1,py1); % save the mask info 
                                                         % for every polygon in 
                                                         % a different variable

  loc = find(m_tmp~=3);                                  % determine the active 
                                                         % cells

  m_new(loc) = m_tmp(loc);                               % update the final mask 
                                                         % for only those active
  clear loc;                                             % cells

% 6. Write out new mask file

  write_ww3file([out_dir,'/',fname,'.mask'],m_new);

% 7. Vizualization (this step can be commented out if resources are limited)

figure(1);
clf;
pcolor(lon,lat,m);
shading flat;
colorbar;
title('Original Mask for grid','fontsize',14);
set(gca,'fontsize',14);

figure(2);
clf;
pcolor(lonb,latb,mb);
shading flat;
colorbar;
title('Mask for base grid','fontsize',14);
set(gca,'fontsize',14);

figure(3);
clf;
pcolor(lon,lat,m_new);
shading flat;
colorbar;
title('Final Mask for grid','fontsize',14);
set(gca,'fontsize',14);

% END OF SCRIPT 
