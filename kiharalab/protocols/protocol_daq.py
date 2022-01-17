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
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************


"""
This protocol is used to perform a pocket search on a protein structure using the FPocket software

"""
import os, shutil

from pyworkflow.protocol import params
from pwem.protocols import EMProtocol
from pwem.objects import AtomStruct, Volume
from pwem.convert.atom_struct import toPdb, toCIF, AtomicStructHandler, addScipionAttribute
from pyworkflow.utils import Message

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
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputAtomStruct', params.PointerParam,
                       pointerClass='AtomStruct', allowsNull=False,
                       label="Input atom structure: ",
                       help='Select the atom structure to be validated')

        form.addParam('inputVolume', params.PointerParam,
                      pointerClass='Volume', allowsNull=True,
                      label="Input volume: ",
                      help='Select the electron map of the structure')

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
        name, ext = os.path.splitext(self.getStructFile())
        pdbFile = self.getPdbStruct()
        if ext != '.pdb':
            toPdb(self.getStructFile(), pdbFile)
        else:
            shutil.copy(self.getStructFile(), pdbFile)

        #Renaming volume to add protocol ID (results saved in different directory in DAQ repo)
        localVolumeFile = self.getLocalVolumeFile()
        shutil.copy(self.getVolumeFile(), localVolumeFile)

    def DAQStep(self):
        args = self.getDAQArgs()
        Plugin.runDAQ(self, args=args, outDir=self._getExtraPath('predictions'))

    def createOutputStep(self):
        outStructFileName = self._getPath('outputStructure.cif')
        outDQAFile = self._getExtraPath('predictions/dqa_score_w9.pdb')

        #Write DAQ_score in a section of the output cif file
        ASH = AtomicStructHandler()
        daqScoresDic = self.parseDAQScores(outDQAFile)
        inpAS = toCIF(self.inputAtomStruct.get().getFileName(), self._getTmpPath('inputStruct.cif'))
        cifDic = ASH.readLowLevel(inpAS)
        cifDic = addScipionAttribute(cifDic, daqScoresDic, self._ATTRNAME)
        ASH._writeLowLevel(outStructFileName, cifDic)

        AS = AtomStruct(filename=outStructFileName)
        AS.setVolume(self._getInputVolume())

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
        return warnings

    # --------------------------- UTILS functions -----------------------------------
    def getDAQArgs(self):
        args = ' --mode=0 -F {} -P {} --window {} --stride {}'. \
          format(os.path.abspath(self.getLocalVolumeFile()), os.path.abspath(self.getPdbStruct()),
                 self.window.get(), self.stride.get())

        args += ' --voxel_size {} --batch_size {} --cardinality {}'.\
          format(self.voxelSize.get(), self.batchSize.get(), self.cardinality.get())
        return args

    def _getInputVolume(self):
      if self.inputVolume.get() is None:
        fnVol = self.inputAtomStruct.get().getVolume()
      else:
        fnVol = self.inputVolume.get()
      return fnVol

    def getStructFile(self):
        return os.path.abspath(self.inputAtomStruct.get().getFileName())

    def getVolumeFile(self):
        return os.path.abspath(self._getInputVolume().getFileName())

    def getStructName(self):
        return os.path.basename(os.path.splitext(self.getStructFile())[0])

    def getVolumeName(self):
        return os.path.basename(os.path.splitext(self.getLocalVolumeFile())[0])

    def getPdbStruct(self):
        return self._getExtraPath(self.getStructName()) + '.pdb'

    def getLocalVolumeFile(self):
        oriName = os.path.basename(os.path.splitext(self.getVolumeFile())[0])
        return self._getExtraPath('{}_{}.mrc'.format(oriName, self.getObjId()))

    def parseDAQScores(self, pdbFile):
        '''Return a dictionary with {spec: value}
        "spec" should be a chimera specifier'''
        from pwchem.utils import splitPDBLine
        daqDic = {}
        with open(pdbFile) as f:
            for line in f:
                pdbLine = splitPDBLine(line)
                if pdbLine is not None:
                    resId = '{}:{}'.format(pdbLine[4], pdbLine[5])
                    if not resId in daqDic:
                      daqScore = pdbLine[10]
                      daqDic[resId] = daqScore
        return daqDic

    def getDAQScoreFile(self):
      return self._getPath('{}.defattr'.format(self._ATTRNAME))


