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

from ..protocols import ProtDAQValidation
import pyworkflow.viewer as pwviewer
from pwem import splitRange
from pwem.viewers.viewer_chimera import Chimera, ChimeraView
from pwem.wizards import ColorScaleWizardBase
import pyworkflow.protocol.params as params

import pyworkflow.gui.plotter as plotter
from pwem.viewers.plotter import EmPlotter

class DAQViewer(pwviewer.ProtocolViewer):
  """ Viewer for plot the histogram of per-residue RMSD of a SetOfAtomStruct. """
  _label = 'DAQ score viewer'
  _targets = [ProtDAQValidation]
  _environments = [pwviewer.DESKTOP_TKINTER, pwviewer.WEB_DJANGO]

  def __init__(self, **kwargs):
    pwviewer.ProtocolViewer.__init__(self, **kwargs)

  def _defineParams(self, form):
    form.addSection(label='Visualization of DAQ score')
    ColorScaleWizardBase.defineColorScaleParams(form, defaultLowest=-1, defaultHighest=1, defaultIntervals=21,
                                                defaultColorMap='RdBu_r')
    group = form.addGroup('Visualization in Chimera')
    group.addParam('displayStruct', params.LabelParam,
                   label='Display output AtomStruct RMSD: ',
                   help='Display the AtomStruct coloured by the DAQ score per residue.\n'
                        'The color palette, intervals, lowest and highest values can be chosen in the '
                        'parameters above.\n The highest the value, the better the model.'
                   )
    group = form.addGroup('Histogram visualization')
    group.addParam('displayHistogram', params.LabelParam,
                   label='Display histogram: ',
                   help='Display the AtomStruct coloured by the DAQ score per residue.\n'
                        'The color palette, intervals, lowest and highest values can be chosen in the '
                        'parameters above.\n The highest the value, the better the model.'
                   )

  def _getVisualizeDict(self):
    return {
      'displayStruct': self._showChimera,
      'displayHistogram': self._showHistogram,
    }

  def _showChimera(self, paramName=None):
    obj = self.protocol
    chimScript = obj._getExtraPath('chimera_script.py')
    f = open(chimScript, "w")
    f.write("from chimerax.core.commands import run\n")
    f.write("from chimerax.graphics.windowsize import window_size\n")
    f.write("from PyQt5.QtGui import QFontMetrics\n")
    f.write("from PyQt5.QtGui import QFont\n")

    f.write("run(session, 'cd %s')\n" % os.getcwd())
    f.write("run(session, 'cofr 0,0,0')\n")  # set center of coordinates

    # building coordinate axes
    _inputVol = obj.outputAtomStruct.getVolume()
    if _inputVol is not None:
      dim, sampling = _inputVol.getDim()[0], _inputVol.getSamplingRate()

      f.write("run(session, 'open %s')\n" % _inputVol.getFileName())
      x, y, z = _inputVol.getOrigin(force=True).getShifts()
      f.write("run(session, 'volume #%d style surface voxelSize %f')\n" % (1, sampling))
      f.write("run(session, 'volume #%d origin %0.2f,%0.2f,%0.2f')\n" % (1, x, y, z))
    else:
      dim, sampling = 150., 1.

    tmpFileName = os.path.abspath(obj._getExtraPath("axis_input.bild"))
    Chimera.createCoordinateAxisFile(dim,
                                     bildFileName=tmpFileName,
                                     sampling=sampling)
    f.write("run(session, 'open %s')\n" % tmpFileName)

    # Open atomstruct and color it by the bfactor (which is actually the DAQ score)
    f.write("run(session, 'open %s')\n" % obj.outputAtomStruct.getFileName())

    stepColors, colorList = self.getColors()
    scolorStr = ''
    for step, color in zip(stepColors, colorList):
      scolorStr += '%s,%s:' % (step, color)
    scolorStr = scolorStr[:-1]
    f.write("run(session, 'color bfactor palette {} range {},{}')\n".
            format(scolorStr, self.lowest.get(), self.highest.get()))

    f.write(self.generateColorLegend(stepColors, colorList))
    f.write("run(session, 'view')\n")

    f.close()

    view = ChimeraView(chimScript)
    return [view]

  def _showHistogram(self, paramName=None):
      prot = self.protocol

      self.plotter = EmPlotter(x=1, y=1, windowTitle='DAQ scores', figure='active')
      daqDic = prot.parseDAQScores(prot.outputAtomStruct.getFileName())
      daqValues = list(daqDic.values())

      a = self.plotter.createSubPlot("Per-residue DAQ", "DAQ score", "Count")
      low, high = self.lowest.get(), self.highest.get()
      a.set_xlim([low, high])

      n = 2
      mult = 10 ** n
      stepSize = int(round(high / self.intervals.get(), n) * mult)
      bins = [i / mult for i in range(int(low * mult), int(high * mult), stepSize)]
      _, _, bars = a.hist(daqValues, bins=bins, linewidth=1, label="Map", rwidth=0.9)
      for bar in bars:
        if bar.get_x() < ((high - low) / 4) + low:
          bar.set_facecolor('red')
        elif bar.get_x() < (3 * (high - low) / 4) + low:
          bar.set_facecolor('grey')
        else:
          bar.set_facecolor('blue')
      a.grid(True)
      return [self.plotter]


  ####################### UTILS ###################
  def getColors(self):
    stepColors = splitRange(self.highest.get(), self.lowest.get(),
                            splitNum=self.intervals.get())
    colorList = plotter.getHexColorList(len(stepColors), self.colorMap.get())
    return stepColors, colorList

  def generateColorLegend(self, stepColors, colorList):
      '''Return a string to write in the file for getting the color legend'''
      colorStr = ''
      colorStr += "v = session.main_view\n"
      colorStr += "vx,vy=v.window_size\n"

      # Calculate heights and Y positions: font, scale height and firstY
      ptSize = 12  # default size chimera font
      colorStr += 'font = QFont("Ariel", %d)\n' % ptSize
      colorStr += 'f = QFontMetrics(font)\n'
      colorStr += '_height =  1 * f.height()/vy\n'  # Font height
      colorStr += '_half_scale_height = _height * %f/2\n' % len(stepColors) # Full height of the scale
      colorStr += "_firstY= 0.5 + _half_scale_height\n"  # Y location for first label

      colorStr += "step = "
      # place labels in right place
      # unfortunately chimera has no colorbar
      labelCount = 0
      for step, color in zip(stepColors, colorList):
        if step > 99.9:
          step = "%.2f" % step
        else:
          step = "{:05.2f}".format(step)
        command = 'run(session, "2dlabel text ' + step + \
                  ' bgColor ' + color + \
                  ' xpos 0.01 ypos %f' + \
                  ' size ' + str(ptSize) + \
                  '" % ' + \
                  '(_firstY - %f*_height))\n' % (labelCount)

        colorStr += command
        labelCount += 1
      return colorStr


