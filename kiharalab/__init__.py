# **************************************************************************
# *
# * Authors:  Daniel Del Hoyo (ddelhoyo@cnb.csic.es)
# *
# * Biocomputing Unit, CNB-CSIC
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

import pwem
from .constants import *
import shutil, os

_version_ = '0.1'
_logo = "kiharalab_logo.png"
_references = ['genki2021DAQ']

class Plugin(pwem.Plugin):
    """
    Definition of class variables. For each protocol repo, three variables will be created.
    <protocolNameInUppercase>_WITH_VERSION will contain <protocolNameInUppercase>-<protocolVersion>. For example, "DAQ-1.0"
    _<protocolNameInLowercase>Home will contain the full path of the protocol, ending with a folder whose name will be <protocolNameInUppercase>_WITH_VERSION variable. For example: "~/Documents/scipion/software/em/DAQ-1.0"
    _<protocolNameInLowercase>Repo will be a folder inside _<protocolNameInLowercase>Home and its name will be <protocolNameInUppercase>. For example: "DAQ"
    """
    names = [name for name in PROTOCOL_NAME_LIST]
    for name in names:
        for protocolRepoName in PROTOCOL_LIST[name]:
            nameInLowercase = protocolRepoName.lower()
            nameInUppercase = protocolRepoName.upper()
            locals()[nameInUppercase + "_WITH_VERSION"] = nameInUppercase + '-' + globals()[nameInUppercase + "_REPO_DEFAULT_VERSION"]
            locals()["_" + nameInLowercase + "Home"] = os.path.join(pwem.Config.EM_ROOT, locals()[name.upper() + "_WITH_VERSION"])
            locals()["_" + nameInLowercase + "Repo"] = os.path.join(locals()["_" + nameInLowercase + "Home"], globals()[nameInUppercase])
        
        # Substituting each name with the same name in uppercase
        nameIndex = names.index(name)
        names[nameIndex] = name.upper()

    @classmethod
    def _defineVariables(cls):
        """
        Return and write a home and conda enviroment variable in the config file.
        Each protocol will have a variable called <protocolNameInUppercase>_HOME, and another called <protocolNameInUppercase>_ENV
        <protocolNameInUppercase>_HOME will contain the path to the protocol installation. For example: "~/Documents/scipion/software/em/DAQ-1.0"
        <protocolNameInUppercase>_ENV will contain the name of the conda enviroment for that protocol. For example: "DAQ-1.0"
        """
        for name in cls.names:
            protocolHomeAndEnv = name + '-' + globals()[name + "_DEFAULT_VERSION"]
            cls._defineEmVar(globals()[name + "_HOME"], protocolHomeAndEnv)
            cls._defineVar(name + "_ENV", protocolHomeAndEnv)

    @classmethod
    def defineBinaries(cls, env):
        """
        This function defines the binaries for each protocol.
        """
        for name in cls.names:
            nameInLowercase = name.lower()
            cls.addProtocolPackage(env,
                                    globals()[name],
                                    getattr(cls, "_" + nameInLowercase + "Home"),
                                    name,
                                    globals()[name + "_DEFAULT_VERSION"])

    @classmethod
    def addProtocolPackage(cls, env, protocolName, protocolHome, protocolVariableName, protocolVersion):
        """
        Define and execute commands for protocol installation.
        Every command has it's own checkpoint so if, for some reason, process is interrupted, only commands that were not completed will be repeated.
        cloneCmd clones the repo in the right folder.
        envCreationCmd creates the conda enviroment and installs the required python packages.
        """
        # Defining initial empty list of commands
        commandList = []

        # Defining empty list of protocol dependencies
        dependencies = []

        for repoName in PROTOCOL_LIST[protocolName]:
            # Defining repo variables
            repoVariableName = repoName.upper()
            protocolRepo = getattr(cls, "_" + repoName.lower() + "Repo")
            repoURLName = globals()[repoVariableName + "_REPO_URL_NAME"]
            repoDependencies = globals()[repoVariableName + "_DEPENDENCIES"]

            # Defining checkpoint filenames
            checkpointPrefix = repoVariableName + "_"
            repoClonedCheckpoint = checkpointPrefix + "REPO_CLONED"
            enviromentCreatedCheckpoint = checkpointPrefix + "ENVIROMENT_CREATED"
            extraFileCheckpoint = checkpointPrefix + "EXTRA_FILE_"
            extraCommandCheckpoint = checkpointPrefix + "EXTRA_COMMAND_"
        
            # Adding the list of dependencies of the repo to the list of the protocol without duplicates
            dependencies = list(set(dependencies + repoDependencies))

            # Cloning repo
            cloneCmd = 'cd {} && git clone {} {} && touch {}'.format(protocolHome, cls.getGitUrl(repoURLName), repoName, repoClonedCheckpoint)
            commandList.append((cloneCmd, repoClonedCheckpoint))

            # Creating conda virtual enviroment and installing requirements if project runs on Python
            try:
                repoPythonVersion = globals()[repoVariableName + "_PYTHON_VERSION"]
            except:
                repoPythonVersion = None
            if repoPythonVersion: 
                envCreationCmd = '{} conda create -y -n {} python={} && {} && cd {} && conda install pip && $CONDA_PREFIX/bin/pip install -r requirements.txt && cd .. && touch {}'\
                    .format(cls.getCondaActivationCmd(),
                            getattr(cls, repoVariableName + "_WITH_VERSION"),
                            repoPythonVersion,
                            cls.getProtocolActivationCommand(repoVariableName),
                            protocolRepo,
                            enviromentCreatedCheckpoint)
                commandList.append((envCreationCmd, enviromentCreatedCheckpoint))
            
            # Check if protocol repo has extra files to download
            extraFilesVariableName = repoVariableName + "_EXTRA_FILES"
            if (extraFilesVariableName in globals()):
                # Add all extra files as separate commands to create one checkpoint per file
                # Checkpoint file names will be "EXTRA_FILE_0", "EXTRA_FILE_1"...
                downloadCommandList = cls.getProtocolExtraFiles(globals()[extraFilesVariableName])
                commandList = cls.addCommandsToList(commandList, downloadCommandList, extraFileCheckpoint, protocolRepo, protocolHome)
            
            # Check if protocol repo has extra commands to execute
            extraCommandsVariableName = repoVariableName + "_EXTRA_COMMANDS"
            if (extraCommandsVariableName in globals()):
                extraCommands = globals()[extraCommandsVariableName]
                commandList = cls.addCommandsToList(commandList, extraCommands, extraCommandCheckpoint, protocolRepo, protocolHome)

        env.addPackage(protocolVariableName,
                       version=protocolVersion,
                       tar='void.tgz',
                       commands=commandList,
                       neededProgs=dependencies,
                       default=True)
    
    # ---------------------------------- Utils functions  -----------------------

    @classmethod
    def getProtocolExtraFiles(cls, files):
        """
        Creates the neccessary commands to download the extra required files for the protocol.
        -O flag for wget is used to overwrite the downloaded file if one with the same name exists.
        This is done to overwrite potential corrupt files whose download was not fully completed
        """
        commandList = []
        for file in files:
            # Getting filename and path for wget
            fileName = os.popen("basename " + file[0]).read().rstrip("\n")
            filePath = "." if file[1] == "" else file[1]
            # Creating command and adding to the list
            commandList.append("mkdir -p " + filePath + " && wget -O " + filePath + "/" + fileName + " " + file[0])
        
        return commandList
    
    @classmethod
    def addCommandsToList(cls, commandList, newCommands, checkpointPrefix, protocolRepo, protocolHome):
        """
        Appends the given commands to the scipion command list with checkpoints.
        """
        for i in range(len(newCommands)):
            checkpointName = checkpointPrefix + str(i)
            commandList.append(("cd {} && {} && cd {} && touch {}"\
                .format(protocolRepo,
                        newCommands[i],
                        protocolHome,
                        checkpointName),
                checkpointName))
        return commandList
    
    @classmethod
    def getGitUrl(cls, protocolName):
        """
        Returns the GitHub url for the given plugin protocol.
        """
        return globals()[PLUGIN_NAME + "_GIT"] + protocolName
    
    @classmethod
    def getProtocolActivationCommand(cls, variableName):
        """
        Returns the conda activation command for the given protocol.
        """
        return "conda activate " + getattr(cls, variableName + "_WITH_VERSION")

    # ---------------------------------- Protocol execution functions  ----------------------------------

    # ---------------------------------- DAQ ----------------------------------
    @classmethod
    def runDAQ(cls, protocol, args, outDir=None, clean=True):
        """
        Run DAQ script from a given protocol.
        """
        fullProgram = '{} {} && {}'\
            .format(cls.getCondaActivationCmd(), cls.getProtocolActivationCommand('DAQ'), 'python3')
        if not 'main.py' in args:
            args = '{}/main.py {}'.format(cls._daqRepo, args)
        protocol.runJob(fullProgram, args, cwd=cls._daqRepo)

        if outDir is None:
            outDir = protocol._getExtraPath('predictions')

        daqDir = os.path.join(cls._daqRepo, 'Predict_Result', protocol.getVolumeName())
        shutil.copytree(daqDir, outDir)
        if clean:
            shutil.rmtree(daqDir)
    
    # ---------------------------------- Emap2sec ----------------------------------
    @classmethod
    def runEmap2sec(cls, protocol, args, outDir=None, clean=True):
        """
        Run Emap2sec script from a given protocol.
        """
        # Building commands before actual protocol execution
        # Enviroment activation command. Needed to execute befor every other standalone command.
        envActivationCommand = "{} {}".format(cls.getCondaActivationCmd(), cls.getProtocolActivationCommand('EMAP2SEC'))
        
        # If custom output directory is specified, create it if it does not exist
        if outDir:
            protocol.runJob("mkdir -p", outDir, cwd=cls._emap2secRepo)

        # Command to move to Emap2sec's repo's root directory.
        # Needed to be executed once before the actual workflow commands
        moveToRepoCommand = "cd"
        protocol.runJob(moveToRepoCommand, cls._emap2secRepo, cwd=cls._emap2secRepo)

        # Trimapp generation command
        trimappCommand = "map2train_src/bin/map2train"
        for trimappArg in args[0]:
            protocol.runJob(trimappCommand, trimappArg, cwd=cls._emap2secRepo)

        # Dataset generation command
        datasetCommand = "{} && python data_generate/dataset_wo_stride.py".format(envActivationCommand)
        for datasetArg in args[1]:
            protocol.runJob(datasetCommand, datasetArg, cwd=cls._emap2secRepo)

        # Input file for Emap2sec.py
        protocol.runJob("echo", args[2], cwd=cls._emap2secRepo)

        # Emap2sec execution command
        emap2secCommand = "{} && python emap2sec/Emap2sec.py".format(envActivationCommand)
        protocol.runJob(emap2secCommand, args[3], cwd=cls._emap2secRepo)
        
        # Secondary structures visualization command
        visualCommand = "Visual/Visual.pl"
        for visualArg in args[4]:
            protocol.runJob(visualCommand, visualArg, cwd=cls._emap2secRepo)

        # Remove temporary files
        if clean:
            for tmp_file in args[5]:
                protocol.runJob("rm -rf", tmp_file, cwd=cls._emap2secRepo)
    
    # ---------------------------------- Emap2sc+ ----------------------------------
    @classmethod
    def runEmap2secPlus(cls, protocol, args, clean=True):
        """
        Run Emap2secPlus script from a given protocol.
        """
        # Building commands before actual protocol execution
        # Enviroment activation command. Needed to execute befor every other standalone command.
        envActivationCommand = "{} {}".format(cls.getCondaActivationCmd(), cls.getProtocolActivationCommand('EMAP2SECPLUS'))
        
        # Command to move to Emap2sec+'s repo's root directory.
        # Needed to be executed once before the actual workflow commands
        moveToRepoCommand = "cd"
        protocol.runJob(moveToRepoCommand, cls._emap2secplusRepo, cwd=cls._emap2secplusRepo)

        # Emap2sec+ execution command
        runCommand = "{} && python3 main.py".format(envActivationCommand)
        for emap2secPlusArgs in args[0]:
            #testCommand = "echo \'{} {}\'".format(runCommand, emap2secPlusArgs)
            #protocol.runJob(testCommand, '', cwd=cls._emap2secplusRepo)
            protocol.runJob(runCommand, emap2secPlusArgs, cwd=cls._emap2secplusRepo)

        # Remove temporary files
        if clean:
            for tmp_file in args[1]:
                protocol.runJob("rm -rf", tmp_file, cwd=cls._emap2secplusRepo)

    # ---------------------------------- MainMast ----------------------------------
    @classmethod
    def runSegmentation(cls, protocol, args, cwd=None):
        mainMastCall = os.path.join(cls._mainmastRepo, 'MainmastSeg')
        protocol.runJob(mainMastCall, args, cwd=cwd)
    
    @classmethod
    def convertMatrix(cls, protocol, args, cwd=None):
        convertCall = os.path.join(cls._mainmastRepo, 'conv_ncs.pl')
        protocol.runJob(convertCall, args, cwd=cwd)