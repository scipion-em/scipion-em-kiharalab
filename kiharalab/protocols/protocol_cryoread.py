# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors: Joon Hong Park (park1617@purdue.edu)
# *
# * Purdue University - Kihara Lab
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
# * All comments concerning this program package may be sent to the
# * e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os, shutil

from pyworkflow.protocol import params
from pyworkflow.utils import Message
from pwem.protocols import EMProtocol
from pwem.objects import AtomStruct
from pwem.convert import Ccp4Header
from pwem.convert.atom_struct import toCIF, AtomicStructHandler, addScipionAttribute
from pwem.emlib.image import ImageHandler

from kiharalab import Plugin

class ProtCryoREAD(EMProtocol):
    """
    Executes CryoREAD software to construct full atomic structure of DNA/RNA.
    """
    _label = 'CryoREAD'
    _ATTRNAME = 'CryoREAD_score'
    _OUTNAME = 'outputAtomStruct'
    _possibleOutputs = {_OUTNAME: AtomStruct}

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """Define parameters for the CryoREAD protocol."""
        form.addHidden(params.USE_GPU, params.BooleanParam, default=True,
                       label="Use GPU for execution: ",
                       help="This protocol has both CPU and GPU implementation. Select the one you want to use.")

        form.addHidden(params.GPU_LIST, params.StringParam, default='0', label="Choose GPU IDs",
                       help="Add a list of GPU devices that can be used")

        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputVolume', params.PointerParam,
                      pointerClass='Volume', allowsNull=False,
                      label="Input 3D cryo-EM map: ",
                      help='Select the 3D cry-EM map to be analyzed in .map or .mrc format.')

        form.addParam('inputSequence', params.FileParam, allowsNull=True,
                      label="Input Sequence (optional): ",
                      help='Select the sequence in .fasta format. It is optional.')

        group = form.addGroup('CryoREAD parameters')
        group.addParam('contour_level', params.FloatParam, default=0.0, label='Contour level: ',
                       help='Contour level for input map.')
        group.addParam('resolution', params.FloatParam, default=2.5, label='Resolution: ',
                       help='Resolution of maps, used for final structure refinement.')
        group.addParam('batch_size', params.IntParam, default=4, label='Batch size: ',
                       expertLevel=params.LEVEL_ADVANCED,
                       help='Batch size for inference of network.')
        group.addParam('rule_soft', params.IntParam, default=0, label='Rule soft: ',
                       expertLevel=params.LEVEL_ADVANCED,
                       help='Use strict/soft rules to assemble collected fragments in DP step.(Integer)')
        group.addParam('thread', params.IntParam, default=1, label='Thread: ',
                       expertLevel=params.LEVEL_ADVANCED,
                       help='Use multiple threads for fragment-based sequence assignment.')


    # --------------------------- STEPS functions ----------------------------------
    def _insertAllSteps(self):
        """Insert processing steps for the protocol."""
        self._insertFunctionStep('convertInputStep')
        self._insertFunctionStep('cryoREADStep')
        self._insertFunctionStep('createOutputStep')

    def convertInputStep(self):
        ext = os.path.splitext(self.getVolumeFile())[1]
        if ext not in ['.map', '.mrc']:
            print('Input file format is not correct. Please check.')

        inVol = self._getInputVolume()
        inVolFile, inVolSR = inVol.getFileName(), inVol.getSamplingRate()

        # Convert volume to mrc
        mrcFile = self._getTmpPath('inpVolume.mrc')
        ImageHandler().convert(inVolFile, mrcFile)
        Ccp4Header.fixFile(mrcFile, mrcFile, inVol.getOrigin(force=True).getShifts(),
                           inVolSR, Ccp4Header.START)


        # Volume header fixed to have correct origin
        Ccp4Header.fixFile(mrcFile, self.getLocalVolumeFile(), inVol.getOrigin(force=True).getShifts(), inVolSR,
                           Ccp4Header.ORIGIN)

    def cryoREADStep(self):
        inputFilePath = self.getLocalVolumeFile()
        if not os.path.exists(inputFilePath):
            self.error("Input file not found: %s" % inputFilePath)
            return
        outDir = self._getTmpPath('predictions')
        args = self.getcryoREADArgs()

        envActivationCommand = "{} {}".format(Plugin.getCondaActivationCmd(),
                                              Plugin.getProtocolActivationCommand('cryoREAD'))
        fullProgram = '{} && {}'.format(envActivationCommand, 'python3')


        if 'main.py' not in args:
            args = '{}/main.py{}'.format(Plugin._cryoREADBinary, args)

        print(f'Running CryoREAD with input file: {inputFilePath}')
        self.runJob(fullProgram, args, cwd=Plugin._cryoREADBinary)

        if outDir is None:
            outDir = self._getExtraPath('predictions')

        cryoDir = os.path.join(Plugin._cryoREADBinary, 'Predict_Result', self.getVolumeName())
        shutil.copytree(cryoDir, outDir)
        shutil.rmtree(cryoDir)

    def createOutputStep(self):
        outStructFileName = self._getPath('CryoREAD.cif')
        outPdbFileName = os.path.abspath(self._getTmpPath('predictions/CryoREAD_norefine.pdb'))

        ASH = AtomicStructHandler()
        cryoScoresDic = self.parseCryoScores(outPdbFileName)

        outputVolume = toCIF(outPdbFileName, self._getTmpPath('inputStruct.cif'))
        cifDic = ASH.readLowLevel(outputVolume)
        cifDic = addScipionAttribute(cifDic, cryoScoresDic, self._ATTRNAME)
        ASH._writeLowLevel(outStructFileName, cifDic)

        # Create AtomStruct object with the CIF file
        AS = AtomStruct(filename=outStructFileName)

        # Set the volume of the AtomStruct object
        outVol = self._getInputVolume().clone()
        outVol.setLocation(self.getLocalVolumeFile())
        AS.setVolume(outVol)

        # Define the outputs for the protocol
        self._defineOutputs(**{self._OUTNAME: AS})

    # --------------------------- INFO functions -----------------------------------
    def _validate(self):
        errors = []

        return errors

    def _summary(self):
        summary = []
        return summary

    def _methods(self):
        methods = []
        return methods
    # --------------------------- UTILS functions -----------------------------------
    def getcryoREADArgs(self):
        args = ' --mode=0 -F={} -M={}/best_model --contour={} --resolution={}'.format(
            self.getLocalVolumeFile(), Plugin._cryoREADBinary, self.contour_level.get(), self.resolution.get())

        args += ' --batch_size={} --rule_soft={} --thread={}'.format(
            self.batch_size.get(), self.rule_soft.get(), self.thread.get())

        if self.inputSequence.hasValue():
            args += ' -P={}'.format(self.getFastaFilePath())
        else:
            args += ' --no_seqinfo'

        if getattr(self, params.USE_GPU):
            args += ' --gpu={}'.format(self.getGPUIds()[0])

        return args

    def _getInputVolume(self):
        return self.inputVolume.get()

    def getVolumeFile(self):
        return os.path.abspath(self._getInputVolume().getFileName())

    def getVolumeName(self):
        return os.path.basename(os.path.splitext(self.getLocalVolumeFile())[0])

    def getLocalVolumeFile(self):
        oriName = os.path.basename(os.path.splitext(self.getVolumeFile())[0])
        localPath = self._getExtraPath('{}_{}.mrc'.format(oriName, self.getObjId()))
        return os.path.abspath(localPath)

    def getFastaFilePath(self):
        return self.inputSequence.get()

    def getGPUIds(self):
        return getattr(self, params.GPU_LIST).get().split(',')

    def parseCryoScores(self, pdbFile):
        cryoDic = {}
        with open(pdbFile) as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    resId = '{}:{}'.format(line[21].strip(), line[22:26].strip())
                    if resId not in cryoDic:
                        cryoScore = line[60:66].strip()
                        cryoDic[resId] = cryoScore
        return cryoDic
