# **************************************************************************
# *
# * Authors: Martín Salinas Antón (ssalinasmartin@gmail.com)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import shutil, os
from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportVolumes
from ..protocols import ProtEmap2sec
from kiharalab.constants import *

class TestEmap2sec(BaseTest):
    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.tmpFiles = []
        cls.ds = DataSet.getDataSet('model_building_tutorial')

        # Running test
        cls._runImportVolumes()

    @classmethod
    def _runImportVolumes(cls):
        # Creating arguments for import volumes protocol
        args = {
            'filesPath': cls.ds.getFile('volumes/emd_6838.mrc'),
            'samplingRate': 1.4,
            'setOrigCoord': False
        }

        # Creating and launching import volumes protocol
        protImportVolumes = cls.newProtocol(ProtImportVolumes, **args)
        cls.launchProtocol(protImportVolumes)

        # Storing results
        cls.protImportVolume = protImportVolumes
    
    def _runEmap2sec(self):
        # Running protocol
        protEmap2sec = self.newProtocol(
            ProtEmap2sec,
            executionType=EMAP2SEC_TYPE_EMAP2SEC,
            inputVolume=self.protImportVolume.outputVolume,
            emap2secContour=5.4)
        self.launchProtocol(protEmap2sec)

        # Checking function output
        pdbOut = getattr(protEmap2sec, 'outputAtomStruct', None)
        self.assertIsNotNone(pdbOut)
        self.assertIsNotNone(pdbOut.getVolume())
    
    def _runEmap2secPlus(self):
        # Running protocol
        protEmap2sec = self.newProtocol(
            ProtEmap2sec,
            executionType=EMAP2SEC_TYPE_EMAP2SECPLUS,
            inputVolume=self.protImportVolume.outputVolume,
            emap2secplusContour=5.4)
        self.launchProtocol(protEmap2sec)

        # Checking function output
        pdbOut = getattr(protEmap2sec, 'outputAtomStruct', None)
        self.assertIsNotNone(pdbOut)
        self.assertIsNotNone(pdbOut.getVolume())

    def test1Emap2sec(self):
        """First test. Runs Emap2sec."""
        print("Running Emap2sec")
        # Running Emap2sec
        self._runEmap2sec()
    
    def test2Emap2secPlus(self):
        """Third test. Runs Emap2sec+ with an experimental volume type."""
        print("Running Emap2sec+ with an experimental volume type")
        # Running Emap2sec+ with with an experimental volume type
        self._runEmap2secPlus()
        # Last test calls cleaning function so it does not count as a separate test
        self.cleanTest()
    
    def cleanTest(self):
        """This function removes all temporary files produced during the execution."""
        # Cleaning up duplicated files
        for tmpFile in self.tmpFiles:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)