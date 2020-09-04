#!/bin/bash
Xvfb :1 -screen 0 1024x768x16 & source activate wassncplot && export DISPLAY=:1 && python wassncplot.py $@
