#!/usr/bin/python

# increasing margins does not always work

import sys
from pyPdf import PdfFileWriter, PdfFileReader

infile = PdfFileReader(file(sys.argv[1], "rb"))
outfile = PdfFileWriter()

for i in range(infile.getNumPages()):
  if i == 2:
    page = infile.getPage(i)
    print page.mediaBox
    xy = page.mediaBox.getUpperRight()
    (x, y) = map(int, xy)
    page.mediaBox.upperRight = (
                page.mediaBox.getUpperRight_x() * int(0.2*x),
                page.mediaBox.getUpperRight_y() * int(0.2*y),
                )
    #page.mediaBox.lowerLeft = (
    #            page.mediaBox.getLowerLeft_x() - int(0.2*x),
    #            page.mediaBox.getLowerLeft_y() - int(0.2*y),
    #            )
    outfile.addPage(page)
    print page.mediaBox

outputStream = file(sys.argv[2], "wb")
outfile.write(outputStream)
outputStream.close()
