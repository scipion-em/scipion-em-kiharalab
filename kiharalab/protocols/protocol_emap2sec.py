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
from pwem.objects import SetOfAtomStructs, AtomStruct, SetOfVolumes, Volume
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
                        help='Select the electron map/s to be processed.')
        form.addParam('executionType', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SEC_TYPE_EMAP2SEC,
                        choices=['Emap2sec', 'Emap2sec+'], label="Execution type: ",
                        help='Select the type of execution between Emap2sec and Emap2sec+.\n'
                        'Emap2sec+ can only be run on GPU, while Emap2sec runs on CPU.')
        form.addParam('cleanTmps', params.BooleanParam, default='True', label='Clean temporary files: ', expertLevel=params.LEVEL_ADVANCED,
                        help='Clean temporary files after finishing the execution.\nThis is useful to reduce unnecessary disk usage.')

        # -------------------------------------- Emap2sec params --------------------------------------
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
                       
        form.addParam('proteinId', params.StringParam, label='Protein id:', condition='(executionType==%d and type(inputVolume) == Volume)' % EMAP2SEC_TYPE_EMAP2SEC,
                        expertLevel=params.LEVEL_ADVANCED, help='Optional.\nUnique protein identifier. Either EMID or SCOPe ID can be used.'
                            '\nFor example, protein EMD-1733 in EMDB has the identifier 1733.')
        
        form.addParam('predict', params.BooleanParam, default='True', label='Show Secondary Structures predicted data: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC, expertLevel=params.LEVEL_ADVANCED,
                        help='Show predicted data (Predicted secondary structures).')
        
        # -------------------------------------- Emap2sec+ params --------------------------------------
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
        form.addParam('mode', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SECPLUS_MODE_DETECT_STRUCTS, label='Mode: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED,
                        choices=['Detect structures', 'Detect-evaluate structures', 'Detect structures fold 4', 'Detect-evaluate structures fold 4', 'Detect DNA/RNA & protein fold 4'],
                        help='Set this option to define the execution mode. The options are:\n\n'
                            '- Detect structures: Detect structures for EM Map\n\n'
                            '- Detect-evaluate structures: Detect and evaluate structures for EM map with pdb structure\n\n'
                            '- Detect structures fold 4: Detect structure for experimental maps with 4 fold models\n\n'
                            '- Detect-evaluate structures fold 4: Detect and evaluate structure for experimental maps with 4 fold models\n\n'
                            '- Detect DNA/RNA & protein fold 4: Detect DNA/RNA and protein for experimental maps with 4 fold models\n\n'
                            'Setting 4 fold options will make the backend program call 4 fold networks and aggregate the final detection probabilities by majority vote.')
        form.addParam('inputStruct', params.PointerParam,
                        condition='(executionType==%d and (mode==%d or mode==%d))' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4),
                        pointerClass='AtomStruct', allowsNull=False,
                        label="Input atom struct: ",
                        help='Select the atom struct to evaluate the model with.')
        form.addParam('resize', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SECPLUS_RESIZE_NUMBA, label='Map resize: ',
                        condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS, expertLevel=params.LEVEL_ADVANCED, choices=['Numba', 'Scipy'],
                        help='Set this option to define the python package used to resize the maps. The options are:\n\n'
                            '- Numba: Optimized, but some map sizes are not supported.\n'
                            '- Scipy: Relatively slow but supports almost all maps.\n')
        form.addParam('classes', params.IntParam, default='4', label='Number of classes: ', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS,
                        expertLevel=params.LEVEL_ADVANCED, help='Select number of classes to differentiate between.')
        form.addParam('fold', params.EnumParam, display=params.EnumParam.DISPLAY_COMBO, default=EMAP2SECPLUS_FOLD3, label='Fold model: ',
                        condition='(executionType==%d and (mode==%d or mode==%d))' % (EMAP2SEC_TYPE_EMAP2SECPLUS, EMAP2SECPLUS_MODE_DETECT_STRUCTS, EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS),
                        expertLevel=params.LEVEL_ADVANCED, choices=['Fold 1', 'Fold 2', 'Fold 3', 'Fold 4'],
                        help='Set this option to specify the fold model used for detecting the experimental map.')
        form.addParam('customModel', params.FolderParam, label='Custom model path: ', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SECPLUS,
                        expertLevel=params.LEVEL_ADVANCED,
                        help='Set this option to specify the path to a custom model to be used by Emap2sec+.\n'
                            'The model needs to have the same directory and file structure as the models included with this protocol.\n'
                            'This means that, for each file or folder that exists within the example model, a file or folder (same type of element) with the same name must exist.\n'
                            'You can download a sample model to check the folder structure from https://kiharalab.org/emsuites/emap2secplus_model/nocontour_best_model.tar.gz')

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
            []
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
        if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SECPLUS: # TMP, Need to get output structure
            return
        
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
        This method warns about potentially problematic input values that may be used anyway.
        """
        return []
    
    def _validate(self):
        """
        This method validates the received params and checks that they all fullfill the requirements needed to run the protocol.
        """
        errors = []
        # If execution type is Emap2sec+ in evaluation mode, and input is a set of volumes, show error
        if (self.executionType.get() == EMAP2SEC_TYPE_EMAP2SECPLUS and type(self.inputVolume.get()) == SetOfVolumes and
            (self.mode.get() == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS or self.mode.get() == EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4)):
            errors.append('Cannot use evaluation mode for a set of volumes as input, because evaluation mode '
                            'is only designed to test the result pdb file obtained from an input volume against a reference pdb file.\n'
                            'If you want to use evaluation mode, use a single volume as input.')
        return errors

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
        rawVolumeInput = self.inputVolume.get()
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
            for volume in self.inputVolume.get():
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
        return self.scapePath(os.path.abspath(self._getExtraPath('results')))

    def getOutputFile(self, inputFile): # EMAP2SEC SPECIFIC? CHECK WHEN EMAP2SEC+ COMPLETED
        """
        This method returns the full output file with the absolute path given an input file.
        """
        return os.path.join(self.getOutputPath(), self.getProtocolFilePrefix(inputFile)) + 'visual.pdb'

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
            proteinId = (' ' + self.proteinId.get()) if self.proteinId.get() and type(self.inputVolume.get()) == Volume else ''
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
    
    # -------------------------------- Emap2sec+ specific functions --------------------------------
    def getFoldModel(self):
        """
        This method returns the real fold value selected by the user.
        That is the value returned by the form + 1, because input param list starts by 1 but arrays start by 0.
        """
        return self.fold.get() + 1
    
    def getContourLevel(self): # TEST IF NECESSARY, WITH 0 AND 0.0 THE RESULT MUST BE THE SAME
        """
        This function returns the correct contour level, which will be the input contour level if it is different from 0.0.
        If the contour level is 0.0, the resulting level gets converted into an integer.
        """
        contour = self.emap2secplusContour.get()
        return contour if contour != 0.0 else 0
    
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
        return (' -M=' + self.scapePath(customModel)) if customModel else ''
    
    def getEmap2secPlusArgs(self):
        """
        This method returns the arguments necessary to execute Emap2sec+.
        """
        params = []
        # Creating a param string for each input file
        for inputFile in self.getVolumeAbsolutePaths():
            executionMode = self.mode.get()
            param = '-F={} --mode={} --type={} --resize={} --contour={} --gpu={} --class={} --no_compilation --output_folder={}{}'\
                .format(inputFile, executionMode, self.mapType.get(), self.resize.get(), self.getContourLevel(),
                        self.gpuId.get(), self.classes.get(), self.getOutputPath(), self.getCustomModel())
            
            # If selected mode is not a fold4 mode, add fold selection
            if executionMode == 0 or executionMode == 1:
                param = '{} --fold={}'.format(param, self.getFoldModel())

            # If execution mode is evaluate, add input atom struct
            if executionMode == 1 or executionMode == 3:
                param = '{} -P={}'.format(param, self.getStructAbsolutePath())
            params.append(param)

        return params