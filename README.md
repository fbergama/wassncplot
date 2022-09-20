# WASSncplot

WASSncplot is a small tool to plot NetCDF 3D data generated with
[WASS](http://www.dais.unive.it/wass) and [wassgridsurface](https://pypi.org/project/wassgridsurface/) on top of the original image files.

<img src="https://www.dais.unive.it/wass/files/00000249.jpg" width="100%" />

## Install

WASSncplot requires a Python 3.9 and can simply be installed via pip:

```
$ python -m pip install wassncplot
```


## Run wassncplot on a headless system

To use wassncplot while connected remotely via ssh, launch Xvfb first:

```
sudo Xvfb :1 -ac -screen 0 1280x720x24 
```

and then set export the DISPLAY environment variable `export DISPLAY=:1` before running wassncplot.



## Usage

WASSncplot is a command-line tool. You can get a description of the available program
arguments with the following command: 

```
 wassncplot v. 2.0.4
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
Copyright (C) Filippo Bergamasco 2022

usage: __main__.py [-h] [-f FIRST_INDEX] [-l LAST_INDEX] [-s STEP_INDEX] [-sd STEP_DATA_INDEX] [-b BASELINE] [--zmin ZMIN] [--zmax ZMAX] [--alpha ALPHA] [--pxscale PXSCALE] [--wireframe] [--no-wireframe] [--savexyz] [--saveimg] [--ffmpeg] [--ffmpeg-delete-frames] [--ffmpeg-fps FFMPEG_FPS] ncfile out

positional arguments:
  ncfile                Input NetCDF4 file
  out                   Where to store the produced images

optional arguments:
  -h, --help            show this help message and exit
  -f FIRST_INDEX, --first_index FIRST_INDEX
                        First data index to process
  -l LAST_INDEX, --last_index LAST_INDEX
                        Last data index to process (-1 to process all the frames)
  -s STEP_INDEX, --step_index STEP_INDEX
                        Sequence step
  -sd STEP_DATA_INDEX, --step_data_index STEP_DATA_INDEX
                        Sequence data step
  -b BASELINE, --baseline BASELINE
                        Baseline of the stereo system (use this option to override the baseline value stored in the netcdf file)
  --zmin ZMIN           Minimum 3D point elevation (used for colorbar limits)
  --zmax ZMAX           Maximum 3D point elevation (used for colorbar limits)
  --alpha ALPHA         Surface transparency [0..1]
  --pxscale PXSCALE     A scale factor to apply between logical and physical pixels in addition to the actual scale factor determined by the backend.
  --wireframe           Render surface in wireframe
  --no-wireframe        Render shaded surface
  --savexyz             Save mapping between image pixels and 3D coordinates as numpy data file
  --saveimg             Save the undistorted image (without the superimposed grid)
  --ffmpeg              Call ffmpeg to create a sequence video file
  --ffmpeg-delete-frames
                        Delete the produced frames after running ffmpeg
  --ffmpeg-fps FFMPEG_FPS
                        Sequence framerate
```


For example, the command:

```
$ python wassncplot.py ./wass_20140327_0910/3D/wass__20140327_091000.nc ./out 
```

Will render the sequence stored in  ```./wass_20140327_0910/3D/wass__20140327_091000.nc``` to the directory ```./out```.


## License

```
Copyright (C) 2019-2022 Filippo Bergamasco 

wassncplot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

WASS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
