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
        cls._runImportVolume()

    @classmethod
    def _runImportVolume(cls):
        args = {'filesPath': cls.ds.getFile(
            'volumes/emd_3488.map'),
            'samplingRate': 1.0,
            'setOrigCoord': False
        }
        protImportVolume = cls.newProtocol(ProtImportVolumes, **args)
        cls.launchProtocol(protImportVolume)
        cls.protImportVolume = protImportVolume

    def _runemap2sec(self):
        protEmap2sec = self.newProtocol(
            ProtEmap2sec,
            inputVolume=self.protImportVolume.outputVolume,
            contour=2.75)

        self.launchProtocol(protEmap2sec)
        pdbOut = getattr(protEmap2sec, 'outputAtomStructs', None)
        self.assertIsNotNone(pdbOut)

    def testFpocket(self):
        self._runemap2sec()