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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import unittest

from lsst.pipe.tasks.ingest import IngestConfig
import lsst.daf.base
import lsst.log

import lsst.obs.lsst.translators  # noqa: F401 -- register the translators
from lsst.obs.lsst.auxTel import AuxTelParseTask
from lsst.obs.lsst.ts8 import Ts8ParseTask
from lsst.obs.lsst.ts3 import Ts3ParseTask
from lsst.obs.lsst.phosim import PhosimParseTask
from lsst.obs.lsst.imsim import ImsimParseTask
from lsst.obs.lsst.ucd import UcdParseTask
from lsst.obs.lsst.ingest import LsstCamParseTask

TESTDIR = os.path.abspath(os.path.dirname(__file__))
ROOTDIR = os.path.normpath(os.path.join(TESTDIR, os.path.pardir))
DATADIR = os.path.join(ROOTDIR, "data", "input")
CONFIGDIR = os.path.join(ROOTDIR, "config")


class LsstCamParseTaskTestCase(unittest.TestCase):

    def _constructParseTask(self, configdir, name, parseTaskClass):
        """Construct a parser task suitable for testing translation methods.

        Parameters
        ----------
        configdir : `str`
            Root of the config directory. This directory must include a
            directory of name ``name``.
        name : `str`
            Name of instrument within data directory and config directory.
        parseTaskClass : `lsst.pipe.tasks.ParseTask`
            Class, not instance, to use to extract information from header.

        Returns
        -------
        parseTask : `lsst.pipe.tasks.ParseTask`
            Instance of a ``parseTaskClass`` class.
        """
        ingestConfig = IngestConfig()
        ingestConfig.load(os.path.join(configdir, "ingest.py"))
        specificPath = os.path.join(configdir, name, "ingest.py")
        if os.path.exists(specificPath):
            ingestConfig.load(specificPath)
        parser = parseTaskClass(ingestConfig.parse, name=name)
        return parser

    def assertParseCompare(self, datadir, configdir, name, parseTask, testData):
        """Compare parsed output from headers with expected output.

        Parameters
        ----------
        datadir : `str`
            Name of the data directory to use. This directory must include
            a directory of name ``name``.
        configdir : `str`
            Root of the config directory. This directory must include a
            directory of name ``name``.
        name : `str`
            Name of instrument within data directory and config directory.
        parseTask : `lsst.pipe.tasks.ParseTask`
            Class, not instance, to use to extract information from header.
        testData : `tuple` of `tuple` (`str`, `dict`) pairs.
            Each pair in the tuple defines the file name to read from the
            constructed data directory and a `dict` defining the expected
            results from metadata extraction.

        Raises
        ------
        AssertionError
            If the results differ from the expected values.

        """
        parser = self._constructParseTask(configdir, name, parseTask)
        for fileFragment, expected in testData:
            file = os.path.join(DATADIR, name, fileFragment)
            with self.subTest(f"Testing {file}"):
                phuInfo, infoList = parser.getInfo(file)
                print(f"Name: {file}")
                for k, v in phuInfo.items():
                    print(f"{k}: {v!r}")
                self.assertEqual(phuInfo, expected)

    def test_parsetask_auxtel_translator(self):
        """Run the gen 2 metadata extraction code for AuxTel"""
        test_data = (("raw/2018-09-20/2018092000065-det000.fits",
                      dict(
                          expTime=27.0,
                          object='UNKNOWN',
                          imageType='UNKNOWN',
                          detectorName='S00',
                          dateObs='2018-09-21T06:12:18.210',
                          date='2018-09-21T06:12:18.210',
                          dayObs='2018-09-20',
                          detector=0,
                          filter='NONE',
                          seqNum=65,
                          visit=2018092000065,
                          wavelength=-666,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "auxTel", AuxTelParseTask, test_data)

        # Need to test some code paths for translations where we don't have
        # example headers.
        parseTask = self._constructParseTask(CONFIGDIR, "auxTel", AuxTelParseTask)

        md = lsst.daf.base.PropertyList()
        md["IMGNAME"] = "AT-O-20180816-00008"
        seqNum = parseTask.translate_seqNum(md)
        self.assertEqual(seqNum, 8)

        del md["IMGNAME"]
        md["FILENAME"] = "ats_exp_27_AT_C_20180920_000065.fits"
        seqNum = parseTask.translate_seqNum(md)
        self.assertEqual(seqNum, 65)

        # This will issue a warning
        md["FILENAME"] = "ats_exp_27_AT_C.fits"
        with self.assertLogs(level="WARNING"):
            with lsst.log.UsePythonLogging():
                seqNum = parseTask.translate_seqNum(md)
        self.assertEqual(seqNum, 0)

        # Test the wavelength code path for non integer wavelength
        md["MONOWL"] = 600.4
        with self.assertLogs(level="WARNING"):
            with lsst.log.UsePythonLogging():
                wl = parseTask.translate_wavelength(md)
        self.assertEqual(wl, int(md.getScalar("MONOWL")))

    def test_parsetask_ts8_translator(self):
        """Run the gen 2 metadata extraction code for TS8"""
        test_data = (("raw/6006D/201807241028453-RTM-010-S11-det067.fits",
                      dict(
                          expTime=21.913,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='LAMBDA',
                          lsstSerial='E2V-CCD250-179',
                          date='2018-07-24T10:28:45.342',
                          dateObs='2018-07-24T10:28:45.342',
                          run='6006D',
                          wavelength=700,
                          detectorName='S11',
                          raftName="RTM-010",
                          detector=67,
                          dayObs='2018-07-24',
                          filter='z',
                          visit=201807241028453,
                          testSeqNum=17,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "ts8", Ts8ParseTask, test_data)

        # Need to test some code paths for translations where we don't have
        # example headers.
        parseTask = self._constructParseTask(CONFIGDIR, "ts8", Ts8ParseTask)

        md = lsst.daf.base.PropertyList()
        wl = parseTask.translate_testSeqNum(md)
        self.assertEqual(wl, 0)
        md["SEQNUM"] = 5
        wl = parseTask.translate_testSeqNum(md)
        self.assertEqual(wl, 5)

    def test_parsetask_ts3_translator(self):
        """Run the gen 2 metadata extraction code for TS3"""
        test_data = (("raw/2016-07-22/201607220607067-R071-S00-det071.fits",
                      dict(
                          expTime=30.611,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='LAMBDA',
                          lsstSerial='ITL-3800C-098',
                          date='2016-07-22T06:07:06.784',
                          dateObs='2016-07-22T06:07:06.784',
                          run='2016-07-22',
                          wavelength=1000,
                          detectorName='S00',
                          raftName="R071",
                          detector=71,
                          dayObs='2016-07-21',
                          filter='550CutOn',
                          visit=201607220607067,
                          testSeqNum=67,
                      )),
                     ("raw/2018-11-15/201811151255111-R433-S00-det433.fits",
                      dict(
                          expTime=44.631,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='LAMBDA',
                          lsstSerial='E2V-CCD250-411',
                          date='2018-11-15T12:55:11.149',
                          dateObs='2018-11-15T12:55:11.149',
                          run='2018-11-15',
                          wavelength=1000,
                          detectorName='S00',
                          raftName="R433",
                          detector=433,
                          dayObs='2018-11-15',
                          filter='550CutOn',
                          visit=201811151255111,
                          testSeqNum=25,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "ts3", Ts3ParseTask, test_data)

        # Need to test some code paths for translations where we don't have
        # example headers.
        parseTask = self._constructParseTask(CONFIGDIR, "ts3", Ts8ParseTask)

        md = lsst.daf.base.PropertyList()
        wl = parseTask.translate_testSeqNum(md)
        self.assertEqual(wl, 0)
        md["SEQNUM"] = 5
        wl = parseTask.translate_testSeqNum(md)
        self.assertEqual(wl, 5)

    def test_parsetask_imsim_translator(self):
        """Run the gen 2 metadata extraction code for Imsim"""
        test_data = (("raw/204595/R11/00204595-R11-S20-det042-000.fits",
                      dict(
                          expTime=30.0,
                          object='UNKNOWN',
                          imageType='SKYEXP',
                          testType='IMSIM',
                          filter='i',
                          lsstSerial='LCA-11021_RTM-000',
                          date='2022-10-05T06:53:26.357',
                          dateObs='2022-10-05T06:53:26.357',
                          run='204595',
                          visit=204595,
                          wavelength=-666,
                          raftName='R11',
                          detectorName='S20',
                          detector=42,
                          snap=0,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "imsim", ImsimParseTask, test_data)

    def test_parsetask_phosim_translator(self):
        """Run the gen 2 metadata extraction code for Phosim"""
        test_data = (("raw/204595/R11/00204595-R11-S20-det042-000.fits",
                      dict(
                          expTime=30.0,
                          object='UNKNOWN',
                          imageType='SKYEXP',
                          testType='PHOSIM',
                          lsstSerial='R11_S20',
                          date='2022-10-05T06:53:11.357',
                          dateObs='2022-10-05T06:53:11.357',
                          run='204595',
                          wavelength=-666,
                          raftName='R11',
                          detectorName='S20',
                          detector=42,
                          snap=0,
                          filter='i',
                          visit=204595,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "phosim", PhosimParseTask, test_data)

    def test_parsetask_ucd_translator(self):
        """Run the gen 2 metadata extraction code for UCDCam"""
        self.maxDiff = None
        test_data = (("raw/2018-12-05/20181205233148-S00-det000.fits",
                      dict(
                          expTime=0.5,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='flat',
                          lsstSerial='E2V-CCD250-112-04',
                          date='2018-12-05T23:31:48.288',
                          dateObs='2018-12-05T23:31:48.288',
                          run='2018-12-05',
                          wavelength=-666,
                          raftName='R00',
                          detectorName='S00',
                          detector=0,
                          dayObs='2018-12-05',
                          filter='r',
                          visit=20181205233148,
                          testSeqNum=100,
                      )),
                     ("raw/2018-05-30/20180530150355-S00-det002.fits",
                      dict(
                          expTime=0.5,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='flat',
                          lsstSerial='ITL-3800C-002',
                          date='2018-05-30T15:03:55.872',
                          dateObs='2018-05-30T15:03:55.872',
                          run='2018-05-30',
                          wavelength=-666,
                          raftName='R02',
                          detectorName='S00',
                          detector=2,
                          dayObs='2018-05-30',
                          filter='r',
                          visit=20180530150355,
                          testSeqNum=100,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "ucd", UcdParseTask, test_data)

        # Need to test some code paths for translations where we don't have
        # example headers.
        parseTask = self._constructParseTask(CONFIGDIR, "ucd", UcdParseTask)

        md = lsst.daf.base.PropertyList()
        wl = parseTask.translate_testSeqNum(md)
        self.assertEqual(wl, 0)
        md["SEQNUM"] = 5
        wl = parseTask.translate_testSeqNum(md)
        self.assertEqual(wl, 5)

    def test_parsetask_lsstCam_translator(self):
        """Run the gen 2 metadata extraction code for lsstCam"""
        test_data = (("raw/unknown/R10/2019031900001-R10-S02-det029-000.fits",
                      dict(
                          expTime=0.0,
                          object='UNKNOWN',
                          imageType='BIAS',
                          testType='BIAS',
                          seqNum=1,
                          dayObs="2019-03-19",
                          filter='NONE',
                          lsstSerial='ITL-3800C-041',
                          date='2019-03-19T15:50:28.145',
                          dateObs='2019-03-19T15:50:28.145',
                          run='unknown',
                          visit=2019031900001,
                          wavelength=-666,
                          raftName='R10',
                          detectorName='S02',
                          detector=29,
                          snap=0,
                      )),
                     ("raw/6489D/R10/2019032200002-R10-S22-det035-000.fits",
                      dict(
                          expTime=1.0,
                          object='UNKNOWN',
                          imageType='FLAT',
                          testType='FLAT',
                          seqNum=2,
                          dayObs="2019-03-22",
                          filter='SDSSi+ND_OD0.5',
                          lsstSerial='ITL-3800C-103',
                          date='2019-03-22T15:31:01.904',
                          dateObs='2019-03-22T15:31:01.904',
                          run='6489D',
                          visit=2019032200002,
                          wavelength=-666,
                          raftName='R10',
                          detectorName='S22',
                          detector=35,
                          snap=0,
                      )),
                     )
        self.assertParseCompare(DATADIR, CONFIGDIR, "lsstCam", LsstCamParseTask, test_data)


if __name__ == "__main__":
    unittest.main()
