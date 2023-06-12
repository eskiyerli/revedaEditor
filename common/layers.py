
#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

# Schematic and symbol editor classes
# (C) Revolution Semiconductor, 2021
from PySide6.QtGui import (QColor, QColorConstants)
from PySide6.QtCore import (Qt)
from dataclasses import dataclass

@dataclass
class layer:
    name:str = "" # layer name
    pcolor: QColor = Qt.black # pen colour
    pwidth: int = 1 # pen width
    pstyle: Qt.PenStyle = Qt.SolidLine # pen style
    bcolor: Qt.QColor = Qt.transparent # brush colour
    bpattern: Qt.BrushStyle = Qt.NoBrush # brush style
    zindex: int = 1 # z-index
    selectable: bool = True # selectable
    visible: bool = True # visible


wireLayer = layer(name="wireLayer", pcolor=QColor("cyan"), pwidth = 1,
                  pstyle = Qt.SolidLine, z=1, visible=True,
                  selectable= True)
symbolLayer = layer(name="symbolLayer", pcolor=QColor("green"), pwidth = 2,
                    z=2, pstyle= Qt.SolidLine, visible=True, selectable= True)
guideLineLayer = layer(name="guideLineLayer", pcolor=QColor("white"), pwidth =
1, z=3)

selectedWireLayer = layer(name="selectedWireLayer", pcolor=QColor("red"), pwidth = 1,
                          pstyle = Qt.SolidLine, z=3, visible=True, selectable=
                          True)
pinLayer = layer(name="pinLayer", pcolor=QColor("red"), pwidth = 1, z=2,
                 bcolor = QColor("red"), bpattern= Qt.SolidPattern,
                 visible=True, selectable= True)

#wireLayer = layer(name="wireLayer", color=QColor("cyan"), z=1, visible=True)
#symbolLayer = layer(name="symbolLayer", color=QColor("green"), z=1, visible=True)

# selectedWireLayer = layer(name="selectedWireLayer", color=QColor("red"), z=1,
#                           visible=True)
pinLayer = layer(name="pinLayer", color=QColor("red"), z=2, visible=True)
labelLayer = layer(name="labelLayer", color=QColor("yellow"), z=3, visible=True)
textLayer = layer(name="textLayer", color=QColor("white"), z=4, visible=True)
otherLayer = layer(name='otherLayer', color=QColor('white'), z=1, visible= True)
draftLayer = layer(name='draftLayer', color = QColor('gray'), z=1, visible= True)
