# **************************************************************************
# *
# * Authors: Martín Salinas Antón (ssalinasmartin@gmail.com)
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

import os

from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportVolumes, ProtImportPdb

from ..protocols import ProtEmap2sec
from .. import Plugin
from ..constants import EMAP2SEC_TYPE_EMAP2SEC, EMAP2SEC_TYPE_EMAP2SECPLUS
from ..constants import EMAP2SECPLUS_MODE_DETECT_STRUCTS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS
from ..utils import assertHandle

class TestEmap2secBase(BaseTest):
	@classmethod
	def setUpClass(cls):
		setupTestProject(cls)
		cls.tmpFiles = []
		cls.ds = DataSet.getDataSet('model_building_tutorial')

		cls._runImportVolumes()
		cls._runImportPDB()

	@classmethod
	def _runImportVolumes(cls):
		args = {
			'filesPath': cls.ds.getFile('volumes/emd_6838.mrc'),
			'samplingRate': 1.4,
			'setOrigCoord': False
		}

		protImportVolumes = cls.newProtocol(ProtImportVolumes, **args)
		cls.launchProtocol(protImportVolumes)
		cls.protImportVolumePredict = protImportVolumes

		args = {
			'filesPath': os.path.join(Plugin._emap2secBinary, 'data', '1733.mrc'),
			'samplingRate': 1.36825,
			'setOrigCoord': False
		}

		protImportVolumes = cls.newProtocol(ProtImportVolumes, **args)
		cls.launchProtocol(protImportVolumes)
		cls.protImportVolumeEvaluate = protImportVolumes
	
	@classmethod
	def _runImportPDB(cls):
		args = {
			'inputPdbData': 1,
			'pdbFile': os.path.join(Plugin._emap2secBinary, 'data', '3c91.pdb'),
			'inputVolume': cls.protImportVolumeEvaluate.outputVolume
		}

		protImportPDB = cls.newProtocol(ProtImportPdb, **args)
		cls.launchProtocol(protImportPDB)
		cls.protImportPDB = protImportPDB

	def cleanTest(self):
		"""This function removes all temporary files produced during the execution."""
		for tmpFile in self.tmpFiles:
			if os.path.exists(tmpFile):
				os.remove(tmpFile)

class TestEmap2sec(TestEmap2secBase):
	def _runEmap2sec(self):
		protEmap2sec = self.newProtocol(
			ProtEmap2sec,
			executionType=EMAP2SEC_TYPE_EMAP2SEC,
			inputVolume=self.protImportVolumePredict.outputVolume,
			contour=5.4)
		self.launchProtocol(protEmap2sec)

		pdbOut = getattr(protEmap2sec, 'outputAtomStruct', None)
		assertHandle(self.assertIsNotNone, pdbOut, message="No output pdb has been found.")
		assertHandle(self.assertIsNotNone, pdbOut.getVolume(), message="Output Atom Struct has no linked volume.")

	def testEmap2sec(self):
		"""First test. Runs Emap2sec."""
		print("Running Emap2sec")
		self._runEmap2sec()
		self.cleanTest()

class TestEmap2secPlus(TestEmap2secBase):
	def _runEmap2secPlus(self, predictMode=True):
		protEmap2sec = self.newProtocol(
			ProtEmap2sec,
			executionType=EMAP2SEC_TYPE_EMAP2SECPLUS,
			inputVolume=self.protImportVolumePredict.outputVolume if predictMode else self.protImportVolumeEvaluate.outputVolume,
			mode=EMAP2SECPLUS_MODE_DETECT_STRUCTS if predictMode else EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS,
			inputStruct=None if predictMode else self.protImportPDB.outputPdb,
			contour=5.4 if predictMode else 2.5)
		self.launchProtocol(protEmap2sec)

		pdbOut = getattr(protEmap2sec, 'outputAtomStruct', None)
		assertHandle(self.assertIsNotNone, pdbOut, message="No output pdb has been found.")
		assertHandle(self.assertIsNotNone, pdbOut.getVolume(), message="Output Atom Struct has no linked volume.")
	
	def test1Emap2secPlus(self):
		"""Second test. Runs Emap2sec+ in prediction mode with an experimental volume type."""
		print("Running Emap2sec+ in prediction mode with an experimental volume type")
		self._runEmap2secPlus()
	
	def test2Emap2secPlus(self):
		"""Third test. Runs Emap2sec+ in evaluation mode with an experimental volume type."""
		print("Running Emap2sec+ in evaluation mode with an experimental volume type")
		self._runEmap2secPlus(predictMode=False)
		self.cleanTest()
