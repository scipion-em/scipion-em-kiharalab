# Scipion em imports
from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportVolumes

# Plugin imports
from ..protocols import ProtCryoREAD

class TestCryoREAD(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.ds = DataSet.getDataSet('model_building_tutorial')

        setupTestProject(cls)
        cls._runImportVolume()

    @classmethod
    def _runImportVolume(cls):
        args = {
            'filesPath': cls.ds.getFile('volumes/21051.mrc'),
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
