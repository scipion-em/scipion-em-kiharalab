# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors: Blanca Pueche (blanca.pueche@cnb.csic.es)
# *
# * Purdue University - Kihara Lab
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
# * All comments concerning this program package may be sent to the
# * e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os, shutil

from pyworkflow.protocol import params
from pyworkflow.utils import Message
from pwem.protocols import EMProtocol
from pwem.objects import AtomStruct
from pwem.convert import Ccp4Header
from pwem.convert.atom_struct import toCIF, AtomicStructHandler, addScipionAttribute
from pwem.emlib.image import ImageHandler
from glob import glob
import os

from Bio.PDB import PDBParser, Structure, Model, PDBIO


from kiharalab import Plugin

class ProtDMcloud(EMProtocol):
    """
    Executes DMcloud software to construct full atomic structure of protein and DNA/RNA.
    """
    stepsExecutionMode = params.STEPS_PARALLEL
    _label = 'DMcloud'

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """Define parameters for the CryoREAD protocol."""
        form.addHidden(params.USE_GPU, params.BooleanParam, default=True,
                       label="Use GPU for execution: ",
                       help="This protocol has both CPU and GPU implementation. Select the one you want to use.")

        form.addHidden(params.GPU_LIST, params.StringParam, default='0', label="Choose GPU IDs",
                       help="Add a list of GPU devices that can be used")

        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputVolume', params.PointerParam,
                      pointerClass='Volume', allowsNull=False,
                      label="Input 3D cryo-EM map: ",
                      help='Select the 3D cry-EM map to be analyzed in .map or .mrc format.')

        form.addParam('inputStructure', params.PointerParam, pointerClass='AtomStruct', allowsNull=False,
                      label="Input structure: ",
                      help='Select the input structure.')

        group = form.addGroup('Parameters')
        group.addParam('contour_level', params.FloatParam, default=0.0, label='Contour level: ',
                       help='Contour level for input map.')
        group.addParam('pLDDT', params.FloatParam, default=0.50, label='pLDDT threshold: ',
                       help='pLDDT filtering. If negative, use all points. Set to 100 for all points.')
        group.addParam('cluster_size', params.IntParam, default=200, label='Minimum cluster size: ', expertLevel=params.LEVEL_ADVANCED,
                       help='Minimum Size of fitting')

        form.addParallelSection(threads=4, mpi=1)


    # --------------------------- STEPS functions ----------------------------------
    def _insertAllSteps(self):
        """Insert processing steps for the protocol."""
        self._insertFunctionStep('convertInputStep')
        self._insertFunctionStep('dmCloudStep')
        self._insertFunctionStep('createOutputStep')

    def convertInputStep(self):
        ext = os.path.splitext(self.getVolumeFile())[1]
        if ext not in ['.map', '.mrc']:
            print('Input file format is not correct. Please check.')

        inVol = self._getInputVolume()
        inVolFile, inVolSR = inVol.getFileName(), inVol.getSamplingRate()

        # Convert volume to mrc
        mrcFile = self._getTmpPath('inpVolume.mrc')
        ImageHandler().convert(inVolFile, mrcFile)
        Ccp4Header.fixFile(mrcFile, mrcFile, inVol.getOrigin(force=True).getShifts(),
                           inVolSR, Ccp4Header.START)


        # Volume header fixed to have correct origin
        Ccp4Header.fixFile(mrcFile, self.getLocalVolumeFile(), inVol.getOrigin(force=True).getShifts(), inVolSR,
                           Ccp4Header.ORIGIN)

    def dmCloudStep(self):
        inputFilePath = self.getLocalVolumeFile()
        outDir = os.path.abspath(self._getPath('predictions'))

        envActivationCommand = f"{Plugin.getCondaActivationCmd()} {Plugin.getProtocolActivationCommand('dmcloud')}"
        fullProgram = f'{envActivationCommand} && python DMcloud.py'
        threads = self.numberOfThreads.get()

        args = [
            '--Source', str(os.path.abspath(self.inputStructure.get().getFileName())),
            '--Target', str(os.path.abspath(inputFilePath)),
            '--OutPath', str(outDir),
            '--contour', self.contour_level.get(),
            '--MinClstSize', self.cluster_size.get(),
            '--pLDDT', self.pLDDT.get(),
            '--Threads', threads
        ]
        if getattr(self, params.USE_GPU).get():
            args += ['--diffusion_gpu', str(self.getGPUIds())]
        self.runJob(fullProgram, args, cwd=Plugin._dmcloudBinary)

    def createOutputStep(self):
        selectedDir = os.path.join(self._getPath("predictions"), "Selected")
        filledFiles = sorted(glob(os.path.join(selectedDir, "Filled_*.pdb")))
        print(filledFiles)

        if not filledFiles:
            raise Exception("No Filled_*.pdb files were generated.")
        parser = PDBParser(QUIET=True)
        merged = Structure.Structure("DMCloud")
        for i, pdbFile in enumerate(filledFiles):
            structure = parser.get_structure(f"fit_{i}", pdbFile)

            model = next(structure.get_models()).copy()
            model.id = i
            merged.add(model)
        outputPdb = self._getPath("dmcloud_output.pdb")
        io = PDBIO()
        io.set_structure(merged)
        io.save(outputPdb)

        outStruct = AtomStruct(filename=outputPdb)
        self._defineOutputs(outputStructure=outStruct)

    # --------------------------- INFO functions -----------------------------------
    def _validate(self):
        errors = []

        return errors

    def _summary(self):
        summary = []
        return summary

    def _methods(self):
        methods = []
        return methods
    # --------------------------- UTILS functions -----------------------------------
    def _getInputVolume(self):
        return self.inputVolume.get()

    def getVolumeFile(self):
        return os.path.abspath(self._getInputVolume().getFileName())

    def getLocalVolumeFile(self):
        oriName = os.path.basename(os.path.splitext(self.getVolumeFile())[0])
        localPath = self._getExtraPath(f'{oriName}_{self.getObjId()}.mrc')
        return os.path.abspath(localPath)

    def getGPUIds(self):
        return getattr(self, params.GPU_LIST).get().split(',')[0].strip()

    def parseCryoScores(self, pdbFile):
        cryoDic = {}
        with open(pdbFile) as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    resId = f'{line[21].strip()}:{line[22:26].strip()}'
                    if resId not in cryoDic:
                        cryoScore = line[60:66].strip()
                        cryoDic[resId] = cryoScore
        return cryoDic
