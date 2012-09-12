#!/bin/sh
project="qtbigtext"
dir="$HOME/$project/build"
/scratchbox/login mkdir -p $dir
/scratchbox/login -d $dir cmake ..
