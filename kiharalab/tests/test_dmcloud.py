import os

from pyworkflow.tests import BaseTest, setupTestProject
from pwem.protocols import ProtImportVolumes, ProtImportPdb

from ..protocols import ProtDMcloud
from ..utils import assertHandle


class TestDMcloud(BaseTest):
    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls._runImportVolume()
        cls._runImportPDBModel()

    @classmethod
    def _runImportVolume(cls):
        protImportVolume = cls.newProtocol(ProtImportVolumes,
                                           importFrom=1,
                                           emdbId='0202')
        cls.launchProtocol(protImportVolume)
        cls.protImportVolume = protImportVolume

    @classmethod
    def _runImportPDBModel(cls):
        protImportPDB1 = cls.newProtocol(
            ProtImportPdb,
            inputPdbData=0,
            pdbId='6HD7',
        )
        cls.launchProtocol(protImportPDB1)
        cls.protImportPDB1 = protImportPDB1

    def _runDMcloud(self):
        protDMcloud = self.newProtocol(ProtDMcloud,
                                       inputVolume=self.protImportVolume.outputVolume,
                                       inputStructure=self.protImportPDB1.outputPdb,
                                       contour_level=0.0995)
        self.launchProtocol(protDMcloud)
        assertHandle(self.assertIsNotNone, getattr(protDMcloud, protDMcloud.outputStructure))

    def test(self):
        self._runDMcloud()

