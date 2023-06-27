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

from PySide6.QtCore import (QPoint, )  # QtCore

import revedaEditor.common.net as net
import revedaEditor.common.shape as shp
import revedaEditor.fileio.symbolEncoder as se
import pdk.layoutLayers as laylyr
import pathlib


def createSymbolItems(item, gridTuple):
    """
    Create symbol items from json file.
    """
    if item["type"] == "rect":
        return createRectItem(item,gridTuple)
    elif item["type"] == "circle":
        return createCircleItem(item,gridTuple)
    elif item["type"] == "arc":
        return createArcItem(item, gridTuple)
    elif item["type"] == "line":
        return createLineItem(item, gridTuple)
    elif item["type"] == "pin":
        return createPinItem(item, gridTuple)
    elif item["type"] == "label":
        return createLabelItem(item, gridTuple)


def createRectItem(item, gridTuple):
    """
    Create symbol items from json file.
    """
    start = QPoint(item["rect"][0], item["rect"][1])
    end = QPoint(item["rect"][2], item["rect"][3])
    rect = shp.rectangle(start, end, gridTuple)  # note that we are using grid
    # values for
    # scene
    rect.setPos(QPoint(item["loc"][0], item["loc"][1]), )
    rect.angle = item["ang"]
    return rect


def createCircleItem(item, gridTuple):
    centre = QPoint(item["cen"][0], item["cen"][1])
    end = QPoint(item["end"][0], item["end"][1])
    circle = shp.circle(centre, end, gridTuple)  # note that we are using grid
    # values for
    # scene
    circle.setPos(QPoint(item["loc"][0], item["loc"][1]), )
    circle.angle = item["ang"]
    return circle


def createArcItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    end = QPoint(item["end"][0], item["end"][1])

    arc = shp.arc(start, end, gridTuple)  # note that we are using grid values
    # for scene
    arc.setPos(QPoint(item["loc"][0], item["loc"][1]))
    arc.angle = item["ang"]
    return arc


def createLineItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    end = QPoint(item["end"][0], item["end"][1])

    line = shp.line(start, end, gridTuple)
    line.setPos(QPoint(item["loc"][0], item["loc"][1]))
    line.angle = item["ang"]
    return line


def createPinItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    pin = shp.pin(start, item["nam"], item["pd"], item["pt"], gridTuple)
    pin.setPos(QPoint(item["loc"][0], item["loc"][1]))
    pin.angle = item["ang"]
    return pin


def createLabelItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    label = shp.label(start,  item["def"], item["lt"], item["ht"],
                      item["al"], item["or"], item["use"], gridTuple)
    label.setPos(QPoint(item["loc"][0], item["loc"][1]))
    label.angle = item["ang"]
    label.labelName = item["nam"]
    label.labelText = item["txt"]
    label.labelVisible = item["vis"]
    label.labelValue = item["val"]
    return label


def createTextItem(item,gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    text = shp.text(start, item['tc'], item['ff'], item['fs'],
                    item['th'], item['ta'], item['to'], gridTuple)
    text.setPos(QPoint(item["loc"][0], item["loc"][1]))
    return text


def createSymbolAttribute(item):
    if item["type"] == "attr":
        return se.symbolAttribute(item["nam"], item["def"])


def createSchematicItems(item, libraryDict, viewName: str, gridTuple: (int, int)):
    """
    Create schematic items from json file.
    """
    if item["type"] == "symbolShape":
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
        file = libraryPath.joinpath(cell, viewName + ".json")
        # load json file and create shapes
        with open(file, "r") as temp:
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
        symbolInstance = shp.symbolShape(itemShapes,
                                         symbolAttributes, gridTuple)
        symbolInstance.libraryName = item["lib"]
        symbolInstance.cellName = item["cell"]
        symbolInstance.counter = instCounter
        symbolInstance.instanceName = item["nam"]
        symbolInstance.angle = item.get("ang", 0)
        symbolInstance.netlistIgnore = bool(item.get("ign",0))
        symbolInstance.viewName = viewName
        symbolInstance.attributes = symbolAttributes
        for labelItem in symbolInstance.labels.values():
            if labelItem.labelName in labelDict.keys():
                labelItem.labelValue = labelDict[labelItem.labelName][0]
                labelItem.labelVisible = labelDict[labelItem.labelName][1]
        symbolInstance.setPos(item["loc"][0], item["loc"][1])
        return symbolInstance


def createSchematicNets(item):
    """
    Create schematic items from json file.
    """
    if item["type"] == "schematicNet":
        start = QPoint(item["st"][0], item["st"][1])
        end = QPoint(item["end"][0], item["end"][1])
        position = QPoint(item["loc"][0], item["loc"][1])
        netItem = net.schematicNet(start, end)
        netItem.name = item["nam"]
        netItem.nameSet = item["ns"]
        netItem.setPos(position)
        return netItem


def createSchematicPins(item, gridTuple):
    """
    Create schematic items from json file.
    """
    if item["type"] == "schematicPin":
        start = QPoint(item["st"][0], item["st"][1])
        pinName = item["pn"]
        pinDir = item["pd"]
        pinType = item["pt"]
        pinItem = shp.schematicPin(start, pinName, pinDir, pinType, gridTuple)
        pinItem.setPos(QPoint(item["loc"][0], item["loc"][1]))
        pinItem.angle = item["ang"]
        return pinItem


def createLayoutItems(item, libraryDict: dict, gridTuple: (int, int)):
    """
    Create layout items from json file.
    """
    match item["type"]:
        case "layoutCell":
            libraryPath = pathlib.Path(libraryDict.get(item["lib"]))
            if libraryPath is None:
                print(f'{item["lib"]} cannot be found.')
                return None
            cell = item["cell"]
            viewName = item["view"]
            instCounter = item["ic"]
            file = libraryPath.joinpath(cell, f'{viewName}.json')
            itemShapes = list()
            with open(file, "r") as temp:
                try:
                    shapes = json.load(temp)
                    for shape in shapes[1:]:
                        if shape["type"] == "layoutCell":
                            itemShapes.append(createLayoutItems(shape,
                                                                libraryDict,
                                                                gridTuple))
                        elif shape['type'] == 'layRect':
                            itemShapes.append(createRectShape(shape, gridTuple))

                except json.decoder.JSONDecodeError:
                    print("Error: Invalid Layout file")
            layoutInstance = shp.layoutCell(itemShapes, gridTuple)
            layoutInstance.libraryName = item["lib"]
            layoutInstance.cellName = item["cell"]
            layoutInstance.counter = instCounter
            layoutInstance.instanceName = item["nam"]
            layoutInstance.setPos(item["loc"][0], item["loc"][1])
            layoutInstance.viewName = viewName
            return layoutInstance
        case "layRect":
            return createRectShape(item, gridTuple)


def createRectShape(item, gridTuple:tuple[int,int]):
        start = QPoint(item["rect"][0], item["rect"][1])
        end = QPoint(item["rect"][2], item["rect"][3])
        layoutLayer = laylyr.pdkLayoutLayers[item["lnum"]]
        rect = shp.layRect(start, end, layoutLayer, gridTuple)
        rect.setPos(QPoint(item["loc"][0], item["loc"][1]))
        rect.angle = item["ang"]
        return rect

