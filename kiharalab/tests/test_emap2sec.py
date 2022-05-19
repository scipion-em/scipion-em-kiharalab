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

from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportVolumes
from ..protocols import ProtEmap2sec

class TestEmap2sec(BaseTest):
    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.ds = DataSet.getDataSet('model_building_tutorial')

        # Running test with volume as input
        cls._runImportVolumes(False)

        # Running test with set of volumes as input
        cls._runImportVolumes()

    @classmethod
    def _runImportVolumes(cls, isSet=True):
        # Creating arguments for import volumes protocol
        inputPath = 'volumes/1733' + ('*' if isSet else '') + '.mrc'
        args = {
            'filesPath': cls.ds.getFile(inputPath),
            'samplingRate': 1.0,
            'setOrigCoord': False
        }

        # Creating and launching import volumes protocol
        protImportVolumes = cls.newProtocol(ProtImportVolumes, **args)
        cls.launchProtocol(protImportVolumes)

        # Storing results in different variable if input is Volume or SetOfVolumes
        if isSet:
            cls.protImportVolumes = protImportVolumes
        else:
            cls.protImportVolume = protImportVolumes
    
    def _runEmap2sec(self, isSet=True):
        # Getting input volumes and defining output variable string
        inputData = self.protImportVolumes.outputVolumes if isSet else self.protImportVolume.outputVolume
        outputVariable = 'outputAtomStruct' + ('s' if isSet else '')

        # Running protocol
        protEmap2sec = self.newProtocol(
            ProtEmap2sec,
            inputVolume=inputData,
            emap2secContour=2.75)
        self.launchProtocol(protEmap2sec)

        # Checking function output
        pdbOut = getattr(protEmap2sec, outputVariable, None)
        self.assertIsNotNone(pdbOut)
        if isSet:
            for atomStruct in pdbOut:
                self.assertIsNotNone(atomStruct.getVolume())
        else:        
            self.assertIsNotNone(pdbOut.getVolume())

    def testEmap2sec1(self):
        """First test. Runs Emap2sec with Volume as input"""
        print("Running Emap2sec with Volume as input")
        # Running Emap2se with Volume as input
        self._runEmap2sec(False)
    
    def testEmap2sec2(self):
        """Second test. Runs Emap2sec with SetOfVolumes as input"""
        print("Running Emap2sec with SetOfVolumes as input")
        # Running Emap2se with SetOfVolumes as input
        self._runEmap2sec()