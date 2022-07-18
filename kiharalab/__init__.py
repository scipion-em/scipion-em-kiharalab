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

from numpy import var
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
    # Defining some variable suffixes
    gitSuffix = "_GIT"
    homeSuffix = "_HOME"
    envSuffix = "_ENV"
    repoNameSuffix = "_REPO_URL_NAME"
    repoDefaultVersionSuffix = "_REPO_DEFAULT_VERSION"
    defaultVersionSuffix = "_DEFAULT_VERSION"
    pythonVersionSuffix = "_PYTHON_VERSION"
    withVersionSuffix = "_WITH_VERSION"
    dependenciesSuffix = "_DEPENDENCIES"
    extraFilesSuffix = "_EXTRA_FILES"
    extraCommandsSuffix = "_EXTRA_COMMANDS"
    extraCondaCommandsSuffix = "_EXTRA_CONDA_COMMANDS"

    # Getting protocols whose variables will be defined
    names = PROTOCOL_NAME_LIST
    for name in names:
        for protocolRepoName in PROTOCOL_LIST[name]:
            nameInLowercase = protocolRepoName.lower()
            nameInUppercase = protocolRepoName.upper()
            nameAsBinary = protocolRepoName[0].lower() + protocolRepoName[1:]
            locals()[nameInUppercase + withVersionSuffix] = nameAsBinary + '-' + globals()[nameInUppercase + repoDefaultVersionSuffix]
            locals()["_" + nameInLowercase + "Home"] = os.path.join(pwem.Config.EM_ROOT, locals()[name.upper() + withVersionSuffix])
            locals()["_" + nameInLowercase + "Repo"] = os.path.join(locals()["_" + nameInLowercase + "Home"], globals()[nameInUppercase])
        
        # Substituting each name with the same name in uppercase
        nameIndex = names.index(name)
        names[nameIndex] = name[0].lower() + name[1:]

    @classmethod
    def _defineVariables(cls):
        """
        Return and write a home and conda enviroment variable in the config file.
        Each protocol will have a variable called <protocolNameInUppercase>_HOME, and another called <protocolNameInUppercase>_ENV
        <protocolNameInUppercase>_HOME will contain the path to the protocol installation. For example: "~/Documents/scipion/software/em/DAQ-1.0"
        <protocolNameInUppercase>_ENV will contain the name of the conda enviroment for that protocol. For example: "DAQ-1.0"
        """
        for name in cls.names:
            nameInUppercase = name.upper()
            protocolHomeAndEnv = name + '-' + globals()[nameInUppercase + cls.defaultVersionSuffix]
            cls._defineEmVar(globals()[nameInUppercase + cls.homeSuffix], protocolHomeAndEnv)
            cls._defineVar(nameInUppercase + cls.envSuffix, protocolHomeAndEnv)

    @classmethod
    def defineBinaries(cls, env):
        """
        This function defines the binaries for each protocol.
        """
        for name in cls.names:
            nameInUppercase = name.upper()
            nameInLowercase = name.lower()
            cls.addProtocolPackage(env,
                                    globals()[nameInUppercase],
                                    getattr(cls, "_" + nameInLowercase + "Home"),
                                    nameInLowercase[0] + name[1:],
                                    globals()[nameInUppercase + cls.defaultVersionSuffix])

    @classmethod
    def addProtocolPackage(cls, env, protocolName, protocolHome, protocolBinaryName, protocolVersion):
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
            repoDependencies = globals()[repoVariableName + cls.dependenciesSuffix]

            # Defining checkpoint filenames
            checkpointPrefix = repoVariableName + "_"
            repoClonedCheckpoint = checkpointPrefix + "REPO_CLONED"
            enviromentCreatedCheckpoint = checkpointPrefix + "ENVIROMENT_CREATED"
            extraFileCheckpoint = checkpointPrefix + "EXTRA_FILE_"
            extraCommandCheckpoint = checkpointPrefix + "EXTRA_COMMAND_"

            # Defining command string to move to project's root directory.
            cdCmd = 'cd ' + protocolHome

            # Cloning repo if project is downloaded from github
            repoURLName = globals()[repoVariableName + cls.repoNameSuffix] if repoVariableName + cls.repoNameSuffix in globals() else None
            if repoURLName:
                cloneCmd = '{} && git clone {} {} && touch {}'.format(cdCmd, cls.getGitUrl(repoURLName), repoName, repoClonedCheckpoint)
                commandList.append((cloneCmd, repoClonedCheckpoint))
            
            # Defining where the next steps will take place.
            # If a repository has been downloaded, inside its directory. Otherwise, inside the protocol's root directory.
            processDirectory = protocolRepo if repoURLName else protocolHome

            # Check if protocol repo has extra files to download
            extraFilesVariableName = repoVariableName + cls.extraFilesSuffix
            if (extraFilesVariableName in globals()):
                # Add all extra files as separate commands to create one checkpoint per file
                # Checkpoint file names will be "EXTRA_FILE_0", "EXTRA_FILE_1"...
                downloadCommandList = cls.getProtocolExtraFiles(globals()[extraFilesVariableName])
                commandList = cls.addCommandsToList(commandList, downloadCommandList, extraFileCheckpoint, processDirectory, protocolHome)
            
            # Check if protocol repo has extra commands to execute
            extraCommandsVariableName = repoVariableName + cls.extraCommandsSuffix
            if (extraCommandsVariableName in globals()):
                extraCommands = globals()[extraCommandsVariableName]
                commandList = cls.addCommandsToList(commandList, extraCommands, extraCommandCheckpoint, processDirectory, protocolHome)
            
            # Creating conda virtual enviroment and installing requirements if project runs on Python
            if repoVariableName + cls.pythonVersionSuffix in globals():
                envCreationCmd = '{} conda create -y -n {} python={} && {} && cd {} && conda install pip && $CONDA_PREFIX/bin/pip install -r requirements.txt {}&& cd .. && touch {}'\
                    .format(cls.getCondaActivationCmd(),
                            getattr(cls, repoVariableName + cls.withVersionSuffix),
                            globals()[repoVariableName + cls.pythonVersionSuffix],
                            cls.getProtocolActivationCommand(repoVariableName),
                            protocolRepo,
                            cls.getCondaExtraCommands(repoVariableName),
                            enviromentCreatedCheckpoint)
                commandList.append((envCreationCmd, enviromentCreatedCheckpoint))
            
            # Adding the list of dependencies of the repo to the list of the protocol without duplicates
            dependencies = list(set(dependencies + repoDependencies + cls.getDetectedDependencies(repoVariableName)))

        env.addPackage(protocolBinaryName,
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
    def getCondaExtraCommands(cls, repoVariableName):
        """
        Returns the extra conda related commands for the given repo.
        """
        commandsString = ''
        # Check if protocol repo has extra conda enviroment related commands to execute
        extraCondaCommandsVariableName = repoVariableName + cls.extraCondaCommandsSuffix
        if (extraCondaCommandsVariableName in globals()):
            extraCommands = globals()[extraCondaCommandsVariableName]
            commandsString = "&& " + " && ".join(extraCommands) + " "

        return commandsString
    
    @classmethod
    def getGitUrl(cls, protocolName):
        """
        Returns the GitHub url for the given plugin protocol.
        """
        return globals()[PLUGIN_NAME + cls.gitSuffix] + protocolName
    
    @classmethod
    def getProtocolActivationCommand(cls, variableName):
        """
        Returns the conda activation command for the given protocol.
        """
        return "conda activate " + getattr(cls, variableName + cls.withVersionSuffix)
    
    @classmethod
    def getDetectedDependencies(cls, variableName):
        """
        Returns a list with the detected dependencies of the protocol even if it is not properly defined in constants.py.
        As of today, git is used in all protocols and downloading extra files uses wget.
        The rest is left for the new protocol programmer to decide.
        """
        # Defining default dependencies
        detectedDependencies = []

        # Checking if protocol downloads source from git. If so, git is needed.
        gitVariableName = variableName + cls.repoNameSuffix
        if (gitVariableName in globals()):
            detectedDependencies.append('git')

        # Checking if protocol downloads extra files. If so, wget is needed.
        extraFilesVariableName = variableName + cls.extraFilesSuffix
        if (extraFilesVariableName in globals()):
            detectedDependencies.append('wget')
        
        return detectedDependencies

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
            protocol.runJob(runCommand, emap2secPlusArgs, cwd=cls._emap2secplusRepo)
        
        # Output file relocation
        protocol.runJob("mv", args[1][0] + ' ' + args[1][1], cwd=cls._emap2secplusRepo)
        
        # Remove temporary files
        if clean:
            for tmp_file in args[2]:
                protocol.runJob("rm -rf", tmp_file, cwd=cls._emap2secplusRepo)

    # ---------------------------------- MainMast ----------------------------------
    @classmethod
    def runSegmentation(cls, protocol, args, cwd=None):
        """
        Run segmentation phase for MainMast.
        """
        mainMastCall = os.path.join(cls._mainmastRepo, 'MainmastSeg')
        protocol.runJob(mainMastCall, args, cwd=cwd)
    
    @classmethod
    def convertMatrix(cls, protocol, args, cwd=None):
        """
        Run matrix conversion phase for MainMast.
        """
        convertCall = os.path.join(cls._mainmastRepo, 'conv_ncs.pl')
        protocol.runJob(convertCall, args, cwd=cwd)

    @classmethod
    def cleanTmpfiles(cls, protocol, tmpFiles=[]):
        """
        This method removes all temporary files to reduce disk usage.
        """
        for tmp_file in tmpFiles:
            protocol.runJob("rm -rf", tmp_file, cwd=cls._mainmastRepo)