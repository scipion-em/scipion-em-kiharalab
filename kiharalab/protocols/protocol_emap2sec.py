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
import os, subprocess

# Pyworkflow imports
from pyworkflow.protocol import params
from pyworkflow.utils import Message
from pwem.protocols import EMProtocol
from pwem.objects import AtomStruct
from pwem.emlib.image import ImageHandler

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
    _possibleOutputs = {'outputAtomStruct': AtomStruct}

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
        form.addParam('inputVolume', params.PointerParam, pointerClass='Volume', allowsNull=False,
                        label="Input volume: ", help='Select the electron map to be processed.')
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
                       
        form.addParam('proteinId', params.StringParam, label='Protein id:', condition='executionType==%d' % EMAP2SEC_TYPE_EMAP2SEC,
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
                            '- Detect DNA/RNA & protein: Detect DNA/RNA and protein for experimental maps. Only available with 4 fold models\n\n'
                            'For detect-evaluate mode, evaluation results will show up in summary box.')
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
        self._insertFunctionStep('convertInputStep')
        self._insertFunctionStep('mainExecutionStep')
        self._insertFunctionStep('createOutputStep')
    
    def convertInputStep(self):
        """
        This method converts the received input volume to a mrc file that can be used by both Emap2sec and Emap2sec+.
        """
        fileExtension = os.path.splitext(self.getVolumeAbsolutePath())[1]
        # If file extension is not map or mrc (therefore not directly supported), convert to mrc format
        if fileExtension != '.mrc' and fileExtension != '.map':
            img = ImageHandler()
            img.convert(self.getVolumeAbsolutePath(), self.getConvertedVolumeAbsolutePath())

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
            self.runEmap2sec(args, outDir=self.getOutputPath(), clean=self.cleanTmps.get())
        else:
            self.runEmap2secPlus(args, clean=self.cleanTmps.get())

    def createOutputStep(self):
        """
        This method processes the output files generated by the protocol and imports them into Scipion objects.
        """
        # Creating output AtomStruct and linking volume to it
        outputAtomStruct = AtomStruct(filename=self.getOutputFile(self.getVolumeAbsolutePath()))
        outputAtomStruct.setVolume(self.inputVolume.get())

        # Defining protocol output
        self._defineOutputs(outputAtomStruct=outputAtomStruct)
    
    # --------------------------- EXECUTION functions -----------------------------------
    # ---------------------------------- Emap2sec ----------------------------------
    def runEmap2sec(self, args, outDir=None, clean=True):
        """
        Run Emap2sec script from a given protocol.
        """
        # Building commands before actual protocol execution
        # Enviroment activation command. Needed to execute before every other standalone command.
        envActivationCommand = "{} {}".format(Plugin.getCondaActivationCmd(), Plugin.getProtocolActivationCommand('emap2sec'))
        
        # If custom output directory is specified, create it if it does not exist
        if outDir:
            self.runJob("mkdir -p", outDir, cwd=Plugin._emap2secRepo)

        # Command to move to Emap2sec's repo's root directory.
        # Needed to be executed before the actual workflow commands
        moveToRepoCommand = "cd"
        self.runJob(moveToRepoCommand, Plugin._emap2secRepo, cwd=Plugin._emap2secRepo)

        # Trimapp generation command
        trimappCommand = "data_generate/map2train"
        self.runJob(trimappCommand, args[0], cwd=Plugin._emap2secRepo)

        # Dataset generation command
        datasetCommand = "{} && python data_generate/dataset.py".format(envActivationCommand)
        self.runJob(datasetCommand, args[1], cwd=Plugin._emap2secRepo)

        # Input file for Emap2sec.py
        self.runJob("echo", args[2], cwd=Plugin._emap2secRepo)

        # Emap2sec execution command
        emap2secCommand = "{} && python emap2sec/Emap2sec.py".format(envActivationCommand)
        self.runJob(emap2secCommand, args[3], cwd=Plugin._emap2secRepo)
        
        # Secondary structures visualization command
        visualCommand = "Visual/Visual.pl"
        self.runJob(visualCommand, args[4], cwd=Plugin._emap2secRepo)

        # Remove temporary files
        if clean:
            for tmp_file in args[5]:
                self.runJob("rm -rf", tmp_file, cwd=Plugin._emap2secRepo)
    
    # ---------------------------------- Emap2sec+ ----------------------------------
    def runEmap2secPlus(self, args, clean=True):
        """
        Run Emap2secPlus script from a given protocol.
        """
        # Building commands before actual protocol execution
        # Enviroment activation command. Needed to execute befor every other standalone command.
        envActivationCommand = "{} {}".format(Plugin.getCondaActivationCmd(), Plugin.getProtocolActivationCommand('emap2sec', 'emap2secPlus'))
        
        # Command to move to Emap2sec+'s repo's root directory.
        # Needed to be executed once before the actual workflow commands
        moveToRepoCommand = "cd"
        self.runJob(moveToRepoCommand, Plugin._emap2secplusRepo, cwd=Plugin._emap2secplusRepo)

        # Emap2sec+ execution command
        runCommand = "{} && python3 main.py".format(envActivationCommand)
        self.runJob(runCommand, args[0], cwd=Plugin._emap2secplusRepo)

        # Output file/s relocation
        self.runJob("mv", args[1][0] + ' ' + args[1][1], cwd=Plugin._emap2secplusRepo)
        if len(args[1]) == 4:
            self.runJob("mv", args[1][2] + ' ' + args[1][3], cwd=Plugin._emap2secplusRepo)

        # Remove temporary files
        if clean:
            for tmp_file in args[2]:
                self.runJob("rm -rf", tmp_file, cwd=Plugin._emap2secplusRepo)
    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """
        This method usually returns a summary of the text provided by '_methods'.
        """
        summary = []

        # In evaluation mode in Emap2sec+, displays the model results
        if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SECPLUS and self.mode.get() == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS:
            metricsFilename = os.path.join(self.getOutputPath(), self.getEmap2secPlusMetricsFile())
            try:
                metricsFile = open(metricsFilename, 'r')
                summary.append('Model evaluation results:')
                for line in metricsFile:
                    summary.append(line)
                metricsFile.close()
            except:
                summary.append('Metric results not ready yet.')
        
        return summary

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
        if self.executionType.get() == EMAP2SEC_TYPE_EMAP2SECPLUS:
            # Detecting if host machine has Nvidia drivers installed
            try:
                # If no Nvidia drivers are present, the following command will reuturn an error
                subprocess.check_output(['nvidia-smi'])
            except Exception as e:
                errors.append('No Nvidia drivers detected on this machine.\n'
                    'Emap2sec+ needs an Nvidia GPU to run.')

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
    
    def getVolumeRelativePath(self):
        """
        This method returns the volume path relative to current directory.
        Path is scaped to support spaces.
        Example:
            if a file is in /home/username/documents/test/import_file.mrc
            and current directory is /home/username/documents
            this will return '/test/import_file.mrc'
        """
        return self.scapePath(self.inputVolume.get().getFileName())

    def getVolumeAbsolutePath(self):
        """
        This method returns the absolute path for the volume file.
        Path is scaped to support spaces.
        Example: '/home/username/documents/test/import_file.mrc'
        """
        return self.scapePath(os.path.abspath(self.getVolumeRelativePath()))
    
    def getVolumeName(self, filename):
        """
        This method returns the full name of the given volume files.
        Example: import_file.mrc
        """
        return os.path.basename(filename)

    def getCleanVolumeName(self, filename):
        """
        This method returns the full name of the given volume file without the 'import_' prefix.
        Example:
            if filename is 'import_file.mrc'
            this will return 'file.mrc'
        """
        return self.getVolumeName(filename).replace('import_', '')

    def getConvertedVolumeRelativePath(self):
        """
        This method returns the converted volume path relative to current directory if the input volume file is not directly supported.
        Path is scaped to support spaces.
        Example:
            if a file is in /home/username/documents/test/import_file.mrc
            and current directory is /home/username/documents
            this will return '/test/import_file.mrc'
        """
        fileExtension = os.path.splitext(self.getVolumeAbsolutePath())[1]
        if fileExtension != '.mrc' and fileExtension != '.map':
            return self.scapePath(self._getTmpPath(self.getVolumeName(os.path.splitext(self.getVolumeAbsolutePath())[0] + '.mrc')))
        else:
            return self.getVolumeRelativePath()

    def getConvertedVolumeAbsolutePath(self):
        """
        This method returns the absolute path for the converted volume file.
        Path is scaped to support spaces.
        Example: '/home/username/documents/test/import_file.mrc'
        """
        return self.scapePath(os.path.abspath(self.getConvertedVolumeRelativePath()))

    def getOutputPath(self):
        """
        This method returns the absolute path to the custom output directory.
        Spaces in the folder names are scaped to avoid errors.
        """
        return self.scapePath(os.path.abspath(self._getExtraPath('results')))

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
            protocolPrefix = self.getProtocolPrefix()
            filePrefix = self.getProtocolFilePrefix(self.getVolumeAbsolutePath())
            args.append('data/{}trimmap'.format(filePrefix)) # Trimmap file
            args.append('data/{}dataset'.format(filePrefix)) # Dataset file
            args.append('data/{}input.txt'.format(protocolPrefix)) # Input location file
            for i in range(1, 3):
                args.append('results/{}outputP{}_{}dataset'.format(protocolPrefix, i, filePrefix)) # Result prediction files
        else:
            args = [os.path.join(self.getOutputPath(), self.getEmap2secPlusTypePath())] # Whole result folder (key result file is moved out before deletion)
        
        fileExtension = os.path.splitext(self.getVolumeAbsolutePath())[1] # If file extension is not directly supported, add temporary converted input file
        if fileExtension != '.mrc' and fileExtension != '.map':
            args.append(self.getConvertedVolumeAbsolutePath())

        return args

    # -------------------------------- Emap2sec specific functions --------------------------------
    def getTrimmapArgs(self):
        """
        This method returns a list with the arguments neccessary for the trimmap generation for the volume.
        """
        file = self.getConvertedVolumeAbsolutePath()
        return '{} -c {} -sstep {} -vw {} {} > data/{}trimmap'\
        .format(file,
            self.emap2secContour.get(),
            self.sstep.get(),
            self.vw.get(),
            '-gnorm' if self.norm.get() == EMAP2SEC_NORM_GLOBAL else '-Inorm',
            self.getProtocolFilePrefix(file))
    
    def getDatasetArgs(self):
        """
        This method returns the arguments neccessary for the dataset generation.
        """
        outputPefix = 'data/{}'.format(self.getProtocolFilePrefix(self.getVolumeAbsolutePath()))
        proteinId = (' ' + self.proteinId.get()) if self.proteinId.get() else ''
        return '{}trimmap {}dataset{}'.format(outputPefix, outputPefix, proteinId)
    
    def getInputLocationFileArgs(self):
        """
        This method returns the arguments neccessary for input location file generation
        used for Emap2sec.py.
        """
        return '\'data/{}dataset\' > data/{}input.txt'\
            .format(self.getProtocolFilePrefix(self.getVolumeAbsolutePath()), self.getProtocolPrefix())
    
    def getEmap2secArgs(self):
        """
        This method returns the arguments neccessary for the Emap2sec.py's execution.
        """
        return 'data/{}input.txt --prefix results/{}'.format(self.getProtocolPrefix(), self.getProtocolPrefix())

    def getVisualArgs(self):
        """
        This method returns the arguments neccessary for the Secondary Structure visualization.
        """
        file = self.getVolumeAbsolutePath()
        return 'data/{}trimmap results/{}outputP2_{}dataset -p > {}'\
                .format(self.getProtocolFilePrefix(file),
                    self.getProtocolPrefix(),
                    self.getProtocolFilePrefix(file),
                    self.getOutputFile(file))
    
    # -------------------------------- Emap2sec+ specific functions --------------------------------
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
        Path is scaped to support spaces.
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
        executionMode = self.getMode()

        # Initial param string
        param = '-F={} --mode={} --type={} --contour={} --gpu={} --no_compilation --output_folder={}{}'\
            .format(self.getConvertedVolumeAbsolutePath(), executionMode, self.mapType.get(), self.emap2secplusContour.get(),
                    self.gpuId.get(), self.getOutputPath(), self.getCustomModel())

        # If mode is not Detect DNA/RNA & protein, add class
        if executionMode != EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4:
            param += ' --class={}'.format(self.classes.get())

        # If selected mode is not a fold4 mode and map type is experimental, add fold selection
        if (self.mapType.get() == EMAP2SECPLUS_TYPE_EXPERIMENTAL and 
            (executionMode == EMAP2SECPLUS_MODE_DETECT_STRUCTS or executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS)):
            param += ' --fold={}'.format(self.getFoldModel())

        # If execution mode is evaluate, add input atom struct
        if executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS or executionMode == EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4:
            param += ' -P={}'.format(self.getStructAbsolutePath())

        return param
    
    def getEmap2secPlusTypePath(self):
        """
        This method returns the first folder for the output path for Emap2sec+, matching the map type.
        """
        return ('SIMU6' if self.mapType.get() == EMAP2SECPLUS_TYPE_SIMUL6A else
            ('SIMU10' if self.mapType.get() == EMAP2SECPLUS_TYPE_SIMUL10A else
            ('SIMU_MIX' if self.mapType.get() == EMAP2SECPLUS_TYPE_SIMUL6_10A else 'REAL'))
        )
    
    def getEmap2secPlusDefaultOutputPath(self, base=False):
        """
        This method returns the default output file path for Emap2sec+.
        """
        # Checking if selected mode is DNA/RNA & protein prediction (causes path format changes)
        modeIsDNA = self.getMode() == EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4

        # Generating full path
        foldPath = 'Fold{}_Model_Result'.format(self.getFoldModel())
        filePath = os.path.splitext(self.getVolumeName(self.getVolumeAbsolutePath()))[0]
        basePath = os.path.join(self.getOutputPath(),
                'Binary' if modeIsDNA else '',
                self.getEmap2secPlusTypePath(),
                foldPath if not modeIsDNA else '',
                filePath
            )

        return basePath if base else os.path.join(basePath, 'Phase2' if not modeIsDNA else 'Final')
    
    def getEmap2secPlusOutputFile(self, clean=True):
        """
        This method returns the default output file name for Emap2sec+.
        """
        inputFile = self.getVolumeAbsolutePath()
        volumeName = os.path.splitext(self.getCleanVolumeName(inputFile) if clean else self.getVolumeName(inputFile))[0]
        return '{}{}_pred{}.pdb'.format(volumeName,
                ('Final' if self.getMode() == EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4 else 'Phase2'),
                ('C' if self.getConfident.get() else '')
            )
    
    def getEmap2secPlusMetricsFile(self, clean=True):
        """
        This method returns the default metric report file name for Emap2sec+.
        """
        inputFile = self.getVolumeAbsolutePath()
        volumeName = os.path.splitext(self.getCleanVolumeName(inputFile) if clean else self.getVolumeName(inputFile))[0]
        return '{}Phase2_report.txt'.format(volumeName)
    
    def getEmap2secPlusMoveParams(self):
        """
        This method returns the output file move command params for Emap2sec+.
        """
        params = [
            os.path.join(self.getEmap2secPlusDefaultOutputPath(), os.path.basename(self.getEmap2secPlusOutputFile(clean=False))),
            os.path.join(self.getOutputPath(), self.getEmap2secPlusOutputFile())
        ]

        # If evaluation mode, also move metrics report file
        if self.mode.get() == EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS:
            params.append(os.path.join(self.getEmap2secPlusDefaultOutputPath(base=True), self.getEmap2secPlusMetricsFile(clean=False)))
            params.append(os.path.join(self.getOutputPath(), self.getEmap2secPlusMetricsFile()))

        return params