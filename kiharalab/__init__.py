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
    _daqHome = os.path.join(pwem.Config.EM_ROOT, DAQ + '-' + DAQ_DEFAULT_VERSION)
    _daqRepo = os.path.join(_daqHome, 'DAQ')

    @classmethod
    def _defineVariables(cls):
        """ Return and write a variable in the config file.
        """
        cls._defineEmVar(DAQ_HOME, DAQ + '-' + DAQ_DEFAULT_VERSION)
        cls._defineVar("DAQ_ENV_ACTIVATION", 'conda activate daq-env')

    @classmethod
    def defineBinaries(cls, env):
        cls.addDAQPackage(env)

    @classmethod
    def addDAQPackage(cls, env):
        installationCmd = 'cd {} && git clone {} && '.format(cls._daqHome, cls.getGitUrl())
        installationCmd += 'conda create -y -n daq-env python=3.8.5 && {} {} && ' \
            .format(cls.getCondaActivationCmd(), cls.getDAQEnvActivation())
        installationCmd += 'conda install -y -c conda-forge mrcfile && '
        installationCmd += 'cd DAQ && pip install -r requirement.txt && '

        # Creating validation file
        DAQ_INSTALLED = '%s_installed' % DAQ
        installationCmd += 'cd .. && touch %s' % DAQ_INSTALLED  # Flag installation finished

        env.addPackage(DAQ,
                       version=DAQ_DEFAULT_VERSION,
                       tar='void.tgz',
                       commands=[(installationCmd, DAQ_INSTALLED)],
                       neededProgs=["conda", "pip"],
                       default=True)

    @classmethod
    def runDAQ(cls, protocol, args, outDir=None, clean=True):
        """ Run DAQ script from a given protocol. """
        fullProgram = '%s %s && %s' % (cls.getCondaActivationCmd(), cls.getDAQEnvActivation(), 'python3')
        if not 'main.py' in args:
            args = '{}/main.py '.format(cls._daqRepo) + args
        protocol.runJob(fullProgram, args, cwd=cls._daqRepo)

        if outDir is None:
            outDir = protocol._getExtraPath('predictions')

        daqDir = os.path.join(cls._daqRepo, 'Predict_Result', protocol.getVolumeName())
        shutil.copytree(daqDir, outDir)
        if clean:
            shutil.rmtree(daqDir)

    @classmethod
    def getEnviron(cls):
        pass

    @classmethod
    def getDAQEnvActivation(cls):
        return cls.getVar("DAQ_ENV_ACTIVATION")

    @classmethod
    def getGitUrl(cls):
        return "https://github.com/kiharalab/DAQ"

    # ---------------------------------- Utils functions  -----------------------

