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
This protocol is used to identify protein secondary structures, alpha helices, beta sheets,
others (coils/turns), in cryo-Electron Microscopy (EM) maps of medium to low resolution.
"""
import os, shutil

from pyworkflow.protocol import params
from pwem.protocols import EMProtocol
from pwem.objects import AtomStruct
from pwem.convert.atom_struct import toPdb
from pyworkflow.utils import Message

from kiharalab import Plugin
from kiharalab.constants import *

class ProtEmap2sec(EMProtocol):
    """
    Executes the Emap2sec software to indentify protein secondary strctures, alpha helices, beta sheets, and others
    """
    _label = 'Emap2sec'
    _possibleOutputs = {'outputAtomStruct1': AtomStruct, 'outputAtomStruct2': AtomStruct}

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """
        Defines Emap2sec's input params.
        """
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputVolume', params.PointerParam,
                      pointerClass='Volume', allowsNull=False,
                      label="Input volume: ",
                      help='Select the electron map to be processed')

        trimappGroup = form.addGroup('Trimapp generation')
        trimappGroup.addParam('contour', params.FloatParam, default='2.75', label='Contour: ',
                       help='The level of isosurface to generate density values for.'
                       ' You can use a value of 0.0 for simulated maps and the author recommended contour level for experimental EM maps.')
        trimappGroup.addParam('sstep', params.IntParam, default='2', label='Stride size: ', expertLevel=params.LEVEL_ADVANCED,
                       help='This option sets the stride size of the sliding cube used for input data generation.'
                       ' We recommend using a value of 2 that slides the cube by 2Å in each direction.'
                       ' Decreasing this value to 1 produces 8 times more data (increase by a factor of 2 in each direction)'
                       ' and thus slows the running time down by 8 times so please be mindful lowering this value.')
        trimappGroup.addParam('vw', params.IntParam, default='5', label='Sliding cube dimensions: ', expertLevel=params.LEVEL_ADVANCED,
                       help='This option sets the dimensions of sliding cube used for input data generation.'
                       ' The size of the cube is calculated as 2vw+1.'
                       ' We recommend using a value of 5 for this option that generates input cube of size 11*11*11.'
                       ' Please be mindful while increasing this option as it increases the portion of an EM map a single cube covers.'
                       ' Increasing this value also increases running time.')
        trimappGroup.addParam('norm', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_NORM_GLOBAL, label='Normalization type: ',
                        expertLevel=params.LEVEL_ADVANCED, choices=['Global', 'Local'],
                        help='Set this option to normalize density values of the sliding cube, used for input data generation,'
                       ' by global or local maximum density value.')
        
        form.addSection(label=Message.LABEL_EXPERT_ADVANCE)
        visualGroup = form.addGroup('Secondary structures visualization')
        visualGroup.addParam('predict', params.BooleanParam, default='True', label='Show predicted data: ',
                        help='Show predicted data (Predicted secondary structures)')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('mainExecutionStep')
        #self._insertFunctionStep('createOutputStep')

    def mainExecutionStep(self):
        # Getting full path for input file
        inputFile = self.getVolumeAbsolutePath()

        # Defining arguments for each command to execute
        # args will be a list of strings, where each string are the arguments for a given command
        args = [
            self.getTrimappArgs(inputFile),
            self.getDatasetArgs(),
            self.getInputLocationFileArgs(),
            self.getEmap2secArgs()
        ]
        print("NAME: ", args)

        Plugin.runEmap2sec(self, args=args, outDir=self._getExtraPath('results'))
        return;

        # Separating extension from file path and name
        inputFileName, inputFileExtension = os.path.splitext(inputFile)


        print("TEST: ", os.path.basename(os.path.splitext(self.getVolumeFile())[0]).replace('import_', ''))
        print("TEST 2: ", self.getLocalVolumeFile())
        Plugin.runEmap2sec(self, args='', outDir=self._getExtraPath('results'))
        return;
        args = self.getDAQArgs()
        Plugin.runDAQ(self, args=args, outDir=self._getExtraPath('results'))

    def createOutputStep(self):
        outDir = self._getExtraPath('predictions')
        outStruct = self._getPath(self.getVolumeName() + '_1.pdb')
        print("OUTPUT: ", outDir)
        print("OUTPUT 2: ", outStruct)
        return;
        #outVolume = self._getPath(self.getStructName() + '_dqa.mrc')

        shutil.copy(os.path.join(outDir, 'dqa_score_w9.pdb'), outStruct)
        #shutil.copy(os.path.join(outDir, '{}_new.mrc'.format(self.getVolumeName())), outVolume)

        outAS = AtomStruct(filename=outStruct)
        outAS.setVolume(self.inputVolume.get())

        self._defineOutputs(outputAtomStruct=outAS)


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
    def getOutputFilePrefix(self):
        """
        This method returns the prefix that all output files generated by this protocol will have.
        This will be <protocolId>_<inputFileName>_
        """
        return '{}_{}_'.format(self.getObjId(), os.path.splitext(self.getCleanVolumeName())[0])

    def getTrimappArgs(self, inputFile):
        """
        This method returns the arguments neccessary for the trimapp generation.
        """
        return '{} -c {} -sstep {} -vw {} {} > data/{}_{}_trimapp'\
            .format(inputFile,
                self.contour.get(),
                self.sstep.get(),
                self.vw.get(),
                '-gnorm' if self.norm.get() == EMAP2SEC_NORM_GLOBAL else '-Inorm',
                self.getObjId(),
                os.path.splitext(self.getCleanVolumeName())[0])
    
    def getDatasetArgs(self):
        """
        This method returns the arguments neccessary for the dataset generation.
        """
        outputPefix = 'data/{}'.format(self.getOutputFilePrefix())
        return '{}trimapp {}dataset'.format(outputPefix, outputPefix)
    
    def getInputLocationFileArgs(self):
        """
        This method returns the arguments neccessary for input location file generation,
        used for Emap2sec.py.
        """
        outputPefix = 'data/{}'.format(self.getOutputFilePrefix())
        return '{}dataset > {}input.txt'.format(outputPefix, outputPefix)
    
    def getEmap2secArgs(self):
        """
        This method returns the arguments neccessary for the Emap2sec.py's execution.
        """
        return 'data/{}input.txt'.format(self.getOutputFilePrefix())

    def getStructFile(self):
        return os.path.abspath(self.inputAtomStruct.get().getFileName())
    
    def getStructName(self):
        return os.path.basename(os.path.splitext(self.getStructFile())[0])


    def getPdbStruct(self):
        return self._getExtraPath(self.getStructName()) + '.pdb'

    
    def getVolumeRelativePath(self):
        """
        This method returns the volume path relative to current directory.
        Example:
            if file is in /home/username/documents/test/import_file.mrc
            and current directory is /home/username/documents
            this will return /test/import_file.mrc
        """
        return self.inputVolume.get().getFileName()

    def getVolumeAbsolutePath(self):
        """
        This method returns the absolute path for the volume file.
        Example: /home/username/documents/test/import_file.mrc
        """
        return os.path.abspath(self.getVolumeRelativePath())

    def getVolumeName(self):
        """
        This method returns the full name of the volume file.
        Example: import_file.mrc
        """
        return os.path.basename(self.getVolumeRelativePath())
    
    def getCleanVolumeName(self):
        """
        This method returns the full name without the 'import_' prefix.
        Example:
            if filename is import_file.mrc
            this will return file.mrc
        """
        return self.getVolumeName().replace('import_', '')
