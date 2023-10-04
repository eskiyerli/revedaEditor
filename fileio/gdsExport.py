#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#   Add-ons and extensions developed for this software may be distributed
#   under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#
import gdstk
import pdk.layoutLayers as laylyr
import revedaEditor.common.shape as shp
import pathlib

class gdsExporter:
    def __init__(self, cellname:str, items:list, outputFileObj:str):
        self.cellname = cellname
        self.items = items
        self.outputFileObj = outputFileObj


    def gds_export(self):
        self.outputFileObj.parent.mkdir(parents=True, exist_ok=True)
        lib = gdstk.Library()
        cell = lib.new_cell(self.cellname)
        for item in self.items:
            self.createCells(cell, item)
        lib.write_gds(self.outputFileObj)

    def createCells(self, cell,item):
        match type(item):
            case shp.layoutCell:
                self.createCells(cell, item)
            case shp.layRect:
                sceneRect = item.mapRectToScene(item.rect).toRect()
                rect = gdstk.rectangle(sceneRect.topLeft().toTuple(),
                                       sceneRect.bottomRight(
                                       ).toTuple(), item.layer.gdsLayer,
                                       item.layer.datatype)
                cell.add(rect)
