# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST simulations"""

__all__ = ("LsstSimTranslator", )

import warnings
import logging

import astropy.utils.exceptions
from astropy.coordinates import AltAz
from astro_metadata_translator import cache_translation

from .lsst import LsstBaseTranslator, LSST_LOCATION

log = logging.getLogger(__name__)


class LsstSimTranslator(LsstBaseTranslator):
    """Shared routines for LSST Simulated Data.
    """

    # No constant or trivial mappings defined
    _const_map = {}
    _trivial_map = {}

    @cache_translation
    def to_telescope(self):
        # Docstring will be inherited. Property defined in properties.py
        telescope = None
        if self.is_key_ok("OUTFILE") and self._header["OUTFILE"].startswith("lsst"):
            telescope = "LSST"
            self._used_these_cards("OUTFILE")
        elif "LSST_NUM" in self._header:
            telescope = "LSST"
            self._used_these_cards("LSST_NUM")
        return telescope

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        location = None
        # In theory simulated files might not be for LSST
        tel = self.to_telescope()
        if tel == "LSST":
            location = LSST_LOCATION
        else:
            # Try standard FITS headers
            try:
                location = super().to_location()
            except Exception:
                pass
        return location

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.to_observation_type() == "science":
            # Derive from RADec in absence of any other information
            radec = self.to_tracking_radec()
            if radec is not None:
                # This triggers warnings because of the future dates
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=astropy.utils.exceptions.AstropyWarning)
                    altaz = radec.transform_to(AltAz)
                return altaz
        return None
