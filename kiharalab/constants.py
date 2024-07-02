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
KIHARALAB_VERSION = '1.0.6'

# Protocol versions 
DAQ_DEFAULT_VERSION = V1_0
EMAP2SEC_DEFAULT_VERSION = V1_0
MAINMAST_DEFAULT_VERSION = V1_0

# Protocol repo versions
DAQ_REPO_DEFAULT_VERSION = V1_0
EMAP2SEC_REPO_DEFAULT_VERSION = V1_0
EMAP2SECPLUS_REPO_DEFAULT_VERSION = V1_0
MAINMAST_REPO_DEFAULT_VERSION = V1_0

# ------------------------------------ PROTOCOL FORM VARIABLES ------------------------------------
# Emap2sec param constants
EMAP2SEC_NORM_GLOBAL = 0
EMAP2SEC_NORM_LOCAL = 1
EMAP2SEC_TYPE_EMAP2SEC = 0
EMAP2SEC_TYPE_EMAP2SECPLUS = 1
# Emap2sec+ form constants
EMAP2SECPLUS_TYPE_SIMUL6A = 0
EMAP2SECPLUS_TYPE_SIMUL10A = 1
EMAP2SECPLUS_TYPE_SIMUL6_10A = 2
EMAP2SECPLUS_TYPE_EXPERIMENTAL = 3
EMAP2SECPLUS_MODE_DETECT_STRUCTS = 0
EMAP2SECPLUS_MODE_DETECT_EVALUATE_STRUCTS = 1
EMAP2SECPLUS_MODE_DETECT_DNA = 2
EMAP2SECPLUS_FOLD1 = 0
EMAP2SECPLUS_FOLD2 = 1
EMAP2SECPLUS_FOLD3 = 2
EMAP2SECPLUS_FOLD4 = 3
# Emap2sec+ param constants
EMAP2SECPLUS_MODE_DETECT_EXPERIMENTAL_FOLD4 = 2
EMAP2SECPLUS_MODE_DETECT_EVALUATE_EXPERIMENTAL_FOLD4 = 3
EMAP2SECPLUS_MODE_DETECT_DNA_EXPERIMENTAL_FOLD4 = 4