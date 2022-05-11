# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors: Martín Salinas Antón (ssalinasmartin@gmail.com)
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
# Common imports
import os
from re import A

# Pyworkflow imports
from pyworkflow.protocol import params
from pwem.protocols import EMProtocol
from pwem.objects import SetOfAtomStructs, AtomStruct
from pyworkflow.utils import Message

# Kiharalab imports
from kiharalab import Plugin
from kiharalab.constants import *

class ProtEmap2sec(EMProtocol):
    ("Emap2sec is a computational tool using deep learning that can accurately identify protein secondary structures,"
    " alpha helices, beta sheets, others (coils/turns), in cryo-Electron Microscopy (EM) maps of medium to low resolution.\n"
    "Emap2sec+ also covers DNA/RNA.\n"
    "Original software can be found in https://github.com/kiharalab/Emap2sec and https://github.com/kiharalab/Emap2secPlus\n\n"
    "Output files can be visualized outside scipion with pymol, running 'pymol <output_pdb_file>' once pymol is installed.\n"
    "Pymol can be installed from https://pymol.org/2/ or an open source version can be found in https://github.com/schrodinger/pymol-open-source\n")
    _label = 'Emap2sec'
    _possibleOutputs = {'outputAtomStruct': AtomStruct, 'outputAtomStructs': SetOfAtomStructs}

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """
        Defines Emap2sec's input params.
        """
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputVolume', params.PointerParam,
                      pointerClass='Volume,SetOfVolumes', allowsNull=False,
                      label="Input volume/s: ",
                      help='Select the electron map/s to be processed')
        form.addParam('executionType', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_TYPE_EMAP2SEC,
                      choices=['Emap2sec', 'Emap2sec+'], label="Execution type: ",
                      help='Select the type of execution between Emap2sec and Emap2sec+.\n'
                      'Emap2sec+ can only be run on GPU, while Emap2sec runs on CPU.')
        form.addParam('cleanTmps', params.BooleanParam, default='True', label='Clean temporary files: ', expertLevel=params.LEVEL_ADVANCED,
                        help='Clean temporary files after finishing the execution.\nThis is useful to reduce unnecessary disk usage.')

        # -------------------------------------- Emap2sec params --------------------------------------
        trimmapGroup = form.addGroup('Trimmap generation', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC)
        trimmapGroup.addParam('contour', params.FloatParam, label='Contour: ',
                       help='The level of isosurface to generate density values for.\n'
                       'You can use a value of 0.0 for simulated maps and the author recommended contour level for experimental EM maps.')
        trimmapGroup.addParam('sstep', params.IntParam, default='4', label='Stride size: ', expertLevel=params.LEVEL_ADVANCED,
                       help='This option sets the stride size of the sliding cube used for input data generation.\n'
                       'We recommend using a value of 4 that slides the cube by 4Å in each direction.\n'
                       'Decreasing this value by 1 produces 8 times more data (increase by a factor of 2 in each direction)'
                       ' and thus slows the running time down by 8 times so please be mindful lowering this value.')
        trimmapGroup.addParam('vw', params.IntParam, default='5', label='Sliding cube dimensions: ', expertLevel=params.LEVEL_ADVANCED,
                       help='This option sets the dimensions of sliding cube used for input data generation.\n'
                       'The size of the cube is calculated as 2vw+1.\n'
                       'We recommend using a value of 5 for this option that generates input cube of size 11*11*11.\n'
                       'Please be mindful while increasing this option as it increases the portion of an EM map a single cube covers.'
                       ' Increasing this value also increases running time.')
        trimmapGroup.addParam('norm', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_NORM_GLOBAL, label='Normalization type: ',
                        expertLevel=params.LEVEL_ADVANCED, choices=['Global', 'Local'],
                        help='Set this option to normalize density values of the sliding cube, used for input data generation,'
                       ' by global or local maximum density value.')
        
        form.addParam('predict', params.BooleanParam, default='True', label='Show Secondary Structures predicted data: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC, expertLevel=params.LEVEL_ADVANCED,
                        help='Show predicted data (Predicted secondary structures)')
        
        # -------------------------------------- Emap2sec+ params --------------------------------------
        form.addParam('gpuId', params.IntParam, default='0', label='GPU id: ', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS,
                        help='Select the GPU id where the process will run on.')
        form.addParam('mode', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_MODE_DETECT_STRUCTS, label='Mode: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED,
                        choices=['Detect structures', 'Detect-evaluate structures', 'Detect structures fold 4', 'Detect-evaluate structures fold 4'],
                        help='Set this option to define the execution mode. The options are:\n\n'
                            '- Detect structures: Detect structures for EM Map\n\n'
                            '- Detect-evaluate structures: Detect and evaluate structures for EM map with pdb structure\n\n'
                            '- Detect structures fold 4: Detect structure for experimental maps with 4 fold models\n\n'
                            '- Detect-evaluate structures fold 4: Detect and evaluate structure for experimental maps with 4 fold models\n\n')
        form.addParam('resize', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_RESIZE_NUMBA, label='Map resize: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED, choices=['Numba', 'Scipy'],
                        help='Set this option to define the python package used to resize the maps. The options are:\n\n'
                            '- Numba: Optimized, but some map sizes are not supported.\n'
                            '- Scipy: Relatively slow but supports almost all maps.\n')
        form.addParam('classes', params.IntParam, default='4', label='Number of classes: ', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS,
                        expertLevel=params.LEVEL_ADVANCED, help='Select number of classes to differentiate between.')
        form.addParam('fold', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_FOLD4, label='Fold model: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED, choices=['Fold 1', 'Fold 2', 'Fold 3', 'Fold 4'],
                        help='Set this option to specify the fold model used for detecting the experimental map.')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('mainExecutionStep')
        self._insertFunctionStep('createOutputStep')

    def mainExecutionStep(self):
        executionIsEmap2sec = self.executionType.get() == EMAP2SEC_TYPE_EMAP2SEC

        # Defining arguments for each command to execute
        # args will be a list of strings, where each string are the arguments for a given command
        args = [
            self.getTrimmapArgs(),
            self.getDatasetArgs(),
            self.getInputLocationFileArgs(),
            self.getEmap2secArgs(),
            self.getVisualArgs(),
            self.getFilesToRemove()
        ] if executionIsEmap2sec else [

        ]

        # Running protocol
        if executionIsEmap2sec:
            Plugin.runEmap2sec(self, args=args, outDir=self.getOutputPath(), clean=self.cleanTmps.get())
        else:
            Plugin.runEmap2secPlus(self, args=args, outDir=None, clean=self.cleanTmps.get())

    def createOutputStep(self):
        # Checking whether input is one volume or a set of volumes to define output type
        isOneVolume = self.getInputType() == 'Volume'

        # Getting input files deppending on type
        inputData = self.getVolumeAbsolutePaths()[0] if isOneVolume else self.getVolumeAbsolutePaths()

        # Getting input volumes
        inputVolumes = self.inputVolume.get()

        if isOneVolume:
            # Creating output AtomStruct, linking volume to it, and defining protocol output
            outputAtomStruct = AtomStruct(filename=self.getOutputFile(inputData))
            outputAtomStruct.setVolume(self.inputVolume.get())
            self._defineOutputs(outputAtomStruct=outputAtomStruct)
        else:
            # Defining empty sets of AtomStruct
            outputAtomStructs = SetOfAtomStructs().create(self._getPath())

            # For each input file, one output files is produced
            for file, volume in zip(inputData, inputVolumes):
                auxAtomStruct = AtomStruct(filename=self.getOutputFile(file))

                # Linking volume file to AtomStruct and adding to set
                auxAtomStruct.setVolume(volume)
                outputAtomStructs.append(auxAtomStruct)
            
                # Defining protocol output
                self._defineOutputs(outputAtomStructs=outputAtomStructs)

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """
        This method returns a summary of the text provided by '_methods'.
        """
        return []

    def _methods(self):
        """
        This method returns a text intended to be copied and pasted in the paper section 'materials & methods'.
        """
        return []

    def _warnings(self):
        """
        This method warns about potentially problematic input values that will be used anyway.
        """
        return []

    # --------------------------- UTILS functions -----------------------------------
    def getProtocolPrefix(self):
        """
        This method returns the prefix that some output files generated by this protocol will have.
        Specifically, this prefix will be used by functions that will produce many outputs with a single call (like Emap2sec.py).
        This will be <protocolId>_
        """
        return '{}_'.format(self.getObjId())

    def getProtocolFilePrefix(self, filename):
        """
        This method returns the prefix that most output files generated by this protocol will have.
        This will be <protocolId>_<inputFileName>_
        """
        return '{}{}_'.format(self.getProtocolPrefix(), os.path.splitext(self.getCleanVolumeName(filename))[0])

    def getTrimmapArgs(self):
        """
        This method returns a list with the arguments neccessary for the trimmap generation for each volume file.
        """
        args = []
        for file in self.getVolumeAbsolutePaths():
            args.append('{} -c {} -sstep {} -vw {} {} > data/{}trimmap'\
            .format(file,
                self.contour.get(),
                self.sstep.get(),
                self.vw.get(),
                '-gnorm' if self.norm.get() == EMAP2SEC_NORM_GLOBAL else '-Inorm',
                self.getProtocolFilePrefix(file)))
        return args
    
    def getDatasetArgs(self):
        """
        This method returns the arguments neccessary for the dataset generation.
        """
        args = []
        for file in self.getVolumeAbsolutePaths():
            outputPefix = 'data/{}'.format(self.getProtocolFilePrefix(file))
            args.append('{}trimmap {}dataset'.format(outputPefix, outputPefix))
        return args
    
    def getInputLocationFileArgs(self):
        """
        This method returns the arguments neccessary for input location file generation,
        used for Emap2sec.py.
        """
        inputFileLocations = '\''
        for file in self.getVolumeAbsolutePaths():
            inputFileLocations = inputFileLocations + 'data/{}dataset\n'.format(self.getProtocolFilePrefix(file))
        inputFileLocations = inputFileLocations[:-1]
        return inputFileLocations + '\' > data/{}input.txt'.format(self.getProtocolPrefix())
    
    def getEmap2secArgs(self):
        """
        This method returns the arguments neccessary for the Emap2sec.py's execution.
        """
        return 'data/{}input.txt --prefix results/{}'.format(self.getProtocolPrefix(), self.getProtocolPrefix())

    def getVisualArgs(self):
        """
        This method returns the arguments neccessary for the Secondary Structure visualization.
        """
        args = []
        for file in self.getVolumeAbsolutePaths():
            args.append('data/{}trimmap results/{}outputP2_{}dataset -p > {}'\
                .format(self.getProtocolFilePrefix(file),
                    self.getProtocolPrefix(),
                    self.getProtocolFilePrefix(file),
                    self.getOutputFile(file)))
        return args
    
    def getFilesToRemove(self):
        """
        This method returns a list of all the temporary files to be removed if the user chose to do it.
        """
        args = []
        for file in self.getVolumeAbsolutePaths():
            protocolPrefix = self.getProtocolPrefix()
            filePrefix = self.getProtocolFilePrefix(file)
            args.append('data/{}trimmap'.format(filePrefix))
            args.append('data/{}dataset'.format(filePrefix))
            args.append('data/{}input.txt'.format(protocolPrefix))
            for i in range(1, 3):
                args.append('results/{}outputP{}_{}dataset'.format(protocolPrefix, i, filePrefix))
        return args

    def getVolumeRelativePaths(self):
        """
        This method returns a list with the volume paths relative to current directory.
        Example:
            if a file is in /home/username/documents/test/import_file.mrc
            and current directory is /home/username/documents
            this will return ['/test/import_file.mrc']
        """
        rawVolumeInput = self.inputVolume.get()
        volumes = []
        try:
            # Trying to obtain each file from the volume list
            for volume in rawVolumeInput:
                # Adding '\' to folders with spaces to scape the spaces
                volumes.append(volume.getFileName().replace(' ', '\ '))
        except:
            # If we get an exception, it means it si a single volume
            volumes = [rawVolumeInput.getFileName().replace(' ', '\ ')]
        return volumes

    def getVolumeAbsolutePaths(self):
        """
        This method returns a list with the absolute path for the volume files.
        Example: ['/home/username/documents/test/import_file.mrc']
        """
        # os.path.baspath adds '\\' when finding a foldername with '\ ', so '\\\' needs to be replaced with ''
        # Then, '\' is inserted before every space again, to include now possible folders with spaces in the absolute path
        volumes = []
        for volume in self.getVolumeRelativePaths():
            volumes.append(os.path.abspath(volume).replace('\\\ ', ' ').replace(' ', '\ '))
        return volumes
    
    def getVolumeName(self, filename):
        """
        This method returns the full name of the given volume files.
        Example: import_file.mrc
        """
        return os.path.basename(filename)

    def getVolumeNames(self):
        """
        This method returns a list with the full name of the volume files.
        Example: ['import_file.mrc']
        """
        volumes = []
        for volume in self.getVolumeRelativePaths():
            volumes.append(self.getVolumeName(volume))
        return volumes
    
    def getCleanVolumeName(self, filename):
        """
        This method returns the full name of the given volume file without the 'import_' prefix.
        Example:
            if filename is 'import_file.mrc'
            this will return 'file.mrc'
        """
        return self.getVolumeName(filename).replace('import_', '')

    def getCleanVolumeNames(self):
        """
        This method returns a list with the full name of every volume file without the 'import_' prefix.
        Example:
            if a filename is 'import_file.mrc'
            this will return ['file.mrc']
        """
        volumes = []
        for volume in self.getVolumeNames():
            volumes.append(self.getCleanVolumeName(volume))
        return volumes

    def getOutputPath(self):
        """
        This method returns the absolute path to the custom output directory.
        Spaces in the folder names are scaped to avoid errors.
        """
        rawPath = os.path.abspath(self._getExtraPath('results'))
        return rawPath.replace(' ', '\ ')

    def getOutputFile(self, inputFile):
        """
        This method returns the full output file with the absolute path given an input file.
        """
        return os.path.join(self.getOutputPath(), self.getProtocolFilePrefix(inputFile)) + 'visual.pdb'
    
    def getInputType(self):
        """
        This method returns the type of input received by the protocol.
        """
        try:
            # Trying to obtain each file from the volume list
            for volume in self.inputVolume.get():
                # If volumes are iterable, means it is a set
                return 'SetOfVolumes'
        except:
            # If it is not iterable, then it is a single volume
            return 'Volume'
    
    # -------------------------------- Emap2sec+ specific functions --------------------------------

    def getFoldModel(self):
        """
        This method returns the real fold value selected by the user.
        That is the value returned by the form + 1, because input param list starts by 1 but arrays start by 0.
        """
        return self.fold.get() + 1