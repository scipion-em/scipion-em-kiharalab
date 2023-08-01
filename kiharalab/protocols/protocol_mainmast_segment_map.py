# **************************************************************************
# *
# * Authors:		David Herreros Calero (dherreros@cnb.csic.es)
# *							Martín Salinas (martin.salinas@cnb.csic.es)
# *
# * Unidad de Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
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
import os, glob
import numpy as np

# Base Scipion imports
from pwem.protocols import EMProtocol
from pyworkflow.protocol import params
from pwem.emlib.image import ImageHandler
from pwem.objects import Volume, SetOfVolumes

# Plugin imports
from kiharalab import Plugin as Mainmast
try:
	from phenix import Plugin as Phenix
except ModuleNotFoundError:
	pass

# Constants
REGIONS_PATTERN = "region*.mrc"

class ProtMainMastSegmentMap(EMProtocol):
	"""Protcol to perform the segmentation of maps into different regions by using
	mainmast software.
	For more information, follow the next link:
	http://kiharalab.org/mainmast_seg/index.html"""
	_label = 'segment map'
	_OUTMASKNAME = 'outputMask'
	_OUTMASKSNAME = 'outputMasks'
	_possibleOutputs = {_OUTMASKNAME: Volume, _OUTMASKSNAME: SetOfVolumes}

	# -------------------------- DEFINE param functions ----------------------
	def _defineParams(self, form):
		form.addSection(label='Input data')
		form.addParam('inputVolume', params.PointerParam, pointerClass='Volume', label='Input volume', important=True,
										help='Select a Volume to be segmented.')
		form.addParam('sym', params.StringParam, label='Map symmetry',
										help='Point group symmetry of input volume (all point group symmetries are allowed '
												'except C1).')
		form.addParam('threshold', params.FloatParam, default=0.0, label='Threshold',
										help='Threshold of density map.')
		form.addParam('combine', params.BooleanParam, default=False, label='Combine masks',
										help='If selected, all the segmented regions detected will be combine into a '
												'single identifier mask.\nThis means that, if combine is selected, output object'
												'will be Volume type, or SetOfvolumes otherwise.')
		form.addParam('cleanTmps', params.BooleanParam, default='True', label='Clean temporary files: ', expertLevel=params.LEVEL_ADVANCED,
										help='Clean temporary files after finishing the execution.\nThis is useful to reduce unnecessary disk usage.')
		form.addParallelSection(threads=4, mpi=0)

	# --------------------------- STEPS functions ------------------------------
	def _insertAllSteps(self):
		"""
		This method defines the functions that will be run during the execution of this protocol.
		"""
		self._insertFunctionStep('createSymmetryMatrixStep')
		self._insertFunctionStep('segmentStep')
		self._insertFunctionStep('createOutputStep')

	def createSymmetryMatrixStep(self):
		"""
		This method creates the symmetry matrix needed for MainMast.
		"""
		# Getting input file
		pathMap = self.getVolumeAbsolutePath()

		# Generating args for Phenix
		args = '%s symmetry=%s' % (pathMap, self.sym.get())

		# Running Phenix command
		Phenix.runPhenixProgram(Phenix.getProgram('map_symmetry.py'), args, cwd=self._getExtraPath())

		# Generating args and running last matrix conversion phase
		args = '%s > sym_mat.txt' % ('symmetry_from_map.ncs_spec')
		self.convertMatrix(args, cwd=self._getExtraPath())

	def segmentStep(self):
		"""
		This method runs MainMast's software using the previously created conversion matrix.
		"""
		# Getting input file
		pathMap = self.getVolumeAbsolutePath()

		# Getting conversion matrix file
		pathMatrix = self.scapePath(os.path.abspath(self._getExtraPath('sym_mat.txt')))

		# Generating args and running MainMast
		args = '-i %s -Y %s -c %d -t %f -M -W > contour.cif' % (pathMap, pathMatrix, self.numberOfThreads.get(),
			self.threshold.get())
		self.runSegmentation(args, cwd=self._getExtraPath())

	def createOutputStep(self):
		"""
		This method processes the output files generated by the protocol and imports them into Scipion objects.
		"""
		# Getting region files
		regionFiles = sorted(glob.glob(self._getExtraPath(REGIONS_PATTERN)))
		if len(regionFiles) == 0:
			# If region files were not found, throw an exception and cancel execution
			raise FileNotFoundError("Region files were not generated after MainMast's execution."
				" This could be caused by an insufficient amount of dynamic memory being available to the process, "
				"specially if the execution only took some seconds. Try providing more RAM to your system, or"
				" to Scipion if any memory limits have been set.")
		
		if self.combine.get():
			# If combine is selected, return object is of type Volume
			ih = ImageHandler()
			outMask = ih.createImage()

			# Collecting data for every region file into a single mask
			for idx, image in enumerate(regionFiles):
				region = ih.read(image).getData()
				region[region != 0] = 1
				region *= (idx+1)
				if idx == 0:
					outData = np.zeros(region.shape, float)
				outData += region
			
			# Writing combined mask
			outMask.setData(outData)
			ih.write(outMask, self._getExtraPath('outMask.mrc'))

			# Creating output volume from written mask
			volume = Volume()
			volume.setSamplingRate(self.inputVolume.get().getSamplingRate())
			volume.setLocation(self._getExtraPath('outMask.mrc'))

			# Defining protocol output and source relation
			self._defineOutputs(**{self._OUTMASKNAME: volume})
			self._defineSourceRelation(self.inputVolume, volume)
		else:
			# If combine is not selected, return object is of type SetOfVolumes
			outSet = self._createSetOfVolumes()
			samplingRate = self.inputVolume.get().getSamplingRate()
			outSet.setSamplingRate(samplingRate)

			# Creating a Volume object for each region file
			for image in regionFiles:
				volume = Volume()
				volume.setSamplingRate(samplingRate)
				volume.setLocation(image)
				outSet.append(volume)
			
			# Defining protocol output and source relation
			self._defineOutputs(**{self._OUTMASKSNAME: outSet})
			self._defineSourceRelation(self.inputVolume, outSet)
		
		# If clean is selected, clean temporary files
		if self.cleanTmps.get():
			self.cleanTmpfiles(self.getTmpFiles())
	
	# --------------------------- EXECUTION functions -----------------------------------
	def runSegmentation(self, args, cwd=None):
		"""
		Run segmentation phase for MainMast.
		"""
		mainMastCall = os.path.join(Mainmast._mainmastBinary, 'MainmastSeg')
		self.runJob(mainMastCall, args, cwd=cwd)
	
	def convertMatrix(self, args, cwd=None):
		"""
		Run matrix conversion phase for MainMast.
		"""
		convertCall = os.path.join(Mainmast._mainmastBinary, 'conv_ncs.pl')
		self.runJob(convertCall, args, cwd=cwd)

	def cleanTmpfiles(self, tmpFiles=[]):
		"""
		This method removes all temporary files to reduce disk usage.
		"""
		for tmpFile in tmpFiles:
			self.runJob("rm -rf", tmpFile, cwd=Mainmast._mainmastBinary)

	# --------------------------- UTILS functions ------------------------------
	def scapePath(self, path):
		"""
		This function returns the given path with all the spaces in folder names scaped to avoid errors.
		"""
		# os.path.baspath adds '\\' when finding a foldername with '\ ', so '\\\' needs to be replaced with ''
		# Then, '\' is inserted before every space again, to include now possible folders with spaces in the absolute path
		return path.replace('\\\ ', ' ').replace(' ', '\ ')
	
	def getVolumeAbsolutePath(self):
		"""
		This method returns the absolute path for the volume file.
		Example: '/home/username/documents/test/import_file.mrc'
		"""
		return self.scapePath(os.path.abspath(self.inputVolume.get().getFileName()))
	
	def getExtraFileAbsolutePath(self, fileName):
		"""
		This method returns the absolute path for the given extra filename.
		Example: '/home/username/ScipionUserData/projects/MainMast/Runs/ProtMainMastSegmentMap/extra/contour.cif'
		"""
		return self.scapePath(os.path.abspath(self._getExtraPath(fileName)))
	
	def getTmpFiles(self):
		"""
		This method returns a list with the absolute paths for the temporary files.
		Example: ['/home/username/ScipionUserData/projects/MainMast/Runs/ProtMainMastSegmentMap/extra/contour.cif']
		"""
		# Defining fixed tmp files
		tmpFiles = [
			self.getExtraFileAbsolutePath('contour.cif'),
			self.getExtraFileAbsolutePath('sym_mat.txt'),
			self.getExtraFileAbsolutePath('symmetry_from_map.ncs_spec')
		]

		# if combine is selected, region files are not needed any more
		if self.combine.get():
			regionFiles = sorted(glob.glob(self.getExtraFileAbsolutePath(REGIONS_PATTERN)))
			for regionFile in regionFiles:
				tmpFiles.append(regionFile)

		return tmpFiles

	# --------------------------- INFO functions -----------------------------------
	def _summary(self):
		"""
		This method returns a summary of the text provided by '_methods'.
		"""
		summary = ["Input Volume provided: %s\n" % self.inputVolume.get().getFileName()]
		if self.getOutputsSize() >= 1:
			regions = len(glob.glob(self._getExtraPath(REGIONS_PATTERN)))
			if hasattr(self, 'outputMasks'):
				msg = ("A total of %d regions have been segmented" % regions)
				summary.append(msg)
			if hasattr(self, 'outputMask'):
				msg = ("Output regions combined to an indentifier mask with %d different regions" % regions)
				summary.append(msg)
		else:
			summary.append("Segmentation not ready yet.")
		return summary

	def _methods(self):
		"""
		This method returns a text intended to be copied and pasted in the paper section 'materials & methods'.
		"""
		methodsMsgs = [
			'*Input volume:* %s' % self.inputVolume.get().getFileName(),
			'*Map symmetry:* %s' % self.sym.get(),
			'*Map threshold:* %d' % self.threshold.get(),
			'*Regions combined:* %r' % self.combine.get()
		]
		if self.getOutputsSize() >= 1:
			regions = len(glob.glob(self._getExtraPath(REGIONS_PATTERN)))
			msg = ("*Regions segmented:* %d" % regions)
			methodsMsgs.append(msg)
		else:
			methodsMsgs.append("Segmentation not ready yet.")
		return methodsMsgs
	
	def _validate(self):
		"""
		This method validates the received params and checks that they all fullfill the requirements needed to run the protocol.
		"""
		errors = []

		# If symmetry is not C* where * is an integer greater than 1, show error
		symmetry = self.sym.get()
		if symmetry == '':
			errors.append('Error: Symmetry cannot be empty.')
		else:
			if len(symmetry) < 2 or symmetry[0] != 'C' or not symmetry[1:].isdigit():
				errors.append('Error: Invalid value for symmetry. Value needs to be C*, where * is any positive integer greater than 1.')
			else:
				if int(symmetry[1:]) < 2:
					errors.append('Error: Symmetry needs to be C2 or above.')
		
		# Check if Phenix plugin is installed
		try:
			import phenix
		except ModuleNotFoundError:
			errors.append("Plugin scipion-em-phenix is not installed!\nYou can find it at https://github.com/scipion-em/scipion-em-phenix")

		return errors
