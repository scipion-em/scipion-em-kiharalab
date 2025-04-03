# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors: Daniel Del Hoyo (ddelhoyo@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
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


"""
This protocol is used to perform a pocket search on a protein structure using the FPocket software
"""
import os, shutil, time
from decimal import Decimal

from pyworkflow.protocol import params
from pwem.protocols import EMProtocol
from pwem.objects import AtomStruct
from pwem.convert.atom_struct import toPdb, toCIF, AtomicStructHandler, addScipionAttribute
from pwem.convert import Ccp4Header
from pyworkflow.utils import Message, weakImport
from pwem.viewers.viewer_chimera import Chimera
from pwem.emlib.image import ImageHandler

from kiharalab import Plugin

class ProtDAQValidation(EMProtocol):
	"""
	Executes the DAQ software to validate a structure model
	"""
	_label = 'DAQ model validation'
	_ATTRNAME = 'DAQ_score'
	_OUTNAME = 'outputAtomStruct'
	_possibleOutputs = {_OUTNAME: AtomStruct}

	# -------------------------- DEFINE param functions ----------------------
	def _defineParams(self, form):
		""" """
		form.addHidden(params.GPU_LIST, params.StringParam, default='0', label="Choose GPU IDs",
			help="Add a list of GPU devices that can be used")

		form.addSection(label=Message.LABEL_INPUT)
		form.addParam('inputAtomStruct', params.PointerParam,
			pointerClass='AtomStruct', allowsNull=False,
			label="Input atom structure: ",
			help='Select the atom structure to be validated')

		form.addParam('inputVolume', params.PointerParam,
			pointerClass='Volume', allowsNull=True,
			label="Input volume: ",
			help='Select the electron map of the structure')
		form.addParam('chimeraResampling', params.BooleanParam,
			label="Resample using ChimeraX: ", default=True,
			help='Resample volume to 1.0 using ChimeraX software')

		group = form.addGroup('Network parameters')
		group.addParam('window', params.IntParam, default='9', label='Half window size: ',
			help='Half of the window size that used for smoothing the residue-wise score '
			'based on a sliding window scanning the entire sequence')
		group.addParam('stride', params.IntParam, default='1', label='Stride: ',
			help='Stride step to scan the maps.')

		group.addParam('voxelSize', params.IntParam, default='11',
			label='Voxel size: ', expertLevel=params.LEVEL_ADVANCED,
			help='Input voxel size')
		group.addParam('batchSize', params.IntParam, default='256',
			label='Batch size: ', expertLevel=params.LEVEL_ADVANCED,
			help='Batch size for inference')
		group.addParam('cardinality', params.IntParam, default='32',
			label='Cardinality: ', expertLevel=params.LEVEL_ADVANCED,
			help='ResNeXt cardinality')

	# --------------------------- STEPS functions ------------------------------
	def _insertAllSteps(self):
		# Insert processing steps
		self._insertFunctionStep('convertInputStep')
		self._insertFunctionStep('DAQStep')
		self._insertFunctionStep('createOutputStep')

	def convertInputStep(self):
		ext = os.path.splitext(self.getStructFile())[1]
		pdbFile = self.getPdbStruct()
		if ext not in ['.pdb', '.ent']:
			toPdb(self.getStructFile(), pdbFile)
		else:
			shutil.copy(self.getStructFile(), pdbFile)

		inVol = self._getInputVolume()
		inVolFile, inVolSR = inVol.getFileName(), inVol.getSamplingRate()

		#Convert volume to mrc
		mrcFile = self._getTmpPath('inpVolume.mrc')
		ImageHandler().convert(inVolFile, mrcFile)
		Ccp4Header.fixFile(mrcFile, mrcFile, inVol.getOrigin(force=True).getShifts(),
						   inVolSR, Ccp4Header.START)

		#Resample volume to 1A/px with ChimeraX if present
		daqSR = 1.0
		if self.chimeraResampling and Decimal(inVol.getSamplingRate()) != Decimal(daqSR):
			if chimeraInstalled():
				resampledFile = os.path.abspath(self._getTmpPath('resampled.mrc'))
				mrcFile = self.chimeraResample(mrcFile, daqSR, resampledFile)
				inVolSR = daqSR
			else:
				print('ChimeraX not found, resampling with DAQ (slower than ChimeraX)')

		# Volume header fixed to have correct origin
		Ccp4Header.fixFile(mrcFile, self.getLocalVolumeFile(), inVol.getOrigin(force=True).getShifts(),
			inVolSR, Ccp4Header.ORIGIN)

	def DAQStep(self):
		"""
		Run DAQ script.
		"""
		outDir = self._getTmpPath('predictions')
		args = self.getDAQArgs()

		fullProgram = f'{Plugin.getCondaActivationCmd()} {Plugin.getProtocolActivationCommand("daq")} && python'
		if 'main.py' not in args:
			args = f'{Plugin._daqBinary}/main.py {args}'
		self.runJob(fullProgram, args, cwd=Plugin._daqBinary)

		if outDir is None:
			outDir = self._getExtraPath('predictions')

		daqDir = os.path.join(Plugin._daqBinary, 'Predict_Result', self.getVolumeName())
		shutil.copytree(daqDir, outDir)
		shutil.rmtree(daqDir)
	
	def createOutputStep(self):
		outStructFileName = self._getPath('outputStructure.cif')
		outDAQFile = os.path.abspath(self._getTmpPath('predictions/daq_score_w9.pdb'))

		#Write DAQ_score in a section of the output cif file
		ASH = AtomicStructHandler()
		daqScoresDic = self.parseDAQScores(outDAQFile)
		inpAS = toCIF(self.inputAtomStruct.get().getFileName(), self._getTmpPath('inputStruct.cif'))
		cifDic = ASH.readLowLevel(inpAS)
		cifDic = addScipionAttribute(cifDic, daqScoresDic, self._ATTRNAME)
		ASH._writeLowLevel(outStructFileName, cifDic)

		AS = AtomStruct(filename=outStructFileName)
		outVol = self._getInputVolume().clone()
		outVol.setLocation(self.getLocalVolumeFile())
		if self.chimeraResampling and Decimal(self._getInputVolume().getSamplingRate()) != Decimal(1.0) and chimeraInstalled():
			outVol.setSamplingRate(1.0)
		AS.setVolume(outVol)

		self._defineOutputs(**{self._OUTNAME: AS})

	# --------------------------- INFO functions -----------------------------------
	def _summary(self):
		summary = []
		return summary

	def _methods(self):
		methods = []
		return methods

	def _warnings(self):
		""" Try to find warnings on define params. """
		warnings=[]
		if self.chimeraResampling and not chimeraInstalled():
			warnings.append(f'Chimera program is not found were it was expected: \n\n{Chimera.getProgram()}\n\n' \
				'Either install ChimeraX in this path or install our ' \
				'scipion-em-chimera plugin')
		return warnings

	# --------------------------- UTILS functions -----------------------------------
	def getDAQArgs(self):
		args = (f' --mode=0 -F {os.path.abspath(self.getLocalVolumeFile())} '
						f'-P {self.getPdbStruct()} --window {self.window.get()} --stride {self.stride.get()}')

		args += f' --voxel_size {self.voxelSize.get()} --batch_size {self.batchSize.get()} --cardinality {self.cardinality.get()}'

		gpuId = self.getGPUIds()[0]
		if not gpuId:
			gpuId = 0
		args += f' --gpu {gpuId}'
		
		return args

	def _getInputVolume(self):
		if self.inputVolume.get() is None:
			fnVol = self.inputAtomStruct.get().getVolume()
		else:
			fnVol = self.inputVolume.get()
		return fnVol

	def getStructFile(self):
		return os.path.abspath(self.inputAtomStruct.get().getFileName())

	def getPdbStruct(self):
		return os.path.abspath(self._getTmpPath(self.getStructName())) + ".pdb"

	def getVolumeFile(self):
		return os.path.abspath(self._getInputVolume().getFileName())

	def getStructName(self):
		return os.path.basename(os.path.splitext(self.getStructFile())[0])

	def getVolumeName(self):
		return os.path.basename(os.path.splitext(self.getLocalVolumeFile())[0])

	def getLocalVolumeFile(self):
		oriName = os.path.basename(os.path.splitext(self.getVolumeFile())[0])
		return self._getExtraPath(f'{oriName}_{self.getObjId()}.mrc')

	def parseDAQScores(self, pdbFile):
		'''Return a dictionary with {spec: value}
		"spec" should be a chimera specifier. In this case:  chainId:residueIdx'''
		daqDic = {}
		with open(pdbFile) as f:
			for line in f:
				if line.startswith('ATOM') or line.startswith('HETATM'):
					resId = f'{line[21].strip()}:{line[22:26].strip()}'
					if resId not in daqDic:
						daqScore = line[60:66].strip()
						daqDic[resId] = daqScore
		return daqDic
	
	def getGPUIds(self):
		return getattr(self, params.GPU_LIST).get().split(',')

	def getDAQScoreFile(self):
		return self._getPath(f'{self._ATTRNAME}.defattr')

	def chimeraResampleScript(self, inVolFile, newSampling, outFile):
		scriptFn = self._getExtraPath('resampleVolume.cxc')
		with open(scriptFn, 'w') as f:
			f.write(f'cd {os.getcwd()}\n')
			f.write(f"open {inVolFile}\n")
			f.write(f'vol resample #1 spacing {newSampling}\n')
			f.write(f'save {outFile} model #2\n')
			f.write('exit\n')
		return scriptFn

	def chimeraResample(self, inVolFile, newSR, outFile):
		with weakImport("chimera"):
			from chimera import Plugin as chimeraPlugin
			resampleScript = self.chimeraResampleScript(inVolFile, newSampling=newSR, outFile=outFile)
			chimeraPlugin.runChimeraProgram(f"{chimeraPlugin.getProgram()} --nogui --silent",
				resampleScript, cwd=os.getcwd())
			while not os.path.exists(outFile):
				time.sleep(1)
		return outFile

def chimeraInstalled():
  return Chimera.getHome() and os.path.exists(Chimera.getProgram())
