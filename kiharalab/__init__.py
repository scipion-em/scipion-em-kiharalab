# **************************************************************************
# *
# * Authors:  Daniel Del Hoyo (ddelhoyo@cnb.csic.es)
# *           Martín Salinas  (martin.salinas@cnb.csic.es)
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
import os

import pwem
from scipion.install.funcs import InstallHelper
from .constants import *

__version__ = KIHARALAB_VERSION
_logo = "kiharalab_logo.png"
_references = ['genki2021DAQ']

class Plugin(pwem.Plugin):
    """
    Definition of class variables. For each package, a variable will be created.
    _<packageNameInLowercase>Home will contain the full path of the package, ending with a folder whose name will be <packageNameFirstLetterLowercase>-<defaultPackageVersion> variable.
        For example: _emap2secHome = "~/Documents/scipion/software/em/emap2sec-1.0"
    
    Inside that package, for each binary, there will also be another variable.
    _<binaryNameInLowercase>Binary will be a folder inside _<packageNameInLowercase>Home and its name will be <binaryName>.
        For example: _emap2secplusBinary = "~/Documents/scipion/software/em/emap2sec-1.0/Emap2secPlus"
    """
    # DAQ
    daqDefaultVersion = DAQ_DEFAULT_VERSION
    _daqHome = os.path.join(pwem.Config.EM_ROOT, f'daq-{daqDefaultVersion}')
    _daqBinary = os.path.join(_daqHome, 'daq')

    # Emap2sec
    emap2secDefaultVersion = EMAP2SEC_DEFAULT_VERSION
    _emap2secHome = os.path.join(pwem.Config.EM_ROOT, f'emap2sec-{emap2secDefaultVersion}')
    _emap2secBinary = os.path.join(_emap2secHome, 'Emap2sec')
    _emap2secplusBinary = os.path.join(_emap2secHome, 'Emap2secPlus')

    # MainMast
    mainmastDefaultVersion = MAINMAST_DEFAULT_VERSION
    _mainmastHome = os.path.join(pwem.Config.EM_ROOT, f'mainMast-{mainmastDefaultVersion}')
    _mainmastBinary = os.path.join(_mainmastHome, 'MainMast')

    # DMM
    dmmDefaultVersion = DMM_DEFAULT_VERSION
    _DMMHome = os.path.join(pwem.Config.EM_ROOT, f'dmm-{dmmDefaultVersion}')
    _DMMBinary = os.path.join(_DMMHome, 'DMM')

    # CryoREAD
    cryoREADDefaultVersion = CRYOREAD_DEFAULT_VERSION
    _cryoREADHome = os.path.join(pwem.Config.EM_ROOT, f'cryoREAD-{cryoREADDefaultVersion}')
    _cryoREADBinary = os.path.join(_cryoREADHome, 'CryoREAD')

    @classmethod
    def _defineVariables(cls):
        """
        Return and write a home and conda enviroment variable in the config file.
        Each package will have a variable called <packageNameInUppercase>_HOME, and another called <packageNameInUppercase>_ENV
        <packageNameInUppercase>_HOME will contain the path to the package installation. For example: "~/Documents/scipion/software/em/daq-1.0"
        <packageNameInUppercase>_ENV will contain the name of the conda enviroment for that package. For example: "daq-1.0"
        """
        # DAQ
        cls._defineEmVar(DAQ_HOME, cls._daqHome)
        cls._defineVar('DAQ_ENV', f'daq-{cls.daqDefaultVersion}')

        # Emap2sec
        cls._defineEmVar(EMAP2SEC_HOME, cls._emap2secHome)
        cls._defineVar('EMAP2SEC_ENV', f'emap2sec-{cls.emap2secDefaultVersion}')
        cls._defineVar('EMAP2SECPLUS_ENV', f'emap2secPlus-{cls.emap2secDefaultVersion}')

        # MainMast
        cls._defineEmVar(MAINMAST_HOME, cls._mainmastHome)
        cls._defineVar('MAINMAST_ENV', f'mainMast-{cls.mainmastDefaultVersion}')

        # DMM
        cls._defineEmVar(DMM_HOME, cls._DMMHome)
        cls._defineVar('DMM_ENV', f'dmm-{cls.dmmDefaultVersion}')

        # CryoREAD
        cls._defineEmVar(CRYOREAD_HOME, cls._cryoREADHome)
        cls._defineVar('CRYOREAD_ENV', f'cryoREAD-{cls.cryoREADDefaultVersion}')

    @classmethod
    def defineBinaries(cls, env):
        """
        This function defines the binaries for each protocol.
        """
        cls.addDAQ(env)
        cls.addEmap2sec(env)
        cls.addMainMast(env)
        cls.addCryoREAD(env)
        cls.addDMM(env)
    
    @classmethod    
    def addDAQ(cls, env):
        """
        This function provides the neccessary commands for installing DAQ.
        """
        # Defining protocol variables
        packageName = 'daq'

        # Instanciating installer
        installer = InstallHelper(packageName, packageVersion=cls.daqDefaultVersion)

        # Installing protocol
        installer.getCloneCommand('https://github.com/kiharalab/DAQ.git', binaryFolderName=packageName)\
            .getCondaEnvCommand(pythonVersion='3.9', binaryPath=cls._daqBinary, requirementsFile=True)\
            .addPackage(env, dependencies=['git', 'conda'])

    @classmethod    
    def addEmap2sec(cls, env):
        """
        This function provides the neccessary commands for installing Emap2sec.
        """
        # Defining protocol variables
        packageName = 'emap2sec'
        emap2secFolderName = 'Emap2sec'
        emap2secPlusFolderName = 'Emap2secPlus'

        # Instanciating installer
        installer = InstallHelper(packageName, packageVersion=cls.emap2secDefaultVersion)

        # Defining extra files to download
        firstLocation = "models/emap2sec_models_exp1"
        secondLocation = "models/emap2sec_models_exp2"
        emap2secExtraFiles = [
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/checkpoint", path=firstLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/emap2sec_L1_exp.ckpt-108000.data-00000-of-00001", path=firstLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/emap2sec_L1_exp.ckpt-108000.index", path=firstLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/emap2sec_L1_exp.ckpt-108000.meta", path=firstLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/checkpoint", path=secondLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/emap2sec_L2_exp.ckpt-20000.data-00000-of-00001", path=secondLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/emap2sec_L2_exp.ckpt-20000.index", path=secondLocation),
            installer.getFileDict("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/emap2sec_L2_exp.ckpt-20000.meta", path=secondLocation)
        ]

        emap2secPlusExtraFiles = [
            installer.getFileDict("https://kiharalab.org/emsuites/emap2secplus_model/best_model.tar.gz"),
            installer.getFileDict("https://kiharalab.org/emsuites/emap2secplus_model/nocontour_best_model.tar.gz")
        ]

        # Defininig extra commands to run
        grantExecPermission = "chmod -R +x *"
        emap2secExtraCommands = [
            "mkdir -p results",
            grantExecPermission,
            "cd map2train_src && make",
            grantExecPermission
        ]

        emap2secPlusExtraCommands = [
            "tar -xf best_model.tar.gz && rm -f best_model.tar.gz",
            "tar -xf nocontour_best_model.tar.gz && rm -f nocontour_best_model.tar.gz",
            "cd process_map && make",
            grantExecPermission
        ]

        # Installing protocol
        installer.getCloneCommand('https://github.com/kiharalab/emap2sec.git', binaryFolderName=emap2secFolderName)\
            .getCloneCommand('https://github.com/kiharalab/emap2secPlus.git', binaryFolderName=emap2secPlusFolderName)\
            .getCondaEnvCommand(binaryPath=cls._emap2secBinary, pythonVersion='3.6', requirementsFile=True)\
            .getCondaEnvCommand(binaryPath=cls._emap2secplusBinary, binaryName='emap2secPlus', pythonVersion='3.6.9', requirementsFile=True)\
            .addCondaPackages(packages=['pytorch==1.1.0', 'cudatoolkit=10.0'], binaryName='emap2secPlus', channel='pytorch')\
            .getExtraFiles(emap2secExtraFiles, workDir=cls._emap2secBinary)\
            .getExtraFiles(emap2secPlusExtraFiles, binaryName='emap2secPlus', workDir=cls._emap2secplusBinary)\
            .addCommands(emap2secExtraCommands, workDir=cls._emap2secBinary)\
            .addCommands(emap2secPlusExtraCommands, binaryName='emap2secPlus', workDir=cls._emap2secplusBinary)\
            .addPackage(env, dependencies=['git', 'conda', 'wget', 'make', 'gcc', 'tar'])

    @classmethod    
    def addMainMast(cls, env):
        """
        This function provides the neccessary commands for installing MainMast.
        """
        # Defining protocol variables
        packageName = 'mainMast'

        # Instanciating installer
        installer = InstallHelper(packageName, packageVersion=cls.mainmastDefaultVersion)

        # Extra commands
        grantExecPermission = "chmod -R +x *"
        cleanObjs = "rm -rf *.o"
        extraCommands = [
            cleanObjs + " MainmastSeg",
            grantExecPermission,
            "make",
            cleanObjs,
            grantExecPermission,
            "cd example1 && gunzip emd-0093.mrc.gz MAP_m4A.mrc.gz region0.mrc.gz region1.mrc.gz region2.mrc.gz region3.mrc.gz"
        ]

        # Installing protocol
        installer.getCloneCommand('https://github.com/kiharalab/MAINMASTseg.git', binaryFolderName='MainMast')\
            .addCommands(extraCommands, workDir=cls._mainmastBinary)\
            .addPackage(env, dependencies=['git', 'make', 'gcc', 'gzip'])
    
    @classmethod
    def addCryoREAD(cls, env):
        """
        This function provides the necessary commands for installing CryoREAD.
        """
        # Defining protocol variables
        packageName = 'cryoREAD'

        # Instantiating installer
        installer = InstallHelper(packageName, packageVersion=cls.cryoREADDefaultVersion)

        # Installing protocol
        currentPath = os.path.dirname(os.path.abspath(__file__))
        enFilePath = os.path.join(currentPath, "environment.yml")
        targetFile = f"{packageName.upper()}_CONDA_ENV_CREATED"
        envName = f"{packageName}-{cls.cryoREADDefaultVersion}"
        installer.getCloneCommand('https://github.com/kiharalab/CryoREAD.git', binaryFolderName=os.path.basename(cls._cryoREADBinary)) \
            .addCommand(f"conda env create -y -n {envName} -f {enFilePath}", workDir=cls._cryoREADBinary, targetName=targetFile)\
            .addPackage(env, dependencies=['git', 'conda'])

    @classmethod    
    def addDMM(cls, env):
        """
        This function provides the neccessary commands for installing DMM.
        """
        # Defining protocol variables
        packageName = 'dmm'

        # Instanciating installer
        installer = InstallHelper(packageName, packageVersion=cls.dmmDefaultVersion)
        
        # Installing protocol
        currentPath = os.path.dirname(os.path.abspath(__file__))
        enFilePath = os.path.join(currentPath, "environment.yml")
        targetFile = f"{packageName.upper()}_CONDA_ENV_CREATED"
        envName = f"{packageName}-{cls.dmmDefaultVersion}"
        installer.getCloneCommand('https://github.com/kiharalab/DeepMainMast.git', binaryFolderName=os.path.basename(cls._DMMBinary))\
            .addCommand(f"conda env create -y -n {envName} -f {enFilePath}", workDir=cls._DMMBinary, targetName=targetFile)\
            .addPackage(env, dependencies=['git', 'conda'])

    # ---------------------------------- Utils functions  -----------------------
    @classmethod
    def getProtocolEnvName(cls, protocolName, repoName=None):
        """
        This function returns the env name for a given protocol and repo.
        """
        return f"{repoName if repoName else protocolName}-{getattr(cls, protocolName + 'DefaultVersion')}"
    
    @classmethod
    def getProtocolActivationCommand(cls, protocolName, repoName=None):
        """
        Returns the conda activation command for the given protocol.
        """
        return f"conda activate {cls.getProtocolEnvName(protocolName, repoName)}"
