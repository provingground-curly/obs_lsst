#!/usr/bin/env python

import sys
import os.path
import re

import numpy
from astropy.io import fits
import collections

from lsst.obs.lsst.auxTel import AuxTelMapper

Defect = collections.namedtuple('Defect', ['x0', 'y0', 'width', 'height'])
mapperMap = {'auxTel': AuxTelMapper}


def genDefectFits(cameraName, source, targetDir):
    mapper = mapperMap[cameraName](root=".", calibRoot=".")
    camera = mapper.camera

    ccds = dict()
    for ccd in camera:
        ccdNum = ccd.getId()
        ccdName = ccd.getName()
        ccds[ccdNum] = ccdName

    defects = dict()

    with open(source, "r") as f:
        for line in f:
            line = re.sub(r"\#.*", "", line).strip()
            if len(line) == 0:
                continue
            ccd, x0, y0, width, height = re.split(r"\s+", line)
            ccd = int(ccd)
            if ccd not in ccds:
                raise RuntimeError("Unrecognised ccd: %d" % ccd)
            if ccd not in defects:
                defects[ccd] = list()
            defects[ccd].append(Defect(x0=int(x0), y0=int(y0), width=int(width), height=int(height)))

    for ccd in ccds:
        # Make empty defect FITS file for CCDs with no defects
        if ccd not in defects:
            defects[ccd] = list()

        columns = list()
        for colName in Defect._fields:
            colData = numpy.array([d._asdict()[colName] for d in defects[ccd]])
            col = fits.Column(name=colName, format="I", array=colData)
            columns.append(col)

        cols = fits.ColDefs(columns)
        table = fits.BinTableHDU.from_columns(cols)

        table.header['DETNUM'] = ccd
        table.header['NAME'] = ccdName

        name = os.path.join(targetDir, "defects_%d.fits" % ccd)
        print("Writing %d defects from CCD %d (%s) to %s" % (table.header['NAXIS2'], ccd, ccds[ccd], name))
        if os.path.exists(name):
            if args.force:
                os.unlink(name)
            else:
                print("File %s already exists; use --force to overwrite" % name, file=sys.stderr)
                continue

        table.writeto(name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("cameraName", type=str, choices=['auxTel'],
                        help="Camera name: auxTel only at present")
    parser.add_argument("defectsFile", type=str, help="Text file containing list of defects")
    parser.add_argument("targetDir", type=str, nargs="?", help="Directory for generated fits files")
    parser.add_argument("-f", "--force", action="store_true", help="Force operations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Be chattier")
    args = parser.parse_args()

    if not args.targetDir:
        args.targetDir = os.path.split(args.defectsFile)[0]

    genDefectFits(args.cameraName, args.defectsFile, args.targetDir)
