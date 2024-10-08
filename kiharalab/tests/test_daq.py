# **************************************************************************
# *
# * Authors:		Daniel Del Hoyo (ddelhoyo@cnb.csic.es)
# *
# * Unidad de Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307 USA
# *
# * All comments concerning this program package may be sent to the
# * e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportPdb, ProtImportVolumes

from ..protocols import ProtDAQValidation
from ..utils import assertHandle

class TestDAQ(BaseTest):
	@classmethod
	def setUpClass(cls):
		cls.ds = DataSet.getDataSet('model_building_tutorial')

		setupTestProject(cls)
		cls._runImportPDB()
		cls._runImportVolume()

	@classmethod
	def _runImportPDB(cls):
		protImportPDB = cls.newProtocol(
			ProtImportPdb,
			inputPdbData=1,
			pdbFile=cls.ds.getFile('PDBx_mmCIF/5ni1.pdb'))
		cls.launchProtocol(protImportPDB)
		cls.protImportPDB = protImportPDB

	@classmethod
	def _runImportVolume(cls):
		args = {'filesPath': cls.ds.getFile(
			'volumes/emd_3488.map'),
			'samplingRate': 1.05,
			'setOrigCoord': True,
			'x': 0.0,
			'y': 0.0,
			'z': 0.0
		}
		protImportVolume = cls.newProtocol(ProtImportVolumes, **args)
		cls.launchProtocol(protImportVolume)
		cls.protImportVolume = protImportVolume

	def _runDAQ(self):
		protDAQ = self.newProtocol(
			ProtDAQValidation,
			inputAtomStruct=self.protImportPDB.outputPdb,
			inputVolume=self.protImportVolume.outputVolume,
			stride=2)

		self.launchProtocol(protDAQ)
		assertHandle(self.assertIsNotNone, getattr(protDAQ, 'outputAtomStruct', None))

	def testDAQ(self):
		self._runDAQ()
