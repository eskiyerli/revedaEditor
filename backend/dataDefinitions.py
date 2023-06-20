#
#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#   #
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#   #
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#   #
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
from collections import namedtuple
from dataclasses import dataclass

from PySide6.QtCore import (Qt)
from PySide6.QtGui import (QColor, QPen, QBrush)

viewTuple = namedtuple('viewTuple', ['libraryName', 'cellName', 'viewName'])
cellTuple = namedtuple('cellTuple', ['libraryName', 'cellName'])
viewItemTuple = namedtuple('viewItemTuple', ['libraryItem', 'cellItem',
                                             'viewItem'])
pinNetTuple = namedtuple('pinNetTuple', ['pin', 'net', 'start'])
netTuple = namedtuple('netTuple', ['net', 'start'])
# this namedtuple is used to collect information on dashed lines.
# net is the dashed line
# index is the index of the self (schematicNet) where dashed line ends,
# 0: start,
# 1: end
# orient is True if self is horizontal, otherwise False
netEndTuple = namedtuple('netEndTuple', ['net', 'index', 'orient'])


@dataclass
class edLayer:
    name: str = ""  # edLayer name
    purpose: str= "drawing"  # edLayer purpose
    pcolor: QColor = Qt.black  # pen colour
    pwidth: int = 1  # pen width
    pstyle: Qt.PenStyle = Qt.SolidLine  # pen style
    bcolor: QColor = Qt.transparent  # brush colour
    bstyle: Qt.BrushStyle = Qt.NoBrush  # brush style
    z: int = 1  # z-index
    selectable: bool = True  # selectable
    visible: bool = True  # visible
    gdsLayer: int = 0 # gds edLayer
    datatype: int = 0# gds datatype


