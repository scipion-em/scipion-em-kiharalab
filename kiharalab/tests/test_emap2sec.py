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

# General imports
import os

# Scipion em imports
from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportVolumes, ProtImportPdb

# Plugin imports
from ..protocols import ProtEmap2sec
from .. import Plugin
from ..constants import EMAP2SEC_TYPE_EMAP2SEC, EMAP2SEC_TYPE_EMAP2SECPLUS
from ..constants import EMAP2SECPLUS_MODE_DETECT_STRUCTS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS

class TestEmap2sec(BaseTest):
	@classmethod
	def setUpClass(cls):
		setupTestProject(cls)
		cls.tmpFiles = []
		cls.ds = DataSet.getDataSet('model_building_tutorial')

		# Running test
		cls._runImportVolumes()
		cls._runImportPDB()

	@classmethod
	def _runImportVolumes(cls):
		# Creating arguments for import volumes protocol for prediction purposes
		args = {
			'filesPath': cls.ds.getFile('volumes/emd_6838.mrc'),
			'samplingRate': 1.4,
			'setOrigCoord': False
		}

		# Creating and launching import volumes protocol
		protImportVolumes = cls.newProtocol(ProtImportVolumes, **args)
		cls.launchProtocol(protImportVolumes)

		# Storing results
		cls.protImportVolumePredict = protImportVolumes

		# Creating arguments for import volumes protocol for evaluation purposes
		args = {
			'filesPath': os.path.join(Plugin._emap2secBinary, 'data', '1733.mrc'),
			'samplingRate': 1.36825,
			'setOrigCoord': False
		}

		# Creating and launching import volumes protocol
		protImportVolumes = cls.newProtocol(ProtImportVolumes, **args)
		cls.launchProtocol(protImportVolumes)

		# Storing results
		cls.protImportVolumeEvaluate = protImportVolumes
	
	@classmethod
	def _runImportPDB(cls):
		# Creating arguments for import pdb protocol
		args = {
			'inputPdbData': 1,
			'pdbFile': os.path.join(Plugin._emap2secBinary, 'data', '3c91.pdb'),
			'inputVolume': cls.protImportVolumeEvaluate.outputVolume
		}

		# Creating and launching import pdb protocol
		protImportPDB = cls.newProtocol(ProtImportPdb, **args)
		cls.launchProtocol(protImportPDB)

		# Storing results
		cls.protImportPDB = protImportPDB

	def _runEmap2sec(self):
		# Running protocol
		protEmap2sec = self.newProtocol(
			ProtEmap2sec,
			executionType=EMAP2SEC_TYPE_EMAP2SEC,
			inputVolume=self.protImportVolumePredict.outputVolume,
			contour=5.4)
		self.launchProtocol(protEmap2sec)

		# Checking function output
		pdbOut = getattr(protEmap2sec, 'outputAtomStruct', None)
		self.assertIsNotNone(pdbOut, "No output pdb has been found.")
		self.assertIsNotNone(pdbOut.getVolume(), "Output Atom Struct has no linked volume.")
	
	def _runEmap2secPlus(self, predictMode=True):
		# Running protocol
		protEmap2sec = self.newProtocol(
			ProtEmap2sec,
			executionType=EMAP2SEC_TYPE_EMAP2SECPLUS,
			inputVolume=self.protImportVolumePredict.outputVolume if predictMode else self.protImportVolumeEvaluate.outputVolume,
			mode=EMAP2SECPLUS_MODE_DETECT_STRUCTS if predictMode else EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS,
			inputStruct=None if predictMode else self.protImportPDB.outputPdb,
			contour=5.4 if predictMode else 2.5)
		self.launchProtocol(protEmap2sec)

		# Checking function output
		pdbOut = getattr(protEmap2sec, 'outputAtomStruct', None)
		self.assertIsNotNone(pdbOut, "No output pdb has been found.")
		self.assertIsNotNone(pdbOut.getVolume(), "Output Atom Struct has no linked volume.")

	def test1Emap2sec(self):
		"""First test. Runs Emap2sec."""
		print("Running Emap2sec")
		# Running Emap2sec
		self._runEmap2sec()
	
	def test2Emap2secPlus(self):
		"""Second test. Runs Emap2sec+ in prediction mode with an experimental volume type."""
		print("Running Emap2sec+ in prediction mode with an experimental volume type")
		# Running Emap2sec+ with with an experimental volume type
		self._runEmap2secPlus()
	
	def test3Emap2secPlus(self):
		"""Third test. Runs Emap2sec+ in evaluation mode with an experimental volume type."""
		print("Running Emap2sec+ in evaluation mode with an experimental volume type")
		# Running Emap2sec+ with with an experimental volume type
		self._runEmap2secPlus(predictMode=False)
		# Last test calls cleaning function so it does not count as a separate test
		self.cleanTest()
	
	def cleanTest(self):
		"""This function removes all temporary files produced during the execution."""
		# Cleaning up duplicated files
		for tmpFile in self.tmpFiles:
			if os.path.exists(tmpFile):
				os.remove(tmpFile)