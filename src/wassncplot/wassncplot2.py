
from netCDF4 import Dataset
import numpy as np
import scipy.io as sio
import cv2 as cv
from .WaveFieldVisualize.waveview2 import WaveView
from tqdm import tqdm
import sys
import os
import argparse
import glob
import scipy.io


VERSION="2.0.8"



def wassncplot_main():

    print(" wassncplot v.", VERSION )
    print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\nCopyright (C) Filippo Bergamasco 2022 \n")


    parser = argparse.ArgumentParser()
    parser.add_argument("ncfile", help="Input NetCDF4 file")
    parser.add_argument("out", help="Where to store the produced images")
    parser.add_argument("-f", "--first_index", default=0, type=int, help="First data index to process")
    parser.add_argument("-l", "--last_index", default=-1, type=int, help="Last data index to process (-1 to process all the frames)")
    parser.add_argument("-s", "--step_index", default=1, type=int, help="Sequence step")
    parser.add_argument("-sd", "--step_data_index", default=1, type=int, help="Sequence data step")
    parser.add_argument("-b", "--baseline", type=float, help="Baseline of the stereo system (use this option to override the baseline value stored in the netcdf file)")
    parser.add_argument("--zmin", type=float, help="Minimum 3D point elevation (used for colorbar limits)")
    parser.add_argument("--zmax", type=float, help="Maximum 3D point elevation (used for colorbar limits)")
    parser.add_argument("--alpha", default=0.5, type=float, help="Surface transparency [0..1]")
    parser.add_argument("--pxscale", default=1, type=int, help="A scale factor to apply between logical and physical pixels in addition to the actual scale factor determined by the backend.")
    parser.add_argument("--text_prefix", default="", help="Bottom overlay text prefix")
    parser.add_argument("--wireframe", dest="wireframe", action="store_true", help="Render surface in wireframe")
    parser.add_argument("--upscale2x", dest="upscale2x", action="store_true", help="Upscale the input image before rendering")
    parser.add_argument("--no-wireframe", dest="wireframe", action="store_false", help="Render shaded surface")
    parser.add_argument("--no-textoverlay", dest="textoverlay", action="store_false", help="Add text overlay at the bottom of the frame")
    parser.add_argument("--savexyz", dest="savexyz", action="store_true", help="Save mapping between image pixels and 3D coordinates as numpy data file")
    parser.add_argument("--saveimg", dest="saveimg", action="store_true", help="Save the undistorted image (without the superimposed grid)")
    parser.add_argument("--ffmpeg", dest="ffmpeg", action="store_true", help="Call ffmpeg to create a sequence video file")
    parser.add_argument("--ffmpeg-delete-frames", dest="ffmpegdelete", action="store_true", help="Delete the produced frames after running ffmpeg")
    parser.add_argument("--ffmpeg-fps", dest="ffmpeg_fps", default=10.0, type=float, help="Sequence framerate")
    parser.set_defaults(wireframe=True)
    args = parser.parse_args()

    outdir = args.out

    if not os.path.isdir( outdir ):
        print("Output dir does not exist")
        sys.exit( -1 )
    else:
        print("Output renderings and data will be saved in: ", outdir)


    print("Opening netcdf file ", args.ncfile)
    rootgrp = Dataset( args.ncfile, mode="r")

    if args.baseline != None:
        stereo_baseline = args.baseline
    else:
        print("Loading baseline from netcdf")
        stereo_baseline = rootgrp["scale"][0]

    print("Stereo baseline: ",stereo_baseline, " (use -b option to change)")
    XX = np.array( rootgrp["X_grid"] )/1000.0
    YY = np.array( rootgrp["Y_grid"] )/1000.0
    ZZ = rootgrp["Z"]
    P0plane = np.array( rootgrp["meta"]["P0plane"] )
    nframes = ZZ.shape[0]

    Iw, Ih = rootgrp["meta"].image_width, rootgrp["meta"].image_height

    if args.zmin is None:
        try:
            args.zmin = rootgrp["meta"].zmin
        except:
            print("zmin not specified from command line and not found in NC file, aborting.")
            sys.exit(-1)

    if args.zmax is None:
        try:
            args.zmax = rootgrp["meta"].zmax
        except:
            print("zmax not specified from command line and not found in NC file, aborting.")
            sys.exit(-1)

    if np.abs(args.zmin)>np.abs(args.zmax):
        args.zmax = -args.zmin
    else:
        args.zmin = -args.zmax

    zmean = 0
    try:
        zmean = rootgrp["meta"].zmean
    except:
        print("Zmean not found in NC file, assuming 0.0")

    zrange = args.zmax - args.zmin

    print("Zmin/Zmax/Zmean: %3.3f / %3.3f / %3.3f"%(args.zmin,args.zmax,zmean) )
    print("Range: %f"%zrange)

    if args.last_index > 0:
        nframes = args.last_index

    waveview = None

    print("Rendering grid data...")
    pbar = tqdm( range(args.first_index, nframes, args.step_index), file=sys.stdout, unit="frames" )

    data_idx = args.first_index

    for image_idx in pbar:

        I0 = cv.imdecode( rootgrp["cam0images"][image_idx], cv.IMREAD_GRAYSCALE )
        if args.upscale2x:
            I0 = cv.pyrUp(I0)

        if waveview is None:
            waveview = WaveView( title="Wave field", width=I0.shape[1], height=I0.shape[0], wireframe=args.wireframe, pixel_scale=args.pxscale )
            waveview.setup_field( XX, YY, P0plane.T )
            waveview.set_zrange( -zrange/2.0, zrange/2, args.alpha )

        ZZ_data = np.squeeze( np.array( ZZ[data_idx,:,:] ) )/1000.0 - zmean
        #mask = (ZZ_data == 0.0)
        #ZZ_dil = cv.dilate( ZZ_data, np.ones((3,3)))
        #ZZ_data[mask]=ZZ_dil

        img, img_xyz = waveview.render( I0, ZZ_data )

        if args.savexyz:
            scipy.io.savemat( '%s/%08d'%(outdir,image_idx), {"px_2_3D": img_xyz} )

        img = (img*255).astype( np.uint8 )
        img = cv.cvtColor( img, cv.COLOR_RGB2BGR )

        if args.textoverlay:
            img[(img.shape[0]-20):,:,:] //= 3
            img[(img.shape[0]-20):,:,:] *= 2
            cv.putText( img, "%s frame %d"%(args.text_prefix,image_idx), (5,img.shape[0]-5), cv.FONT_HERSHEY_DUPLEX, 0.5, color=(255,255,255))

        cv.imwrite('%s/%08d_grid.png'%(outdir,image_idx), img )

        if args.saveimg:
            cv.imwrite('%s/%08d.png'%(outdir,image_idx), I0 )

        data_idx += args.step_data_index

    if args.ffmpeg:
        import subprocess
        _, outname = os.path.split(args.ncfile)

        ffmpeg_exe = "ffmpeg"
        if os.name == "nt":
            ffmpeg_exe += ".exe"

        callarr = [ffmpeg_exe, "-y", "-r","%d"%args.ffmpeg_fps, "-i" ,"%s/%%08d_grid.png"%(outdir), "-c:v", "libx264", "-vf", 'fps=25,format=yuv420p,scale=614x514', "-preset", "slow", "-crf", "22", "%s/%s.mp4"%(outdir,outname) ]

        print("Calling ", callarr)
        subprocess.run(callarr)

        if args.ffmpegdelete:
            img_files = glob.glob( "%s/*.png"%outdir )
            for imgfile in img_files:
                os.remove( imgfile )

