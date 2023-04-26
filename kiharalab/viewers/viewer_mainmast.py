# **************************************************************************
# *
# * Authors:     David Herreros Calero (dherreros@cnb.csic.es)
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

import os, glob

import pyworkflow.viewer as pwviewer

import pwem.viewers as viewers
import pwem.viewers.views as vi
from pwem.viewers.viewer_chimera import ChimeraView

from ..protocols.protocol_mainmast_segment_map import ProtMainMastSegmentMap

class MainMastViewer(pwviewer.Viewer):
    """
    Wrapper to visualize different outputs of MAINMASTseg software.
    """
    _environments = [pwviewer.DESKTOP_TKINTER]
    _targets = [ProtMainMastSegmentMap]

    def __init__(self, **kwargs):
        pwviewer.Viewer.__init__(self, **kwargs)
        self._views = []

    def _getObjView(self, obj, fn, viewParams={}):
        return vi.ObjectView(
            self._project, obj.strId(), fn, viewParams=viewParams)

    def _visualize(self, obj, **kwargs):
        views = []
        cls = type(obj)

        if issubclass(cls, ProtMainMastSegmentMap):
            filePath = self.chimeraViewFile()
            views.append(ChimeraView(filePath))

        return views

    def chimeraViewFile(self, axis=False):
        """
        This function creates the chimera file needed to visualize the results.
        """
        outPath = self.protocol._getExtraPath()
        filePath = os.path.abspath(self.protocol._getExtraPath('chimera.cxc'))
        f = open(filePath, "w")

        # Adding all result volumes
        for idx, segmentation in enumerate(glob.glob(os.path.join(outPath, 'region*.mrc'))):
            volumeIdx = idx + 1
            f.write('open %s\n' % os.path.abspath(segmentation))
            f.write('volume #%d step 1 level %f\n' % (volumeIdx, self.protocol.threshold.get()))

        # Adding axis to file if requested
        if axis:
            builFileName = os.path.abspath(self.protocol._getExtraPath("axis.bild"))
            viewers.viewer_chimera.Chimera.createCoordinateAxisFile(self.protocol.inputVolume.get().getDim()[0],
                bildFileName=os.path.abspath(self.protocol._getExtraPath("axis.bild")),
                sampling=self.protocol.inputVolume.get().getSamplingRate())
            f.write('open %s\n' % builFileName)

            # Setting center of coordinates for the axis
            f.write('cofr 0,0,0\n')
            
        f.close()
        return filePath