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
    Definition of class variables. For each protocol, three variables will be created.
    <protocolNameInUppercase>_WITH_VERSION will contain <protocolNameInUppercase>-<protocolVersion>. For example, "DAQ-1.0"
    _<protocolNameInLowercase>Home will contain the full path of the protocol, ending with a folder whose name will be <protocolNameInUppercase>_WITH_VERSION variable. For example: "~/Documents/scipion/software/em/DAQ-1.0"
    _<protocolNameInLowercase>Repo will be a folder inside _<protocolNameInLowercase>Home and its name will be <protocolNameInUppercase>. For example: "DAQ"
    """
    names = [name.upper() for name in PROTOCOL_LIST]
    for name in names:
        nameInLowercase = name.lower()
        locals()[name + "_WITH_VERSION"] = name + '-' + globals()[name + "_DEFAULT_VERSION"]
        locals()["_" + nameInLowercase + "Home"] = os.path.join(pwem.Config.EM_ROOT, locals()[name + "_WITH_VERSION"])
        locals()["_" + nameInLowercase + "Repo"] = os.path.join(locals()["_" + nameInLowercase + "Home"], globals()[name])

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
                                    getattr(cls, "_" + nameInLowercase + "Repo"),
                                    name,
                                    globals()[name + "_DEFAULT_VERSION"])

    @classmethod
    def addProtocolPackage(cls, env, protocolName, protocolHome, protocolRepo, protocolVariableName, protocolVersion):
        """
        Define and execute commands for protocol installation.
        Every command has it's own checkpoint so if, for some reason, process is interrupted, only commands that were not completed will be repeated.
        cloneCmd clones the repo in the right folder.
        envCreationCmd creates the conda enviroment and installs the required python packages.
        """
        cloneCmd = 'cd {} && git clone {} && touch REPO_CLONED' .format(protocolHome, cls.getGitUrl(protocolName))
        envCreationCmd = '{} conda create -y -n {} python={} && {} && cd {} && conda install pip && $CONDA_PREFIX/bin/pip install -r requirements.txt && cd .. && touch ENVIROMENT_CREATED'\
            .format(cls.getCondaActivationCmd(),
                    getattr(cls, protocolVariableName + "_WITH_VERSION"),
                    globals()[protocolVariableName + "_PYTHON_VERSION"],
                    cls.getProtocolActivationCommand(protocolVariableName),
                    protocolRepo)
        
        ## REMOVE LATER ##
        if protocolVariableName == 'EMAP2SEC': # REMOVE WHEN PR APPROVED
            envCreationCmd = '{} conda create -y -n {} python={} && {} && cd {} && conda install pip && echo \'tensorflow==1.15\\nscikit-learn==0.24.2\\npandas==1.1.5\\nnumpy==1.16.4\' > requirements.txt && $CONDA_PREFIX/bin/pip install -r requirements.txt && cd .. && touch ENVIROMENT_CREATED'\
                .format(cls.getCondaActivationCmd(),
                        getattr(cls, protocolVariableName + "_WITH_VERSION"),
                        globals()[protocolVariableName + "_PYTHON_VERSION"],
                        cls.getProtocolActivationCommand(protocolVariableName),
                        protocolRepo)
        ## REMOVE LATER ##

        commandList = [(cloneCmd, "REPO_CLONED"), (envCreationCmd, "ENVIROMENT_CREATED")]
        
        # Check if protocol has extra files to download
        extraFilesVariableName = protocolVariableName + "_EXTRA_FILES"
        if (extraFilesVariableName in globals()):
            # Add all extra files as separate commands to create one checkpoint per file
            downloadCommandList = cls.getProtocolExtraFiles(globals()[extraFilesVariableName])
            for i in range(len(downloadCommandList)):
                checkpointName = "EXTRA_FILE_" + str(i)
                commandList.append(("cd " + protocolRepo + " && " + downloadCommandList[i] + " && cd " + protocolHome + " && touch " + checkpointName, checkpointName))

        env.addPackage(protocolVariableName,
                       version=protocolVersion,
                       tar='void.tgz',
                       commands=commandList,
                       neededProgs=["conda", "pip"],
                       default=True)
    
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
    def runDAQ(cls, protocol, args, outDir=None, clean=True):
        print("CUSTOM PRINT - start - runDAQ") # REMOVE
        """ Run DAQ script from a given protocol. """
        fullProgram = '%s %s && %s' % (cls.getCondaActivationCmd(), cls.getEnvActivation('DAQ'), 'python3')
        if not 'main.py' in args:
            args = '{}/main.py '.format(cls._daqRepo) + args
        protocol.runJob(fullProgram, args, cwd=cls._daqRepo)

        if outDir is None:
            outDir = protocol._getExtraPath('predictions')

        daqDir = os.path.join(cls._daqRepo, 'Predict_Result', protocol.getVolumeName())
        shutil.copytree(daqDir, outDir)
        if clean:
            shutil.rmtree(daqDir)
        print("CUSTOM PRINT - ebd - runDAQ") # REMOVE
    
    @classmethod
    def runEmap2sec(cls, protocol, args, outDir=None, clean=True):
        print("CUSTOM PRINT - start - runEmap2sec") # REMOVE
        """
        Run Emap2sec script from a given protocol.
        """
        fullProgram = "{} {} && {}"\
            .format(cls.getCondaActivationCmd(),
                cls.getProtocolActivationCommand('EMAP2SEC'),
                'python3')
        if not 'main.py' in args:
            args = '{}/main.py '.format(cls._emap2secRepo) + args
        protocol.runJob(fullProgram, args, cwd=cls._emap2secRepo)

        if outDir is None:
            outDir = protocol._getExtraPath('predictions')

        emap2secDir = os.path.join(cls._emap2secRepo, 'Predict_Result', protocol.getVolumeName())
        shutil.copytree(emap2secDir, outDir)
        if clean:
            shutil.rmtree(emap2secDir)
        print("CUSTOM PRINT - end - runEmap2sec") # REMOVE

    @classmethod
    def getGitUrl(cls, protocolName):
        """
        Returns the GitHub url for the given Kiharalab protocol.
        """
        return KIHARALAB_GIT + protocolName
    
    @classmethod
    def getProtocolActivationCommand(cls, variableName):
        """
        Returns the conda activation command for the given protocol.
        """
        return "conda activate " + getattr(cls, variableName + "_WITH_VERSION")

    # ---------------------------------- Utils functions  -----------------------
