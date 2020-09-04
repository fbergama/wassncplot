%%
clc;clear;close all;

PIXEL_SCALE = '1.0';  

plane = [ -0.002495052745, 0.7628649396, 0.6465524468, -4.76079452];

K = [1.457e+03  0.0        1.212e+03 ;...
     0.         1.457e+03  1.007e+03  ;...
     0.0        0.0        1.0];

 
W = 2456;
H = 2058;
xmin = -10;
xmax =  10;
ymin = -30;
ymax = -5;


%%

[XX,YY] = meshgrid( linspace(xmin,xmax,256), linspace(ymin,ymax,256) );
ZZ = 0.05*( sin(XX*0.5)+2*sin(YY) )-3;
%ZZ = ZZ*0;


%%

[R,T] = plane_2_RT( plane );
Ri = R';
Ti = -Ri*T;

P0cam = [K,zeros(3,1)];
pts3d = [XX(:) , YY(:) , -ZZ(:)]';

pts2d = K  * (Ri*pts3d + Ti); 
pts2d = pts2d(1:2,:) ./ pts2d(3,:);

figure;
scatter( pts2d(1,:), pts2d(2,:), 1, ZZ(:) );
axis ij;
xlim([0,W]);ylim([0,H]);

%%
% Prepare wassncplot input data

delete('test.nc');
nccreate('test.nc', 'scale' );
ncwrite('test.nc', 'scale', 1.0 );

nccreate('test.nc', 'X_grid', 'Dimensions',{'r',256,'c',256} );
ncwrite('test.nc', 'X_grid', XX*1000 );

nccreate('test.nc', 'Y_grid', 'Dimensions',{'r',256,'c',256} );
ncwrite('test.nc', 'Y_grid', YY*1000 );

ZZ3(:,:,1)=ZZ;
nccreate('test.nc', 'Z', 'Dimensions',{'r',256,'c',256,'t',1} );
ncwrite('test.nc', 'Z', ZZ3*1000 );
ncdisp('test.nc')


mkdir('config_test');
writematrix(P0cam, 'config_test/P0cam.txt','Delimiter',' ');
writematrix(plane', 'config_test/plane.txt','Delimiter',' ');
save_ocv_matrix(K,'config_test/intrinsics_00.xml');
save_ocv_matrix(zeros(5,1),'config_test/distortion_00.xml');

mkdir('cam_test');
I = uint8( zeros(H,W) );
imwrite(I,'cam_test/000000_000.png');

mkdir('wassncplot_out');

%%
% Call wassncplot

% cmdstring = [CONDA_BIN_DIR, 'conda run -n wassncplot ',...
%              'python3 ',...
%              '../wassncplot.py ',...
%              '-f 0 -l 1 -s 2 -b 1.0 --scale 1 --savexyz --saveimg --pxscale ', PIXEL_SCALE, ' ',...
%              pwd(),'/test.nc '...
%              pwd(),'/cam_test/ ', ...
%              pwd(),'/config_test/ ', ...
%              pwd(),'/config_test/plane.txt ', ...
%              pwd(),'/config_test/P0cam.txt ', ...
%              pwd(),'/wassncplot_out'];
         
cmdstring = ['docker run -it --rm -v "',pwd(),'":/DATA fbergama/wassncplot ',...
             '-f 0 -l 1 -s 2 -b 1.0 --scale 1 --savexyz --saveimg --pxscale ', PIXEL_SCALE, ' ',...
             '/DATA/test.nc '...
             '/DATA/cam_test/ ', ...
             '/DATA/config_test/ ', ...
             '/DATA/config_test/plane.txt ', ...
             '/DATA/config_test/P0cam.txt ', ...
             '/DATA/wassncplot_out'];
 
fprintf(cmdstring);
fprintf('\n');
%%
[status,cmdout]=system(cmdstring);
fprintf(cmdout);
fprintf('\n');

%%
% Load wassncplot output

load('wassncplot_out/00000000.mat');

X_ncpl = squeeze(px_2_3D(:,:,1));
Y_ncpl = squeeze(px_2_3D(:,:,2));
Z_ncpl = squeeze(px_2_3D(:,:,3));

xgt = XX(:);
ygt = YY(:);
zgt = ZZ(:);

%%
% compare

figure;
imagesc(Z_ncpl);

figure;
imagesc( Z_ncpl ); hold on;
scatter( pts2d(1,:), pts2d(2,:), 1,'k');
colorbar;
title('wassncplot output vs. projected points');

%%

xvals = interp2(X_ncpl, pts2d(1,:), pts2d(2,:) )';
xerror = abs( xvals - xgt );

yvals = interp2(Y_ncpl, pts2d(1,:), pts2d(2,:) )';
yerror = abs( yvals - ygt );

zvals = interp2(Z_ncpl, pts2d(1,:), pts2d(2,:) )';
zerror = abs( zvals - zgt );

figure;
scatter( pts2d(1,:), pts2d(2,:), 1, xerror);
title('X error');
axis ij;
xlim([0,W]);ylim([0,H]);
caxis([0,0.1]);
colorbar;

figure;
scatter( pts2d(1,:), pts2d(2,:), 1, yerror);
title('Y error');
axis ij;
xlim([0,W]);ylim([0,H]);
caxis([0,0.1]);
colorbar;

figure;
scatter( pts2d(1,:), pts2d(2,:), 1, zerror);
title('Z error');
axis ij;
xlim([0,W]);ylim([0,H]);
caxis([0,0.1]);
colorbar;

%% 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


function [R,T] = plane_2_RT( plane )
    a=plane(1);b=plane(2);c=plane(3);d=plane(4);
    q = (1-c)/(a*a + b*b);
    R=eye(3);T=zeros(3,1);
    R(1,1) = 1-a*a*q;
    R(1,2) = -a*b*q;
    R(1,3) = -a;
    R(2,1) = -a*b*q;
    R(2,2) = 1-b*b*q;
    R(2,3) = -b;
    R(3,1) = a;
    R(3,2) = b;
    R(3,3) = c;
    T(1)=0;
    T(2)=0;
    T(3)=d;
end

function save_ocv_matrix( M, filename )
    fid = fopen(filename,'w');
    fprintf(fid,'<?xml version="1.0"?>\n<opencv_storage>\n<intr type_id="opencv-matrix">\n<rows>%d</rows>\n<cols>%d</cols>\n<dt>d</dt>\n<data>\n',size(M,1),size(M,2));
    for ii=1:size(M,1)
        for jj=1:size(M,2)
            fprintf(fid,'%f ',M(ii,jj));
        end
        fprintf(fid,'\n');
    end
    fprintf(fid,'</data>\n</intr>\n</opencv_storage>');
    fclose(fid);
end

