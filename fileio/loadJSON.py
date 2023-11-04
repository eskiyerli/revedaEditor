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

# Load symbol and maybe later schematic from json file.
# import pathlib

import json
import pdk.process as fabproc
import pdk.pcells as pcell
from PySide6.QtCore import (
    QPoint,
    QLineF,
) 
from PySide6.QtWidgets import (QGraphicsScene,)

import revedaEditor.common.net as net
import revedaEditor.common.shape as shp
import revedaEditor.common.layoutShapes as lshp
import revedaEditor.fileio.symbolEncoder as se
import pdk.layoutLayers as laylyr
import pathlib


def createSymbolItems(item:dict, gridTuple):
    """
    Create symbol items from json file.
    """
    match item["type"]:
        case "rect":
            return createRectItem(item, gridTuple)
        case "circle":
            return createCircleItem(item, gridTuple)
        case "arc":
            return createArcItem(item, gridTuple)
        case "line":
            return createLineItem(item, gridTuple)
        case "pin":
            return createPinItem(item, gridTuple)
        case "label":
            return createLabelItem(item, gridTuple)
        case "text":
            return createTextItem(item, gridTuple)
        case "polygon":
            return createPolygonItem(item, gridTuple)
    

def createRectItem(item, gridTuple):
    """
    Create symbol items from json file.
    """
    start = QPoint(item["rect"][0], item["rect"][1])
    end = QPoint(item["rect"][2], item["rect"][3])
    rect = shp.symbolRectangle(start, end, gridTuple)  # note that we are using grid
    # values for
    # scene
    rect.setPos(
        QPoint(item["loc"][0], item["loc"][1]),
    )
    rect.angle = item["ang"]
    return rect


def createCircleItem(item, gridTuple):
    centre = QPoint(item["cen"][0], item["cen"][1])
    end = QPoint(item["end"][0], item["end"][1])
    circle = shp.symbolCircle(centre, end, gridTuple)  # note that we are using grid
    # values for
    # scene
    circle.setPos(
        QPoint(item["loc"][0], item["loc"][1]),
    )
    circle.angle = item["ang"]
    return circle


def createArcItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    end = QPoint(item["end"][0], item["end"][1])

    arc = shp.symbolArc(start, end, gridTuple)  # note that we are using grid values
    # for scene
    arc.setPos(QPoint(item["loc"][0], item["loc"][1]))
    arc.angle = item["ang"]
    return arc


def createLineItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    end = QPoint(item["end"][0], item["end"][1])

    line = shp.symbolLine(start, end, gridTuple)
    line.setPos(QPoint(item["loc"][0], item["loc"][1]))
    line.angle = item["ang"]
    return line


def createPinItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    pin = shp.symbolPin(start, item["nam"], item["pd"], item["pt"], gridTuple)
    pin.setPos(QPoint(item["loc"][0], item["loc"][1]))
    pin.angle = item["ang"]
    return pin


def createLabelItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    label = shp.symbolLabel(
        start,
        item["def"],
        item["lt"],
        item["ht"],
        item["al"],
        item["or"],
        item["use"],
        gridTuple,
    )
    label.setPos(QPoint(item["loc"][0], item["loc"][1]))
    label.angle = item["ang"]
    label.labelName = item["nam"]
    label.labelText = item["txt"]
    label.labelVisible = item["vis"]
    label.labelValue = item["val"]
    return label


def createTextItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    text = shp.text(
        start,
        item["tc"],
        item["ff"],
        item["fs"],
        item["th"],
        item["ta"],
        item["to"],
        gridTuple,
    )
    text.setPos(QPoint(item["loc"][0], item["loc"][1]))
    return text

def createPolygonItem(item, gridTuple):
    pointsList = [QPoint(point[0], point[1]) for point in item["ps"]]
    return shp.symbolPolygon(pointsList, gridTuple)

def createSymbolAttribute(item):
    if item["type"] == "attr":
        return se.symbolAttribute(item["nam"], item["def"])


def createSchematicItems(item:dict, libraryDict,  gridTuple: (int, int)):
    """
    Create schematic items from json file.
    """
    match item["type"]:
        case "symbolShape":
            libraryPath = libraryDict.get(item["lib"])
            if libraryPath is None:
                print(f'{item["lib"]} cannot be found.')
                return None
            cell = item["cell"]
            instCounter = item["ic"]
            itemShapes = list()
            symbolAttributes = dict()
            labelDict = item["ld"]
            # find the symbol file
            file = libraryPath.joinpath(cell, f'{item["view"]}.json')
            # load json file and create shapes
            with file.open(mode='r', encoding='utf-8') as temp:
                try:
                    shapes = json.load(temp)
                    for shape in shapes[1:]:
                        if shape["type"] == "rect":
                            itemShapes.append(createRectItem(shape, gridTuple))
                        elif shape["type"] == "circle":
                            itemShapes.append(createCircleItem(shape, gridTuple))
                        elif shape["type"] == "arc":
                            itemShapes.append(createArcItem(shape, gridTuple))
                        elif shape["type"] == "line":
                            itemShapes.append(createLineItem(shape, gridTuple))
                        elif shape["type"] == "pin":
                            itemShapes.append(createPinItem(shape, gridTuple))
                        elif shape["type"] == "label":
                            itemShapes.append(createLabelItem(shape, gridTuple))
                        # just recreate attributes dictionary
                        elif shape["type"] == "attr":
                            symbolAttributes[shape["nam"]] = shape["def"]
                except json.decoder.JSONDecodeError:
                    print("Error: Invalid Symbol file")
            symbolInstance = shp.schematicSymbol(itemShapes, symbolAttributes, gridTuple)
            symbolInstance.libraryName = item["lib"]
            symbolInstance.cellName = item["cell"]
            symbolInstance.counter = instCounter
            symbolInstance.instanceName = item["nam"]
            symbolInstance.angle = item.get("ang", 0)
            symbolInstance.netlistIgnore = bool(item.get("ign", 0))
            symbolInstance.viewName = item["view"]
            symbolInstance.attributes = symbolAttributes
            for labelItem in symbolInstance.labels.values():
                if labelItem.labelName in labelDict.keys():
                    labelItem.labelValue = labelDict[labelItem.labelName][0]
                    labelItem.labelVisible = labelDict[labelItem.labelName][1]
            symbolInstance.setPos(item["loc"][0], item["loc"][1])
            [labelItem.labelDefs() for labelItem in symbolInstance.labels.values()]
            return symbolInstance
        case "schematicNet":
            start = QPoint(item["st"][0], item["st"][1])
            end = QPoint(item["end"][0], item["end"][1])
            position = QPoint(item["loc"][0], item["loc"][1])
            netItem = net.schematicNet(start, end)
            netItem.name = item["nam"]
            netItem.nameSet = item["ns"]
            netItem.setPos(position)
            return netItem
        case "schematicPin":
            start = QPoint(item["st"][0], item["st"][1])
            pinName = item["pn"]
            pinDir = item["pd"]
            pinType = item["pt"]
            pinItem = shp.schematicPin(start, pinName, pinDir, pinType, gridTuple)
            pinItem.setPos(QPoint(item["loc"][0], item["loc"][1]))
            pinItem.angle = item["ang"]
            return pinItem
        case "text":
            start = QPoint(item["st"][0], item["st"][1])
            text = shp.text(
                start,
                item["tc"],
                item["ff"],
                item["fs"],
                item["th"],
                item["ta"],
                item["to"],
                gridTuple,
            )
            text.setPos(QPoint(item["loc"][0], item["loc"][1]))
            return text


class layoutItems():
    def __init__(self,scene:QGraphicsScene):
        """
        Create layout items from json file.
        """
        self.scene = scene
        self.libraryDict = scene.libraryDict
        self.rulerFont = scene.rulerFont
        self.rulerTickLength = scene.rulerTickLength
        self.gridTuple = scene.gridTuple
        self.rulerWidth = scene.rulerWidth
        self.rulerTickGap = scene.rulerTickGap
    
    def create(self, item:dict):
        match item["type"]:
            case "Inst":
                return self.createLayoutInstance(item)
            case "Pcell":
                libraryPath = pathlib.Path(self.libraryDict.get(item["lib"]))
                if libraryPath is None:
                    self.scene.logger.error(f'{item["lib"]} cannot be found.')
                    return None
                cell = item["cell"]
                viewName = item["view"]
                # open pcell json file with reference to pcell class name
                file = libraryPath.joinpath(cell, f"{viewName}.json")
                with file.open("r") as temp: # open pcell view item
                    try:
                        pcellDef = json.load(temp)
                        if pcellDef[0]["cellView"] != "pcell":
                            self.scene.logger.error("Not a pcell cell")
                        else:
                            pcellInstance = eval(f'pcell.{pcellDef[1]["reference"]}({self.gridTuple})')
                            pcellInstance(**item["params"])
                            pcellInstance.libraryName = item["lib"]
                            pcellInstance.cellName = item["cell"]
                            pcellInstance.viewName = item["view"]
                            pcellInstance.counter = item["ic"]
                            pcellInstance.instanceName = item["nam"]
                            pcellInstance.setPos(QPoint(item["loc"][0], item["loc"][1]))
                            return pcellInstance
                    except json.decoder.JSONDecodeError:
                        print("Error: Invalid PCell file")
            case "Rect":
                return self.createRectShape(item)
            case "Path":
                return self.createPathShape(item)
            case "Label":
                return self.createLabelShape(item,)
            case "Pin":
                return self.createPinShape(item)
            case "Polygon":
                return self.createPolygonShape(item)
            case "Via":
                return self.createViaArrayShape(item)
            case "Ruler":
                return self.createRulerShape(item)

    
    def createLayoutInstance(self,item):
        libraryPath = pathlib.Path(self.libraryDict.get(item["lib"]))
        if libraryPath is None:
            print(f'{item["lib"]} cannot be found.')
            return None
        cell = item["cell"]
        viewName = item["view"]
        instCounter = item["ic"]
        file = libraryPath.joinpath(cell, f"{viewName}.json")
        itemShapes = list()
        with open(file, "r") as temp:
            try:
                shapes = json.load(temp)
                for shape in shapes[1:]:
                    itemShapes.append(layoutItems(self.scene, shape))
            except json.decoder.JSONDecodeError:
                print("Error: Invalid Layout file")
        layoutInstance = lshp.layoutInstance(itemShapes, self.gridTuple)
        layoutInstance.libraryName = item["lib"]
        layoutInstance.cellName = item["cell"]
        layoutInstance.counter = instCounter
        layoutInstance.instanceName = item.get("nam", "")
        layoutInstance.setPos(item["loc"][0], item["loc"][1])
        layoutInstance.angle = item.get("ang", 0)
        layoutInstance.viewName = viewName
        return layoutInstance
    

    def createRectShape(self,item):
        start = QPoint(item["tl"][0], item["tl"][1])
        end = QPoint(item["br"][0], item["br"][1])
        layoutLayer = laylyr.pdkDrawingLayers[item["ln"]]
        rect = lshp.layoutRect(start, end, layoutLayer, self.gridTuple)
        # rect.setPos(QPoint(item["loc"][0], item["loc"][1]))
        rect.angle = item.get("ang", 0)
        return rect


    def createPathShape(self, item):
        path = lshp.layoutPath(
            QLineF(
                QPoint(item["dfl1"][0], item["dfl1"][1]),
                QPoint(item["dfl2"][0], item["dfl2"][1]),
            ),
            laylyr.pdkDrawingLayers[item["ln"]],
            self.gridTuple,
            item["w"],
            item["se"],
            item["ee"],
            item["md"],
        )
        path.name = item.get("nam", "")
        path.angle = item.get("ang", 0)
        return path

    def createRulerShape(self,item):
        ruler = lshp.layoutRuler(QLineF(
                QPoint(item["dfl1"][0], item["dfl1"][1]),
                QPoint(item["dfl2"][0], item["dfl2"][1]),
            ), self.rulerWidth, self.rulerTickGap,self.rulerTickLength, self.rulerFont, self.gridTuple, item["md"]
            )
        ruler.angle = item.get("ang", 0)
        return ruler

    def createLabelShape(self,item):
        layoutLayer = laylyr.pdkTextLayers[item["ln"]]
        item =  lshp.layoutLabel(
            QPoint(item["st"][0], item["st"][1]),
            item["lt"],
            item["ff"],
            item["fs"],
            item["fh"],
            item["la"],
            item["lo"],
            layoutLayer,
            self.gridTuple,
        )
        item.angle = item.get("ang", 0)
        return item


    def createPinShape(self,item):
        layoutLayer = laylyr.pdkPinLayers[item["ln"]]
        item = lshp.layoutPin(
            QPoint(item["tl"][0], item["tl"][1]),
            QPoint(item["br"][0], item["br"][1]),
            item["pn"],
            item["pd"],
            item["pt"],
            layoutLayer,
            self.gridTuple,
        )
        item.angle = item.get("ang", 0)
        return item


    def createPolygonShape(self,item):
        layoutLayer = laylyr.pdkDrawingLayers[item["ln"]]
        pointsList = [QPoint(point[0], point[1]) for point in item["ps"]]
        item = lshp.layoutPolygon(pointsList, layoutLayer, self.gridTuple)
        item.angle = item.get("ang", 0)
        return item


    def createViaArrayShape(self, item):
        viaDefTuple = fabproc.processVias[fabproc.processViaNames.index(item["via"]["vdt"])]
        via = lshp.layoutVia(
            QPoint(item["via"]["st"][0], item["via"]["st"][1]),
            viaDefTuple,
            item["via"]["w"],
            item["via"]["h"],
            self.gridTuple,
        )
        item =  lshp.layoutViaArray(
            QPoint(item["st"][0], item["st"][1]),
            via,
            item["sp"],
            item["xn"],
            item["yn"],
            self.gridTuple,
        )
        item.angle = item.get("ang", 0)
        return item

