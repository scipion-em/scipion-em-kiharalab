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

# Pyworkflow imports
from pyworkflow.protocol import params
from pwem.protocols import EMProtocol
from pwem.objects import SetOfAtomStructs, AtomStruct, Volume
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
        # -------------------------------------- Common params --------------------------------------
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('executionType', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_TYPE_EMAP2SEC,
                        choices=['Emap2sec', 'Emap2sec+'], label="Execution type: ",
                        help='Select the type of execution between Emap2sec and Emap2sec+.\n'
                        'Emap2sec+ can only be run on GPU, while Emap2sec runs on CPU.')
        form.addParam('cleanTmps', params.BooleanParam, default='True', label='Clean temporary files: ', expertLevel=params.LEVEL_ADVANCED,
                        help='Clean temporary files after finishing the execution.\nThis is useful to reduce unnecessary disk usage.')

        # -------------------------------------- Emap2sec params --------------------------------------
        form.addParam('inputVolumeEmap2sec', params.PointerParam, condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC,
                        pointerClass='Volume,SetOfVolumes', allowsNull=False,
                        label="Input volume/s: ",
                        help='Select the electron map/s to be processed.')
        trimmapGroup = form.addGroup('Trimmap generation', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC)
        trimmapGroup.addParam('emap2secContour', params.FloatParam, label='Contour: ', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC,
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
                       
        form.addParam('proteinId', params.StringParam, label='Protein id:', condition='(executionType==%d and type(inputVolumeEmap2sec) == Volume)' % EMAP2SEC_TYPE_EMAP2SEC,
                        expertLevel=params.LEVEL_ADVANCED, help='Optional.\nUnique protein identifier. Either EMID or SCOPe ID can be used.'
                            '\nFor example, protein EMD-1733 in EMDB has the identifier 1733.')
        
        form.addParam('predict', params.BooleanParam, default='True', label='Show Secondary Structures predicted data: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC, expertLevel=params.LEVEL_ADVANCED,
                        help='Show predicted data (Predicted secondary structures).')
        
        # -------------------------------------- Emap2sec+ params --------------------------------------
        form.addParam('mode', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SECPLUS_MODE_DETECT_STRUCTS, label='Mode: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED,
                        choices=['Detect structures', 'Detect-evaluate structures', 'Detect DNA/RNA & protein'],
                        help='Set this option to define the execution mode. The options are:\n\n'
                            '- Detect structures: Detect structures for EM Map\n\n'
                            '- Detect-evaluate structures: Detect and evaluate structures for EM map with pdb structure\n\n'
                            '- Detect DNA/RNA & protein: Detect DNA/RNA and protein for experimental maps. Only available with 4 fold models')
        form.addParam('inputVolumeEmap2secPlusPredict', params.PointerParam, condition='executionType==%d and mode !=%d' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS),
                        pointerClass='Volume,SetOfVolumes', allowsNull=False,
                        label="Input volume/s: ",
                        help='Select the electron map/s to be processed.')
        form.addParam('inputVolumeEmap2secPlusEvaluate', params.PointerParam, condition='executionType==%d and mode==%d' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS),
                        pointerClass='Volume', allowsNull=False,
                        label="Input volume: ",
                        help='Select the electron map to be processed.')
        form.addParam('mapType', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SECPLUS_TYPE_EXPERIMENTAL, label='Map type: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED,
                        choices=['Simulated map at 6Å', 'Simulated map at 10Å', 'Simulated map at 6-10Å', 'Experimental map'],
                        help='Set this option to define the type of input map.')
        form.addParam('gpuId', params.IntParam, default='0', label='GPU id: ', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS,
                        help='Select the GPU id where the process will run on.')
        form.addParam('emap2secplusContour', params.FloatParam, default='0.0', label='Contour: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, help='Contour level for real map.\n'
                            'You can use the author recommended contour level, which will be used by a specific model,'
                            ' or 0.0 to indicate that no contour is defined, which will use a general purpose model.')
        form.addParam('inputStruct', params.PointerParam,
                        condition='(executionType==%d and mode==%d)' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS),
                        pointerClass='AtomStruct', allowsNull=False, label="Input atom struct: ", help='Select the atom struct to evaluate the model with.')
        form.addParam('classes', params.IntParam, default='4', label='Number of classes: ', condition='executionType==%d and mode!=%d' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_DNA),
                        expertLevel=params.LEVEL_ADVANCED, help='Select number of classes to differentiate between.\n'
                            'Not available for Detect DNA/RNA & protein mode.')
        form.addParam('fold', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SECPLUS_FOLD3, label='Fold model: ',
                        condition='(executionType==%d and mode!=%d and mapType==%d)' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_DNA, EMAP2SECPLUS_TYPE_EXPERIMENTAL),
                        expertLevel=params.LEVEL_ADVANCED, choices=['Fold 1', 'Fold 2', 'Fold 3', 'Fold 4'],
                        help='Set this option to specify the fold model used for detecting the experimental map.\n'
                            'This param is not available for DNA/RNA & protein detection.')
        form.addParam('customModel', params.FolderParam, label='Custom model path: ', condition='executionType==%d and (fold==%d or mode==%d)' % (EMAP2SEC_TYPE_EMAP2SECPLUS, 3, EMAP2SECPLUS_MODE_DETECT_DNA),
                        expertLevel=params.LEVEL_ADVANCED,
                        help='Set this option to specify the path to a custom model to be used by Emap2sec+.\n'
                            'The model needs to have the same directory and file structure as the models included with this protocol.\n'
                            'This means that, for each file or folder that exists within the example model, a file or folder (same type of element) with the same name must exist.\n'
                            'You can download a sample model to check the folder structure from https://kiharalab.org/emsuites/emap2secplus_model/nocontour_best_model.tar.gz\n'
                            'Custom models can only be used with 4 fold networks.')
        form.addParam('getConfident', params.BooleanParam, default='True', label='Get confident results: ', expertLevel=params.LEVEL_ADVANCED, condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS,
                        help='Only accept as valid predictions the ones with a 90%+ probability.')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        """
        This method defines the functions that will be run during the execution of this protocol.
        """
        self._insertFunctionStep('mainExecutionStep')
        self._insertFunctionStep('createOutputStep')

    def mainExecutionStep(self):
        """
        This method collects the necessary arguments for the execution of this protocol and calls the protocol's run function.
        """
        # Defining which software will be run
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
            self.getEmap2secPlusArgs(),
            self.getEmap2secPlusMoveParams(),
            self.getFilesToRemove()
        ]

        # Running protocol
        if executionIsEmap2sec:
            Plugin.runEmap2sec(self, args=args, outDir=self.getOutputPath(), clean=self.cleanTmps.get())
        else:
            Plugin.runEmap2secPlus(self, args=args, clean=self.cleanTmps.get())

    def createOutputStep(self):
        """
        This method processes the output files generated by the protocol and imports them into Scipion objects.
        """
        # Checking whether input is one volume or a set of volumes to define output type
        isOneVolume = self.getInputType() == 'Volume'

        # Getting input files deppending on type
        inputData = self.getVolumeAbsolutePaths()[0] if isOneVolume else self.getVolumeAbsolutePaths()

        # Getting input volumes
        inputVolumes = self.inputVolumeEmap2sec.get() if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SEC else self.getEmap2secPlusInput()

        if isOneVolume:
            # Creating output AtomStruct, linking volume to it, and defining protocol output
            outputAtomStruct = AtomStruct(filename=self.getOutputFile(inputData))
            outputAtomStruct.setVolume(inputVolumes)
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
        This method warns about potentially problematic input values that may be used anyway.
        """
        return []
    
    def _validate(self):
        """
        This method validates the received params and checks that they all fullfill the requirements needed to run the protocol.
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
    
    def scapePath(self, path):
        """
        This function returns the given path with all the spaces in folder names scaped to avoid errors.
        """
        # os.path.baspath adds '\\' when finding a foldername with '\ ', so '\\\' needs to be replaced with ''
        # Then, '\' is inserted before every space again, to include now possible folders with spaces in the absolute path
        return path.replace('\\\ ', ' ').replace(' ', '\ ')
    
    def getVolumeRelativePaths(self):
        """
        This method returns a list with the volume paths relative to current directory.
        Example:
            if a file is in /home/username/documents/test/import_file.mrc
            and current directory is /home/username/documents
            this will return ['/test/import_file.mrc']
        """
        rawVolumeInput = self.inputVolumeEmap2sec.get() if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SEC else self.getEmap2secPlusInput()
        volumes = []
        try:
            # Trying to obtain each file from the volume list
            for volume in rawVolumeInput:
                # Adding '\' to folders with spaces to scape the spaces
                volumes.append(self.scapePath(volume.getFileName()))
        except:
            # If we get an exception, it means it si a single volume
            volumes = [self.scapePath(rawVolumeInput.getFileName())]
        return volumes

    def getVolumeAbsolutePaths(self):
        """
        This method returns a list with the absolute path for the volume files.
        Example: ['/home/username/documents/test/import_file.mrc']
        """
        volumes = []
        for volume in self.getVolumeRelativePaths():
            volumes.append(self.scapePath(os.path.abspath(volume)))
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

    def getInputType(self):
        """
        This method returns the type of input received by the protocol.
        """
        try:
            # Trying to obtain each file from the volume list
            rawVolumeInput = self.inputVolumeEmap2sec.get() if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SEC else self.getEmap2secPlusInput()
            for volume in rawVolumeInput:
                # If volumes are iterable, means it is a set
                return 'SetOfVolumes'
        except:
            # If it is not iterable, then it is a single volume
            return 'Volume'

    def getOutputPath(self):
        """
        This method returns the absolute path to the custom output directory.
        Spaces in the folder names are scaped to avoid errors.
        """
        # Defining base output path
        outputPath = self.scapePath(os.path.abspath(self._getExtraPath('results')))

        return outputPath

    def getOutputFile(self, inputFile):
        """
        This method returns the full output file with the absolute path given an input file.
        """
        # Generating full output file name for selected execution type
        filename = (
            (self.getProtocolFilePrefix(inputFile) + 'visual.pdb') if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SEC
            else self.getEmap2secPlusOutputFile()
        )
        return os.path.join(self.getOutputPath(), filename)
    
    def getFilesToRemove(self):
        """
        This method returns a list of all the temporary files to be removed if the user chose to do it.
        """
        args = []
        if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SEC:
            for file in self.getVolumeAbsolutePaths():
                protocolPrefix = self.getProtocolPrefix()
                filePrefix = self.getProtocolFilePrefix(file)
                args.append('data/{}trimmap'.format(filePrefix))
                args.append('data/{}dataset'.format(filePrefix))
                args.append('data/{}input.txt'.format(protocolPrefix))
                for i in range(1, 3):
                    args.append('results/{}outputP{}_{}dataset'.format(protocolPrefix, i, filePrefix))
        else:
            args = [os.path.join(self.getOutputPath(), self.getEmap2secPlusTypePath())]

        return args

    # -------------------------------- Emap2sec specific functions --------------------------------
    def getTrimmapArgs(self):
        """
        This method returns a list with the arguments neccessary for the trimmap generation for each volume file.
        """
        args = []
        for file in self.getVolumeAbsolutePaths():
            args.append('{} -c {} -sstep {} -vw {} {} > data/{}trimmap'\
            .format(file,
                self.emap2secContour.get(),
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
            proteinId = (' ' + self.proteinId.get()) if self.proteinId.get() and type(self.inputVolumeEmap2sec.get()) == Volume else ''
            args.append('{}trimmap {}dataset{}'.format(outputPefix, outputPefix, proteinId))
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
    
    # -------------------------------- Emap2sec+ specific functions --------------------------------
    def getEmap2secPlusInput(self):
        """
        This function returns the proper Emap2sec+ input deppening on the mode selected
        """
        return self.inputVolumeEmap2secPlusEvaluate.get() if self.mode.get() == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS else self.inputVolumeEmap2secPlusPredict.get()

    def getFoldModel(self):
        """
        This method returns the real fold value selected by the user.
        That is the value returned by the form + 1, because input param list starts by 1 but arrays start by 0.
        """
        return self.fold.get() + 1
    
    def getMode(self):
        """
        This method translates mode value selected by the user in the form into the actual param needed for Emap2sec+.
        """
        # Real Emap2sec+ mode values that do not match plugin form values
        EMAP2SECPLUS_MODE_DETECT_EXPERIMENTAL_FOLD4 = 2
        EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4 = 3

        # Getting form mode value
        realMode = self.mode.get()

        if realMode == EMAP2SECPLUS_MODE_DETECT_STRUCTS and self.getFoldModel() == 4:
            return EMAP2SECPLUS_MODE_DETECT_EXPERIMENTAL_FOLD4
        
        if realMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS and self.getFoldModel() == 4:
            return EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4
        
        if realMode == EMAP2SECPLUS_MODE_DETECT_DNA:
            return EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4

        return realMode
    
    def getStructRelativePath(self):
        """
        This method returns the AtomStruct path relative to current directory.
        Example:
            if a file is in /home/username/documents/test/my_atom_struct_file.pdb
            and current directory is /home/username/documents
            this will return '/test/my_atom_struct_file.pdb'
        """
        return self.scapePath(self.inputStruct.get().getFileName())
    
    def getStructAbsolutePath(self):
        """
        This method returns the absolute path for the atom struc file.
        Example: '/home/username/documents/test/my_atom_struct_file.pdb'
        """
        return self.scapePath(os.path.abspath(self.getStructRelativePath()))
    
    def getCustomModel(self):
        """
        This function returns the string for the custom model path.
        """
        customModel = self.customModel.get()
        executionMode = self.getMode()
        return ((' -M=' + self.scapePath(customModel)) if 
            (customModel and executionMode == EMAP2SECPLUS_MODE_DETECT_STRUCTS and executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS) 
            else '')
    
    def getEmap2secPlusArgs(self):
        """
        This method returns the arguments necessary to execute Emap2sec+.
        """
        params = []
        # Creating a param string for each input file
        for inputFile in self.getVolumeAbsolutePaths():
            executionMode = self.getMode()
            param = '-F={} --mode={} --type={} --contour={} --gpu={} --no_compilation --output_folder={}{}'\
                .format(inputFile, executionMode, self.mapType.get(), self.emap2secplusContour.get(),
                        self.gpuId.get(), self.getOutputPath(), self.getCustomModel())

            # If mode is not Detect DNA/RNA & protein, add class
            if executionMode != EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4:
                param = '{} --class={}'.format(param, self.classes.get())

            # If selected mode is not a fold4 mode and map type is experimental, add fold selection
            if (self.mapType.get() == EMAP2SECPLUS_TYPE_EXPERIMENTAL and 
                (executionMode == EMAP2SECPLUS_MODE_DETECT_STRUCTS or executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS)):
                param = '{} --fold={}'.format(param, self.getFoldModel())

            # If execution mode is evaluate, add input atom struct
            if executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS or executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4:
                param = '{} -P={}'.format(param, self.getStructAbsolutePath())
            params.append(param)

        return params
    
    def getEmap2secPlusTypePath(self):
        """
        This method returns the first folder for the output path for Emap2sec+, matching the map type.
        """
        return ('SIMU6' if self.mapType.get() == EMAP2SECPLUS_TYPE_SIMUL6A else
            ('SIMU10' if self.mapType.get() == EMAP2SECPLUS_TYPE_SIMUL10A else
            ('SIMU_MIX' if self.mapType.get() == EMAP2SECPLUS_TYPE_SIMUL6_10A else 'REAL'))
        )
    
    def getEmap2secPlusDefaultOutputPath(self):
        """
        This method returns the default output file path for Emap2sec+.
        """
        # Checking if selected mode is DNA/RNA & protein prediction (causes path format changes)
        modeIsDNA = self.getMode() == EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4

        # Generating full path
        foldPath = 'Fold{}_Model_Result'.format(self.getFoldModel())
        filePath = os.path.splitext(self.getVolumeNames()[0])[0]

        # Returning full path
        return os.path.join(self.getOutputPath(),
            'Binary' if modeIsDNA else '',
            self.getEmap2secPlusTypePath(),
            foldPath if not modeIsDNA else '',
            filePath,
            'Phase2' if not modeIsDNA else 'Final')
    
    def getEmap2secPlusOutputFile(self, clean=True):
        """
        This method returns the default output file name for Emap2sec+.
        """
        volumeName = os.path.splitext((self.getCleanVolumeNames() if clean else self.getVolumeNames())[0])[0]
        return '{}{}_pred{}.pdb'.format(volumeName,
            ('Final' if self.getMode() == EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4 else 'Phase2'),
            ('C' if self.getConfident.get() else ''))
    
    def getEmap2secPlusMoveParams(self):
        """
        This method returns the output file move command params for Emap2sec+.
        """
        return [
            os.path.join(self.getEmap2secPlusDefaultOutputPath(), os.path.basename(self.getEmap2secPlusOutputFile(clean=False))),
            os.path.join(self.getOutputPath(), self.getEmap2secPlusOutputFile())
        ]