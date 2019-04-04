# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.

import os.path
from lsst.utils import getPackageDir

if hasattr(config.astrometryRefObjLoader, "ref_dataset_name"):
    config.astrometryRefObjLoader.ref_dataset_name = 'cal_ref_cat'
if hasattr(config.photometryRefObjLoader, "ref_dataset_name"):
    config.photometryRefObjLoader.ref_dataset_name = 'cal_ref_cat'

filterMapFile = os.path.join(getPackageDir('obs_lsst'), 'config', 'filterMap.py')
config.astrometryRefObjLoader.load(filterMapFile)
config.photometryRefObjLoader.load(filterMapFile)

config.sourceSelector.name = 'science'
# Use only stars because aperture fluxes of galaxies are biased and depend on seeing
config.sourceSelector['science'].doUnresolved = True
# with dependable signal to noise ratio.
config.sourceSelector['science'].doSignalToNoise = True
# Min SNR must be > 0 because jointcal cannot handle negative fluxes,
# otherwise selection of 10 is arbitrary
config.sourceSelector['science'].signalToNoise.minimum = 10.
# Base SNR on CalibFlux because that is the flux jointcal that fits and must be positive
config.sourceSelector['science'].signalToNoise.fluxField = 'slot_CalibFlux_instFlux'
config.sourceSelector['science'].signalToNoise.errField = 'slot_CalibFlux_instFluxErr'
# Do not trust blended sources' aperture fluxes which also depend on seeing
config.sourceSelector['science'].doIsolated = True
# Do not trust either flux or centroid measurements with flags (chosen from the usual QA flags for stars)
config.sourceSelector['science'].doFlags = True
badFlags = ['base_PixelFlags_flag_edge', 'base_PixelFlags_flag_saturated',
            'base_PixelFlags_flag_interpolatedCenter', 'base_SdssCentroid_flag',
            'base_PsfFlux_flag', 'base_PixelFlags_flag_suspectCenter']
config.sourceSelector['science'].flags.bad = badFlags
