# **************************************************************************
# *
# * Authors: Daniel Del Hoyo Gomez
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

# ------------------------------------ INSTALLATION VARIABLES ------------------------------------
PLUGIN_NAME = 'KIHARALAB'
KIHARALAB_GIT = 'https://github.com/kiharalab/'
KIHARALAB_HOME = 'KIHARA_HOME'
DAQ_HOME = 'DAQ_HOME'
EMAP2SEC_HOME = 'EMAP2SEC_HOME'
MAINMAST_HOME = 'MAINMAST_HOME'

# Supported versions
V1_0 = '1.0'

# Plugin version
KIHARALAB_DEFAULT_VERSION = V1_0

# Protocol versions 
DAQ_DEFAULT_VERSION = V1_0
EMAP2SEC_DEFAULT_VERSION = V1_0
MAINMAST_DEFAULT_VERSION = V1_0

# Protocol repo versions
DAQ_REPO_DEFAULT_VERSION = V1_0
EMAP2SEC_REPO_DEFAULT_VERSION = V1_0
EMAP2SECPLUS_REPO_DEFAULT_VERSION = V1_0
MAINMAST_REPO_DEFAULT_VERSION = V1_0

# Repo python versions
DAQ_PYTHON_VERSION = '3.8.5'
EMAP2SEC_PYTHON_VERSION = '3.6'
EMAP2SECPLUS_PYTHON_VERSION = '3.6.9'

# Plugin and protocol names
KIHARALAB = 'kiharalab'
DAQ = 'daq'
EMAP2SEC = 'Emap2sec'
EMAP2SECPLUS = 'Emap2secPlus'
MAINMAST = 'MainMast'

# Repository names
DAQ_REPO_URL_NAME = DAQ
EMAP2SEC_REPO_URL_NAME = EMAP2SEC
EMAP2SECPLUS_REPO_URL_NAME = EMAP2SECPLUS
MAINMAST_REPO_URL_NAME = 'MAINMASTseg'

# Protocol name list
PROTOCOL_NAME_LIST = [DAQ, EMAP2SEC, MAINMAST]

# Protocol list. Each protocol can contain multiple repos if functionality of those repos is similar.
# Protocol list is defined as a dictionary with protocol name as key and protocol repo list as value.
PROTOCOL_LIST = {DAQ: [DAQ], EMAP2SEC: [EMAP2SEC, EMAP2SECPLUS], MAINMAST: [MAINMAST]}

# Protocol dependencies. All software required to run each protocol must be defined here.
DAQ_DEPENDENCIES = ['git', 'conda', 'pip']
EMAP2SEC_DEPENDENCIES = ['git', 'conda', 'pip', 'wget', 'make', 'gcc']
EMAP2SECPLUS_DEPENDENCIES = ['git', 'conda', 'pip', 'wget', 'make', 'gcc', 'tar']
MAINMAST_DEPENDENCIES = ['git', 'make', 'gcc', 'gzip']

# Download links for extra files
# Extra files are defined as a list of tuples with two elements
# 	The first element will be the download link
#	The second element is the path for the file to be downloaded. Leave as an empty string for default value (current folder)
# Variable name has to be <PROTOCOL_NAME>_EXTRA_FILES. For example: DAQ_EXTRA_FILES, or EMAP2SEC_EXTRA_FILES
EMAP2SEC_EXTRA_FILES = [
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/checkpoint", "models/emap2sec_models_exp1"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/emap2sec_L1_exp.ckpt-108000.data-00000-of-00001", "models/emap2sec_models_exp1"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/emap2sec_L1_exp.ckpt-108000.index", "models/emap2sec_models_exp1"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp1/emap2sec_L1_exp.ckpt-108000.meta", "models/emap2sec_models_exp1"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/checkpoint", "models/emap2sec_models_exp2"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/emap2sec_L2_exp.ckpt-20000.data-00000-of-00001", "models/emap2sec_models_exp2"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/emap2sec_L2_exp.ckpt-20000.index", "models/emap2sec_models_exp2"),
	("https://kiharalab.org/Emap2sec_models/emap2sec_models_exp2/emap2sec_L2_exp.ckpt-20000.meta", "models/emap2sec_models_exp2")
]

EMAP2SECPLUS_EXTRA_FILES = [
	("https://kiharalab.org/emsuites/emap2secplus_model/best_model.tar.gz", "."),
	("https://kiharalab.org/emsuites/emap2secplus_model/nocontour_best_model.tar.gz", ".")
]

# Extra commands needed for proper project execution
GRANT_EXECUTION_ACCESS = "chmod -R +x *"
CLEAN_ALL_OBJECTS = "rm -rf *.o"
EMAP2SEC_EXTRA_COMMANDS = [
	"mkdir -p results",
	GRANT_EXECUTION_ACCESS,
	"cd map2train_src && make && cd ..",
	GRANT_EXECUTION_ACCESS
]

EMAP2SECPLUS_EXTRA_COMMANDS = [
	"tar -xf best_model.tar.gz && rm -f best_model.tar.gz",
	"tar -xf nocontour_best_model.tar.gz && rm -f nocontour_best_model.tar.gz",
	"cd process_map && make",
	GRANT_EXECUTION_ACCESS
]

# Extra conda commands will only be run when conda enviroment has been created
EMAP2SECPLUS_EXTRA_CONDA_COMMANDS = [
	"conda install -y pytorch==1.1.0 torchvision==0.3.0 cudatoolkit=10.0 -c pytorch"
]

MAINMAST_EXTRA_COMMANDS = [
	CLEAN_ALL_OBJECTS + " MainmastSeg",
	GRANT_EXECUTION_ACCESS,
	"make",
	CLEAN_ALL_OBJECTS,
	GRANT_EXECUTION_ACCESS,
	"cd example1 && gunzip emd-0093.mrc.gz MAP_m4A.mrc.gz region0.mrc.gz region1.mrc.gz region2.mrc.gz region3.mrc.gz"
]

# ------------------------------------ PROTOCOL FORM VARIABLES ------------------------------------
# Emap2sec param constants
EMAP2SEC_NORM_GLOBAL = 0
EMAP2SEC_NORM_LOCAL = 1
EMAP2SEC_TYPE_EMAP2SEC = 0
EMAP2SEC_TYPE_EMAP2SECPLUS = 1
EMAP2SECPLUS_TYPE_SIMUL6A = 0
EMAP2SECPLUS_TYPE_SIMUL10A = 1
EMAP2SECPLUS_TYPE_SIMUL6_10A = 2
EMAP2SECPLUS_TYPE_EXPERIMENTAL = 3
EMAP2SECPLUS_MODE_DETECT_STRUCTS = 0
EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS = 1
EMAP2SECPLUS_MODE_DETECT_EXPERIMENTAL_FOLD4 = 2
EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4 = 3
EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4 = 4
EMAP2SECPLUS_RESIZE_NUMBA = 0
EMAP2SECPLUS_RESIZE_SCIPY = 1
EMAP2SECPLUS_FOLD1 = 0
EMAP2SECPLUS_FOLD2 = 1
EMAP2SECPLUS_FOLD3 = 2
EMAP2SECPLUS_FOLD4 = 3