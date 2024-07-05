from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from pwem.protocols import ProtImportPdb, ProtImportVolumes

from ..protocols import ProtDMM
from ..utils import assertHandle

class TestDMM(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.ds = DataSet.getDataSet('model_building_tutorial')
        setupTestProject(cls)
        cls._runImportPDB()
        cls._runImportVolume()

    @classmethod
    def _runImportPDB(cls):
        protImportPDB = cls.newProtocol(
            ProtImportPdb,
            inputPdbData=1,
            pdbFile=cls.ds.getFile('PDBx_mmCIF/emd_2513_af2.pdb'))
        cls.launchProtocol(protImportPDB)
        cls.protImportPDB = protImportPDB

    @classmethod
    def _runImportVolume(cls):
        args = {
            'filesPath': cls.ds.getFile('volumes/emd_2513.mrc'),
            'samplingRate': 1.05,
            'setOrigCoord': True,
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
        protImportVolume = cls.newProtocol(ProtImportVolumes, **args)
        cls.launchProtocol(protImportVolume)
        cls.protImportVolume = protImportVolume

    def _runDMM(self, withAf2=False):
        args = {
            "inputVolume": self.protImportVolume.outputVolume,
            "inputSeq": self.ds.getFile('Sequences/emd_2513.fasta'),
            "path_training_time": 600,
            "fragment_assembling_time": 600,
            "contourLevel": 0.01
        }
        if withAf2:
            args['af2Structure'] = self.protImportPDB.outputPdb
        protDMM = self.newProtocol(ProtDMM, **args)
        self.launchProtocol(protDMM)
        assertHandle(self.assertIsNotNone, getattr(protDMM, protDMM._OUTNAME))

    def testDMM(self):
        self._runDMM()
    
    def testDMMAf2(self):
        self._runDMM(withAf2=True)
