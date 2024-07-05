import os

from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportVolumes

from .. import Plugin
from ..protocols import ProtCryoREAD

class TestCryoREADSeq(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.ds = DataSet.getDataSet('model_building_tutorial')

        setupTestProject(cls)
        cls._runImportVolume()

    @classmethod
    def _runImportVolume(cls):
        args = {
            'filesPath': os.path.join(Plugin._cryoreadBinary, 'example', '21051.mrc'),
            'samplingRate': 1.05,
            'setOrigCoord': True,
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
        protImportVolume = cls.newProtocol(ProtImportVolumes, **args)
        cls.launchProtocol(protImportVolume)
        cls.protImportVolume = protImportVolume


    def _runCryoREAD(self):
        protCryoREAD = self.newProtocol(
            ProtCryoREAD,
            inputVolume=self.protImportVolume.outputVolume,
            inputSequence=os.path.join(Plugin._cryoreadBinary, 'example', '21051.fasta'),
            contour_level=0.6,
            resolution=3.7,
            batch_size=4,
            rule_soft=0,
            thread=1
        )

        self.launchProtocol(protCryoREAD)
        self.assertIsNotNone(getattr(protCryoREAD, protCryoREAD._OUTNAME))

    def testCryoREAD(self):
        self._runCryoREAD()
