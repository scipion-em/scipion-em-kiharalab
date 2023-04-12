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
from ..protocols import ProtMainMastSegmentMap

class TestMainMast(BaseTest):
    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.ds = DataSet.getDataSet('model_building_tutorial')

        # Running test with volume as input
        cls._runImportVolumes()

    @classmethod
    def _runImportVolumes(cls):
        # Creating arguments for import volumes protocol
        args = {
            'filesPath': cls.ds.getFile('volumes/emd_6838.mrc'),
            'samplingRate': 1.0,
            'setOrigCoord': False
        }

        # Creating and launching import volumes protocol
        cls.protImportVolume = cls.newProtocol(ProtImportVolumes, **args)
        cls.launchProtocol(cls.protImportVolume)
    
    def _runMainMast(self, mergeMasks=False):
        # Defining output variable string
        outputVariable = 'outputMask' + ('' if mergeMasks else 's')

        # Running protocol
        protMainMast = self.newProtocol(
            ProtMainMastSegmentMap,
            inputVolume=self.protImportVolume.outputVolume,
            sym='C2',
            threshold=5.4,
            combine=mergeMasks)
        self.launchProtocol(protMainMast)

        # Checking function output
        volumesOut = getattr(protMainMast, outputVariable, None)
        self.assertIsNotNone(volumesOut, "No output volume has been found.")
        if not mergeMasks:
            for volumeOut in volumesOut:
                self.assertIsNotNone(volumeOut, "At least one of masks has not been found.")

    def testMainMast1(self):
        """First test. Runs MainMast without merging output masks."""
        print("Running MainMast without merging output masks")
        self._runMainMast()
    
    def testMainMast2(self):
        """Second test. Runs MainMast merging output masks."""
        print("Running MainMast merging output masks")
        self._runMainMast()