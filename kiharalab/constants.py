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

KIHARALAB_GIT = 'https://github.com/kiharalab/'
KIHARALAB_HOME = 'KIHARA_HOME'
DAQ_HOME = 'DAQ_HOME'
EMAP2SEC_HOME = 'EMAP2SEC_HOME'
PYMOL_HOME = 'PYMOL_HOME'


# Supported Versions
V1_0 = '1.0'
KIHARALAB_DEFAULT_VERSION = V1_0
DAQ_DEFAULT_VERSION = V1_0
EMAP2SEC_DEFAULT_VERSION = V1_0
DAQ_PYTHON_VERSION = '3.8.5'
EMAP2SEC_PYTHON_VERSION = '3.6'

# Plugin and protocol names
KIHARALAB = 'kiharalab'
DAQ = 'DAQ'
EMAP2SEC = 'Emap2sec'

# Protocol name list
PROTOCOL_LIST = [DAQ, EMAP2SEC]

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

# Extra commands needed for proper project execution
EMAP2SEC_EXTRA_COMMANDS = [
	"mkdir -p results",
	"chmod -R +x *",
	"cd map2train_src && make && cd .."
]

# Emap2sec param constants
EMAP2SEC_NORM_GLOBAL = 0
EMAP2SEC_NORM_LOCAL = 1
