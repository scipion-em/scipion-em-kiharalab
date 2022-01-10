# **************************************************************************
# *
# * Authors:     Daniel Del Hoyo (ddelhoyo@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
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
import os

from pwem.viewers.viewer_chimera import chimeraScriptFileName, Chimera, ChimeraView
from ..protocols import ProtDAQValidation
import pyworkflow.viewer as pwviewer

class viewerDAQ(pwviewer.Viewer):
  _targets = [ProtDAQValidation]

  def __init__(self, **kwargs):
    super().__init__(**kwargs)

  def visualize(self, obj, **kwargs):
      chimScript = obj._getExtraPath(chimeraScriptFileName)
      f = open(chimScript, "w")
      f.write('cd %s\n' % os.getcwd())
      f.write("cofr 0,0,0\n")  # set center of coordinates

      # building coordinate axes
      _inputVol = obj.outputAtomStruct.getVolume()
      if _inputVol is not None:
        dim, sampling = _inputVol.getDim()[0], _inputVol.getSamplingRate()

        f.write("open %s\n" % _inputVol.getFileName())
        x, y, z = _inputVol.getOrigin(force=True).getShifts()
        f.write("volume #%d style surface voxelSize %f\nvolume #%d origin "
                "%0.2f,%0.2f,%0.2f\n"
                % (1, sampling, 1, x, y, z))
      else:
        dim, sampling = 150., 1.

      tmpFileName = os.path.abspath(obj._getExtraPath("axis_input.bild"))
      Chimera.createCoordinateAxisFile(dim,
                                       bildFileName=tmpFileName,
                                       sampling=sampling)
      f.write("open %s\n" % tmpFileName)

      #Open atomstruct and color it by the bfactor (which is actually the DAQ score)
      f.write("open %s\n" % obj.outputAtomStruct.getFileName())
      f.write("color bfactor palette redblue range -1,1")
      f.close()

      ChimeraView(chimScript).show()
