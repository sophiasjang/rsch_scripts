#!/bin/sh

# Based on a batch file by Maverick Woo
#
# Usage:
#       pdfrescale path-stem scale-factor
#
# Example:
#       pdfrescale sillyLNCSpaper 1.2
# produces
#       sillyLNCSpaper-1.2.pdf

current=`pwd`
working=${1%/*}

# echo $current
# echo $working

# change into directory of pdf file
cd "$working"

# extract filename
filename=${1##*/}
# echo $filename
# remove extension
jobname=${filename%.pdf}
# echo $jobname

if [ ! -f "$jobname.pdf" ]; then
  echo "Input file $jobname.pdf not found"
  exit 1
fi

scale=$2
if [ -z "$scale" ]; then
  echo "scale not specified, using default: 0.8"
  scale=0.8
fi
tmp=`tempfile|sed -e 's/\./_/g'`.pdf

cp "${jobname}.pdf" "$tmp"
pdflatex \
   -jobname="$jobname-$scale" \
   '\documentclass{article}\usepackage{pdfpages}\begin{document}\includepdf[pages=-,scale='"$scale"']{'"$tmp"'}\end{document}\batchmode' \
   > /dev/null
\rm "$tmp"
\rm "$jobname-$scale.aux" "$jobname-$scale.log"

cd "$current"