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

# from hashlib import new
import inspect
import json
import os
# from hashlib import new
import pathlib
import time
from typing import List, Dict, Any, Union

# import numpy as np
from PySide6.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QRectF,
    Qt,
    QLineF,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QTransform,
    QPen,
    QFontDatabase,
    QFont,
)
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGraphicsSceneMouseEvent,
    QGraphicsLineItem,
    QGraphicsRectItem,
)
from dotenv import load_dotenv

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.undoStack as us
import revedaEditor.common.layoutShapes as lshp  # import layout shapes
import revedaEditor.fileio.layoutEncoder as layenc
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.propertyDialogues as pdlg
from revedaEditor.gui.editorScene import editorScene

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.layoutLayers as laylyr
    import pdk.process as fabproc
    import pdk.pcells as pcells
else:
    import defaultPDK.layoutLayers as laylyr
    import defaultPDK.process as fabproc
    import defaultPDK.pcells as pcells


class layoutScene(editorScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.selectEdLayer = laylyr.pdkAllLayers[0]
        self.layoutShapes = [
            "Inst",
            "Rect",
            "Path",
            "Label",
            "Via",
            "Pin",
            "Polygon",
            "Pcell",
            "Ruler",
        ]
        # draw modes
        self.editModes = ddef.layoutModes(
            selectItem=False,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPath=False,
            drawPin=False,
            drawArc=False,
            drawPolygon=False,
            addLabel=False,
            addVia=False,
            drawRect=False,
            drawLine=False,
            drawCircle=False,
            drawRuler=False,
            stretchItem=False,
            addInstance=False,
        )
        self.editModes.setMode("selectItem")
        self.selectModes = ddef.layoutSelectModes(
            selectAll=True,
            selectPath=False,
            selectInstance=False,
            selectVia=False,
            selectPin=False,
            selectLabel=False,
            selectText=False,
        )
        self.newInstance = None
        self.layoutInstanceTuple = None
        self._scale = fabproc.dbu
        self.itemCounter = 0
        self._newPath = None
        self._stretchPath = None
        self.newPathTuple = None
        self.draftLine = None
        self.m45Rotate = QTransform()
        self.m45Rotate.rotate(-45)
        self._newPin = None
        self.newPinTuple = None
        self.newLabelTuple = None
        self._newLabel = None
        self._newRect = None
        self._newPolygon = None
        self.arrayViaTuple = None
        self._singleVia = None
        self._arrayVia = None
        self._polygonGuideLine = None
        self._newRuler = None
        self._selectionRectItem = None
        self.rulersSet = set()
        self.rulerFont = self.setRulerFont(12)
        self.rulerFont.setKerning(False)
        self.rulerTickGap = fabproc.dbu
        self.rulerTickLength = 10
        self.rulerWidth = 2



    @property
    def drawMode(self):
        return any(
            (
                self.editModes.drawPath,
                self.editModes.drawPin,
                self.editModes.drawArc,
                self.editModes.drawPolygon,
                self.editModes.drawRect,
                self.editModes.drawCircle,
                self.editModes.drawRuler,
            )
        )

    # Order of drawing
    # 1. Rect
    # 2. Path
    # 3. Pin
    # 4. Label
    # 5. Via/Contact
    # 6. Polygon
    # 7. Add instance
    # 8. select item/s
    # 9. rotate item/s

    @staticmethod
    def toLayoutCoord(point: Union[QPoint | QPointF]) -> QPoint | QPointF:
        """
        Converts a point in scene coordinates to layout coordinates by dividing it to
        fabproc.dbu.
        """
        point /= fabproc.dbu
        return point

    @staticmethod
    def toSceneCoord(point: Union[QPoint | QPointF]) -> QPoint | QPointF:
        """
        Converts a point in layout coordinates to scene coordinates by multiplying it with
        fabproc.dbu.
        """
        point *= fabproc.dbu
        return point

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse press event.

        Args:
            mouse_event: The mouse event object.

        Returns:
            None
        """
        # Store the mouse press location
        self.mousePressLoc = mouse_event.scenePos().toPoint()
        # Call the base class mouse press event
        super().mousePressEvent(mouse_event)
        try:
            # Get the keyboard modifiers
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                pass

        except Exception as e:
            self.logger.error(f"mouse press error: {e}")


    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse move event.

        Args:
            mouse_event (QGraphicsSceneMouseEvent): The mouse event object.

        Returns:
            None
        """
        # Get the current mouse position
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        # Call the parent class's mouseMoveEvent method
        super().mouseMoveEvent(mouse_event)
        # Get the keyboard modifiers
        modifiers = QGuiApplication.keyboardModifiers()

        # Handle drawing path mode
        if self.editModes.drawPath and self._newPath is not None:
            self._newPath.draftLine = QLineF(
                self._newPath.draftLine.p1(), self.mouseMoveLoc
            )
        elif self.editModes.drawRect and self._newRect:
            self._newRect.end = self.mouseMoveLoc
        # Handle drawing pin mode with no new pin
        elif self.editModes.drawPin:
            if self._newPin is not None:
                self._newPin.end = self.mouseMoveLoc
        elif self.editModes.addLabel and self._newLabel is not None:
            self._newLabel.start = self.mouseMoveLoc
        elif self.editModes.addInstance and self.newInstance is not None:
            self.newInstance.setPos(self.mouseMoveLoc - self.newInstance.start)
        # Handle drawing polygon mode
        elif self.editModes.drawPolygon and self._newPolygon is not None:
            self._polygonGuideLine.setLine(
                QLineF(self._newPolygon.points[-1], self.mouseMoveLoc)
            )
        elif self.editModes.drawRuler and self._newRuler is not None:
            self._newRuler.draftLine = QLineF(
                self._newRuler.draftLine.p1(), self.mouseMoveLoc
            )
        # Handle adding via mode with array via tuple
        elif self.editModes.addVia and self._arrayVia is not None:
            self._arrayVia.setPos(self.mouseMoveLoc - self._arrayVia.start)

        elif self.editModes.stretchItem and self._stretchPath is not None:
            self._stretchPath.draftLine = QLineF(
                self._stretchPath.draftLine.p1(), self.mouseMoveLoc
            )
        elif self.editModes.selectItem and self._selectionRectItem is not None:
            self._selectionRectItem.setRect(QRect(self.mouseReleaseLoc, self.mouseMoveLoc))
        # Calculate the cursor position in layout units
        cursorPosition = self.toLayoutCoord(self.mouseMoveLoc - self.origin)

        # Show the cursor position in the status line
        self.statusLine.showMessage(
            f"Cursor Position: ({cursorPosition.x()}, {cursorPosition.y()})"
        )

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawPath:
                    self.editorWindow.messageLine.setText("Path mode")
                    if self._newPath:
                        if self._newPath.draftLine.isNull():
                            self.undoStack.removeLastCommand()
                        self._newPath = None

                    # Create a new path
                    self._newPath = lshp.layoutPath(
                        QLineF(self.mousePressLoc, self.mousePressLoc),
                        self.newPathTuple.layer,
                        self.newPathTuple.width,
                        self.newPathTuple.startExtend,
                        self.newPathTuple.endExtend,
                        self.newPathTuple.mode,
                    )
                    self._newPath.name = self.newPathTuple.netName
                    self.addUndoStack(self._newPath)
                elif self.editModes.drawRect:
                    self.editorWindow.messageLine.setText("Rectangle mode.")
                    # Create a new rectangle
                    if self._newRect:
                        if self._newRect.rect.isNull():
                            self.undoStack.removeLastCommand()
                        self._newRect = None
                    self._newRect = lshp.layoutRect(
                        self.mouseReleaseLoc,
                        self.mouseReleaseLoc,
                        self.selectEdLayer,
                    )
                    self.addUndoStack(self._newRect)
                elif self.editModes.drawPin:
                    self.editorWindow.messageLine.setText("Pin mode.")
                    # Create a new pin
                    if self._newPin:
                        if self._newPin.rect.isNull():
                            self.undoStack.removeLastCommand()
                        else:
                            self.editModes.setMode('addLabel')
                            self._newLabel = lshp.layoutLabel(
                                self.mouseReleaseLoc, *self.newLabelTuple
                            )
                            self.addUndoStack(self._newLabel)
                        self._newPin = None
                    self._newPin = lshp.layoutPin(
                        self.mouseReleaseLoc, self.mouseReleaseLoc, *self.newPinTuple
                    )
                    self.addUndoStack(self._newPin)
                elif self.editModes.addLabel:
                    if self._newLabel is not None:
                        self.newLabelTuple = None
                        self._newLabel = None
                    self._newLabel = lshp.layoutLabel(
                        self.mouseReleaseLoc, *self.newLabelTuple
                    )
                    self.addUndoStack(self._newLabel)
                elif self.editModes.addInstance:
                    if self.newInstance is not None:
                        self.newInstance = None
                        self.layoutInstanceTuple = None
                    if self.layoutInstanceTuple:
                        self.addNewInstance()
                        self.addUndoStack(self.newInstance)
                        self.newInstance.setPos(self.mouseReleaseLoc - self.newInstance.start)
                elif self.editModes.drawPolygon:
                    if self._newPolygon is None:
                        # Create a new polygon
                        self._newPolygon = lshp.layoutPolygon(
                            [self.mouseReleaseLoc, self.mouseReleaseLoc],
                            self.selectEdLayer,
                        )
                        self.addUndoStack(self._newPolygon)
                        # Create a guide line for the polygon
                        self._polygonGuideLine = QGraphicsLineItem(
                            QLineF(
                                self._newPolygon.points[-2], self._newPolygon.points[-1]
                            )
                        )
                        self._polygonGuideLine.setPen(
                            QPen(QColor(255, 255, 0), 2, Qt.DashLine)
                        )
                        self._polygonGuideLine.pen().setCosmetic(False)
                        self.addUndoStack(self._polygonGuideLine)
                    else:
                        self._newPolygon.addPoint(self.mouseReleaseLoc)

                elif self.editModes.drawRuler:
                    if self._newRuler:
                        if self._newRuler.draftLine.isNull():
                            self.undoStack.removeLastCommand()
                        self._newRuler = None
                    self._newRuler = lshp.layoutRuler(
                        QLineF(self.mouseReleaseLoc, self.mouseReleaseLoc),
                        width=self.rulerWidth,
                        tickGap=self.rulerTickGap,
                        tickLength=self.rulerTickLength,
                        tickFont=self.rulerFont,
                    )
                    self.addUndoStack(self._newRuler)
                elif self.editModes.addVia:
                    if self._arrayVia is not None:
                        self.arrayViaTuple = None
                        self._arrayVia = None

                    singleVia = lshp.layoutVia(
                        QPoint(0, 0),
                        *self.arrayViaTuple.singleViaTuple,
                    )
                    self._arrayVia = lshp.layoutViaArray(
                        self.mouseMoveLoc,
                        singleVia,
                        self.arrayViaTuple.xs,
                        self.arrayViaTuple.ys,
                        self.arrayViaTuple.xnum,
                        self.arrayViaTuple.ynum,
                    )
                    self.addUndoStack(self._arrayVia)

                elif self.editModes.changeOrigin:
                    self.origin = self.mouseReleaseLoc
                elif self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        # Rotate selected items
                        self.rotateSelectedItems(self.mouseReleaseLoc)

        except Exception as e:
            self.logger.error(f"mouse release error: {e}")

    def addNewInstance(self):
        self.newInstance = self.instLayout()
        # if new instance is a pcell, start a dialogue for pcell parameters
        if isinstance(self.newInstance, pcells.baseCell):
            dlg = ldlg.pcellInstanceDialog(self.editorWindow)
            dlg.pcellLibName.setText(self.newInstance.libraryName)
            dlg.pcellCellName.setText(self.newInstance.cellName)
            dlg.pcellViewName.setText(self.newInstance.viewName)
            initArgs = inspect.signature(
                self.newInstance.__class__.__init__
            ).parameters
            argsUsed = [param for param in initArgs if (param != "self")]
            argDict = {
                arg: getattr(self.newInstance, arg) for arg in argsUsed
            }
            lineEditDict = {
                key: edf.shortLineEdit(value)
                for key, value in argDict.items()
            }
            for key, value in lineEditDict.items():
                dlg.instanceParamsLayout.addRow(key, value)
            if dlg.exec() == QDialog.Accepted:
                instanceValuesDict = {}
                for key, value in lineEditDict.items():
                    instanceValuesDict[key] = value.text()
                self.newInstance(*instanceValuesDict.values())


    def instLayout(self):
        """
        Read a layout file and create layoutShape objects from it.
        """
        match self.layoutInstanceTuple.viewItem.viewType:
            case "layout":
                with self.layoutInstanceTuple.viewItem.viewPath.open("r") as temp:
                    try:
                        decodedData = json.load(temp)
                        if decodedData[0]["cellView"] != "layout":
                            self.logger.error("Not a layout cell")
                        else:
                            instanceShapes = [
                                lj.layoutItems(self).create(item)
                                for item in decodedData[2:]
                                if item.get("type") in self.layoutShapes
                            ]
                            layoutInstance = lshp.layoutInstance(instanceShapes)
                            layoutInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            layoutInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            layoutInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            self.itemCounter += 1
                            layoutInstance.counter = self.itemCounter
                            layoutInstance.instanceName = f"I{layoutInstance.counter}"
                            # For each instance assign a counter number from the scene
                            return layoutInstance
                    except json.JSONDecodeError:
                        self.logger.warning("Invalid JSON File")
            case "pcell":
                with open(self.layoutInstanceTuple.viewItem.viewPath, "r") as temp:
                    try:
                        pcellRefDict = json.load(temp)
                        if pcellRefDict[0]["cellView"] != "pcell":
                            self.logger.error("Not a pcell cell")
                        else:
                            # create a pcell instance with default parameters.
                            pcellInstance = eval(
                                f"pcells.{pcellRefDict[1]['reference']}()"
                            )
                            # now evaluate pcell

                            pcellInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            pcellInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            pcellInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            self.itemCounter += 1
                            pcellInstance.counter = self.itemCounter
                            # This needs to become more sophisticated.
                            pcellInstance.instanceName = f"I{pcellInstance.counter}"

                            return pcellInstance
                    except Exception as e:
                        self.logger.error(f"Cannot read pcell: {e}")

    def findScenelayoutCellSet(self) -> set[lshp.layoutInstance]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, lshp.layoutInstance)}

    def saveLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """
        Save the layout cell items to a file.

        Args:
            filePathObj (pathlib.Path): filepath object for layout file.

        Returns:
            None
        """
        try:
            # Only save the top-level items

            topLevelItems = [item for item in self.items() if item.parentItem() is None]
            topLevelItems.insert(0, {"cellView": "layout"})
            topLevelItems.insert(1, {"snapGrid": self.snapTuple})
            with filePathObj.open("w") as file:
                # Serialize items to JSON using layoutEncoder class
                json.dump(topLevelItems, file, cls=layenc.layoutEncoder)
        except Exception as e:
            self.logger.error(f"Cannot save layout: {e}")

    def loadLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """
        Load the layout cell from the given file path.

        Args:
            filePathObj (pathlib.Path): The file path object.

        Returns:
            None
        """
        try:
            with filePathObj.open("r") as file:
                decodedData = json.load(file)

            # Unpack grid settings
            _, gridSettings, *itemData = decodedData
            snapGrid = gridSettings.get("snapGrid", [1, 1])
            self.majorGrid, self.snapGrid = snapGrid
            self.snapTuple = (self.snapGrid, self.snapGrid)
            self.snapDistance = 2 * self.snapGrid

            startTime = time.perf_counter()
            self.createLayoutItems(itemData)
            endTime = time.perf_counter()

            self.logger.info(f"Load time: {endTime - startTime:.4f} seconds")
            print(f"Load time: {endTime - startTime:.4f} seconds")
        except Exception as e:
            self.logger.error(f"Cannot load layout: {e}")



    def createLayoutItems(self, decodedData: List[Dict[str, Any]]) -> None:
        """
        Create layout items from decoded data.

        Args:
            decodedData (List[Dict[str, Any]]): List of item data dictionaries.

        Returns:
            None
        """
        if not decodedData:
            return

        validTypes = frozenset(self.layoutShapes)
        loadedLayoutItems = [
            lj.layoutItems(self).create(item)
            for item in decodedData
            if item.get("type") in validTypes
        ]

        if loadedLayoutItems:
            undoCommand = us.loadShapesUndo(self, loadedLayoutItems)
            self.undoStack.push(undoCommand)

    #
    # def loadLayoutCell(self, filePathObj: pathlib.Path) -> None:
    #     """
    #     Load the layout cell from the given file path.
    #
    #     Args:
    #         filePathObj (pathlib.Path): The file path object.
    #
    #     Returns:
    #         None
    #     """
    #     try:
    #         with filePathObj.open("r") as file:
    #             decodedData = json.load(file)
    #         snapGrid = decodedData[1].get("snapGrid")
    #         self.majorGrid = snapGrid[0]  # dot/line grid spacing
    #         self.snapGrid = snapGrid[1]  # snapping grid size
    #         self.snapTuple = (self.snapGrid, self.snapGrid)
    #         self.snapDistance = 2 * self.snapGrid
    #         starttime = time.time()
    #         self.createLayoutItems(decodedData[2:])
    #         endtime = time.time()
    #         print(f"load time: {endtime-starttime}")
    #     except Exception as e:
    #         self.logger.error(f"Cannot load layout: {e}")
    #
    # def createLayoutItems(self, decodedData):
    #     if decodedData:
    #         loadedLayoutItems = [
    #             lj.layoutItems(self).create(item)
    #             for item in decodedData
    #             if item.get("type") in self.layoutShapes
    #         ]
    #         # A hack to get loading working. Otherwise, when it is saved the top-level items
    #         # get destroyed.
    #         undoCommand = us.loadShapesUndo(self, loadedLayoutItems)
    #         self.undoStack.push(undoCommand)

    def reloadScene(self):
        # Get the top level items from the scene
        topLevelItems = [item for item in self.items() if item.parentItem() is None]
        # Insert a layout item at the beginning of the list
        topLevelItems.insert(0, {"cellView": "layout"})
        # Convert the top level items to JSON string
        # Decode the JSON string back to Python objects
        decodedData = json.loads(json.dumps(topLevelItems, cls=layenc.layoutEncoder))
        # Clear the current scene
        self.clear()
        # Create layout items based on the decoded data
        self.createLayoutItems(decodedData)

    def deleteSelectedItems(self):
        for item in self.selectedItems():
            # if pin is to be deleted, the associated label should be also deleted.
            if isinstance(item, lshp.layoutPin) and item.label is not None:
                undoCommand = us.deleteShapeUndo(self, item.label)
                self.undoStack.push(undoCommand)
        super().deleteSelectedItems()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    match type(item):
                        case lshp.layoutRect:
                            self.layoutRectProperties(item)
                        case lshp.layoutPin:
                            self.layoutPinProperties(item)
                        case lshp.layoutLabel:
                            self.layoutLabelProperties(item)
                        case lshp.layoutPath:
                            self.layoutPathProperties(item)
                        case lshp.layoutViaArray:
                            self.layoutViaProperties(item)
                        case lshp.layoutPolygon:
                            self.layoutPolygonProperties(item)
                        case lshp.layoutInstance:
                            self.layoutInstanceProperties(item)
                        case _:
                            if item.__class__.__bases__[0] == pcells.baseCell:
                                self.layoutPCellProperties(item)

        except Exception as e:
            self.logger.error(f"{type(item)} property editor error: {e}")

    def layoutPolygonProperties(self, item):
        pointsTupleList = [self.toLayoutCoord(point) for point in item.points]
        dlg = ldlg.layoutPolygonProperties(self.editorWindow, pointsTupleList)
        dlg.polygonLayerCB.addItems(
            [f"{item.netName} [{item.purpose}]" for item in laylyr.pdkAllLayers]
        )
        dlg.polygonLayerCB.setCurrentText(
            f"{item.layer.netName} [" f"{item.layer.purpose}]"
        )

        if dlg.exec() == QDialog.Accepted:
            item.layer = laylyr.pdkAllLayers[dlg.polygonLayerCB.currentIndex()]
            tempPoints = []
            for i in range(dlg.tableWidget.rowCount()):
                xcoor = dlg.tableWidget.item(i, 1).text()
                ycoor = dlg.tableWidget.item(i, 2).text()
                if xcoor != "" and ycoor != "":
                    tempPoints.append(
                        self.toSceneCoord(QPointF(float(xcoor), float(ycoor)))
                    )
            item.points = tempPoints

    def layoutRectProperties(self, item):
        dlg = ldlg.layoutRectProperties(self.editorWindow)
        dlg.rectLayerCB.addItems(
            [f"{item.netName} [{item.purpose}]" for item in laylyr.pdkAllLayers]
        )
        dlg.rectLayerCB.setCurrentText(f"{item.layer.netName} [{item.layer.purpose}]")
        dlg.rectWidthEdit.setText(str(item.width / fabproc.dbu))
        dlg.rectHeightEdit.setText(str(item.height / fabproc.dbu))
        dlg.topLeftEditX.setText(str(item.rect.topLeft().x() / fabproc.dbu))
        dlg.topLeftEditY.setText(str(item.rect.topLeft().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.layer = laylyr.pdkAllLayers[dlg.rectLayerCB.currentIndex()]
            item.width = float(dlg.rectWidthEdit.text()) * fabproc.dbu
            item.height = float(dlg.rectHeightEdit.text()) * fabproc.dbu

            item.rect = QRectF(
                float(dlg.topLeftEditX.text()) * fabproc.dbu,
                float(dlg.topLeftEditY.text()) * fabproc.dbu,
                float(dlg.rectWidthEdit.text()) * fabproc.dbu,
                float(dlg.rectHeightEdit.text()) * fabproc.dbu,
            )

    def layoutViaProperties(self, item):
        dlg = ldlg.layoutViaProperties(self.editorWindow)
        if item.xnum == 1 and item.ynum == 1:
            dlg.singleViaRB.setChecked(True)
            dlg.singleViaClicked()
            dlg.singleViaNamesCB.setCurrentText(item.via.viaDefTuple.netName)
            dlg.singleViaWidthEdit.setText(str(item.width / fabproc.dbu))
            dlg.singleViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
        else:
            dlg.arrayViaRB.setChecked(True)
            dlg.arrayViaClicked()
            dlg.arrayViaNamesCB.setCurrentText(item.via.viaDefTuple.netName)
            dlg.arrayViaWidthEdit.setText(str(item.via.width / fabproc.dbu))
            dlg.arrayViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
            dlg.arrayViaSpacingEdit.setText(str(item.spacing / fabproc.dbu))
            dlg.arrayXNumEdit.setText(str(item.xnum))
            dlg.arrayYNumEdit.setText(str(item.ynum))
        dlg.startXEdit.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.startYEdit.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            if dlg.singleViaRB.isChecked():
                item.viaDefTuple = [
                    viaDefT
                    for viaDefT in fabproc.processVias
                    if viaDefT.netName == dlg.singleViaNamesCB.currentText()
                ][0]
                item.width = float(dlg.singleViaWidthEdit.text()) * fabproc.dbu
                item.height = float(dlg.singleViaHeightEdit.text()) * fabproc.dbu
                item.start = item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.startXEdit.text()), float(dlg.startYEdit.text())
                        )
                    )
                )
                item.xnum = 1
                item.ynum = 1
                item.spacing = 0.0
            else:
                item.viaDefTuple = [
                    viaDefT
                    for viaDefT in fabproc.processVias
                    if viaDefT.netName == dlg.arrayViaNamesCB.currentText()
                ][0]
                item.width = float(dlg.arrayViaWidthEdit.text()) * fabproc.dbu
                item.height = float(dlg.arrayViaHeightEdit.text()) * fabproc.dbu
                item.start = item.mapFromScene(
                    self.toLayoutCoord(
                        QPointF(
                            float(dlg.startXEdit.text()), float(dlg.startYEdit.text())
                        )
                    )
                )
                item.xnum = int(dlg.arrayXNumEdit.text())
                item.ynum = int(dlg.arrayYNumEdit.text())
                item.spacing = float(dlg.arrayViaSpacingEdit.text()) * fabproc.dbu

    def layoutPathProperties(self, item):
        dlg = ldlg.layoutPathPropertiesDialog(self.editorWindow)
        match item.mode:
            case 0:
                dlg.manhattanButton.setChecked(True)
            case 1:
                dlg.diagonalButton.setChecked(True)
            case 2:
                dlg.anyButton.setChecked(True)
            case 3:
                dlg.horizontalButton.setChecked(True)
            case 4:
                dlg.verticalButton.setChecked(True)
        dlg.pathLayerCB.addItems(
            [f"{item.netName} [{item.purpose}]" for item in laylyr.pdkDrawingLayers]
        )
        dlg.pathLayerCB.setCurrentText(f"{item.layer.netName} [{item.layer.purpose}]")
        dlg.pathWidth.setText(str(item.width / fabproc.dbu))
        dlg.pathNameEdit.setText(item.netName)
        roundingFactor = len(str(fabproc.dbu)) - 1
        dlg.startExtendEdit.setText(
            str(round(item.startExtend / fabproc.dbu, roundingFactor))
        )
        dlg.endExtendEdit.setText(
            str(round(item.endExtend / fabproc.dbu, roundingFactor))
        )
        dlg.p1PointEditX.setText(
            str(round(item.draftLine.p1().x() / fabproc.dbu, roundingFactor))
        )
        dlg.p1PointEditY.setText(
            str(round(item.draftLine.p1().y() / fabproc.dbu, roundingFactor))
        )
        dlg.p2PointEditX.setText(
            str(round(item.draftLine.p2().x() / fabproc.dbu, roundingFactor))
        )
        dlg.p2PointEditY.setText(
            str(round(item.draftLine.p2().y() / fabproc.dbu, roundingFactor))
        )
        angle = item.angle
        if dlg.exec() == QDialog.Accepted:
            item.netName = dlg.pathNameEdit.text()
            item.layer = laylyr.pdkDrawingLayers[dlg.pathLayerCB.currentIndex()]
            item.width = fabproc.dbu * float(dlg.pathWidth.text())
            item.startExtend = fabproc.dbu * float(dlg.startExtendEdit.text())
            item.endExtend = fabproc.dbu * float(dlg.endExtendEdit.text())
            p1 = self.toSceneCoord(
                QPointF(
                    float(dlg.p1PointEditX.text()),
                    float(dlg.p1PointEditY.text()),
                )
            )
            p2 = self.toSceneCoord(
                QPointF(
                    float(dlg.p2PointEditX.text()),
                    float(dlg.p2PointEditY.text()),
                )
            )
            item.draftLine = QLineF(p1, p2)
            item.angle = angle

    def layoutLabelProperties(self, item):
        dlg = ldlg.layoutLabelProperties(self.editorWindow)
        dlg.labelName.setText(item.labelText)
        dlg.labelLayerCB.addItems(
            [f"{layer.netName} [{layer.purpose}]" for layer in laylyr.pdkTextLayers]
        )
        dlg.labelLayerCB.setCurrentText(f"{item.layer.netName} [{item.layer.purpose}]")
        dlg.familyCB.setCurrentText(item.fontFamily)
        dlg.fontStyleCB.setCurrentText(item.fontStyle)
        dlg.labelHeightCB.setCurrentText(str(int(item.fontHeight)))
        dlg.labelAlignCB.setCurrentText(item.labelAlign)
        dlg.labelOrientCB.setCurrentText(item.labelOrient)
        dlg.labelTopLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.labelTopLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.labelText = dlg.labelName.text()
            item.layer = laylyr.pdkTextLayers[dlg.labelLayerCB.currentIndex()]
            item.fontFamily = dlg.familyCB.currentText()
            item.fontStyle = dlg.fontStyleCB.currentText()
            item.fontHeight = int(float(dlg.labelHeightCB.currentText()))
            item.labelAlign = dlg.labelAlignCB.currentText()
            item.labelOrient = dlg.labelOrientCB.currentText()
            item.start = item.snapToGrid(
                item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.labelTopLeftX.text()),
                            float(dlg.labelTopLeftY.text()),
                        )
                    )
                ),
                self.snapTuple,
            )

    def layoutPinProperties(self, item):
        dlg = ldlg.layoutPinProperties(self.editorWindow)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)

        dlg.pinLayerCB.addItems(
            [
                f"{pinLayer.netName} [{pinLayer.purpose}]"
                for pinLayer in laylyr.pdkPinLayers
            ]
        )
        dlg.pinLayerCB.setCurrentText(f"{item.layer.netName} [{item.layer.purpose}]")
        dlg.pinBottomLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.pinBottomLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        dlg.pinTopRightX.setText(str(item.mapToScene(item.end).x() / fabproc.dbu))
        dlg.pinTopRightY.setText(str(item.mapToScene(item.end).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.pinName = dlg.pinName.text()
            item.pinDir = dlg.pinDir.currentText()
            item.pinType = dlg.pinType.currentText()
            item.layer = laylyr.pdkPinLayers[dlg.pinLayerCB.currentIndex()]
            item.label.labelText = dlg.pinName.text()
            item.start = item.snapToGrid(
                item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.pinBottomLeftX.text()),
                            float(dlg.pinBottomLeftY.text()),
                        )
                    )
                ),
                self.snapTuple,
            )
            item.end = item.snapToGrid(
                item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.pinTopRightX.text()),
                            float(dlg.pinTopRightY.text()),
                        )
                    )
                ),
                self.snapTuple,
            )
            item.layer.netName = dlg.pinLayerCB.currentText()

    def layoutInstanceProperties(self, item):
        dlg = ldlg.layoutInstancePropertiesDialog(self.editorWindow)
        dlg.instanceLibName.setText(item.libraryName)
        dlg.instanceCellName.setText(item.cellName)
        dlg.instanceViewName.setText(item.viewName)
        dlg.instanceNameEdit.setText(item.instanceName)
        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.libraryName = dlg.instanceLibName.text().strip()
            item.cellName = dlg.instanceCellName.text().strip()
            item.viewName = dlg.instanceViewName.text().strip()
            item.instanceName = dlg.instanceNameEdit.text().strip()
            item.setPos(
                QPoint(
                    self.snapToBase(
                        float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]
                    ),
                    self.snapToBase(
                        float(dlg.yEdit.text()) * fabproc.dbu, self.snapTuple[1]
                    ),
                )
            )

    def layoutPCellProperties(self, item: lshp.layoutPcell):
        dlg = ldlg.pcellInstancePropertiesDialog(self.editorWindow)
        dlg.pcellLibName.setText(item.libraryName)
        dlg.pcellCellName.setText(item.cellName)
        dlg.pcellViewName.setText(item.viewName)
        dlg.instanceNameEdit.setText(item.instanceName)
        lineEditDict = self.extractPcellInstanceParameters(item)
        for key, value in lineEditDict.items():
            dlg.instanceParamsLayout.addRow(key, value)
        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.libraryName = dlg.pcellLibName.text()
            item.cellName = dlg.pcellCellName.text()
            item.viewName = dlg.pcellViewName.text()
            item.instanceName = dlg.instanceNameEdit.text()
            rowCount = dlg.instanceParamsLayout.rowCount()
            instParamDict = {}
            for row in range(4, rowCount):  # first 4 rows are already processed.
                labelText = (
                    dlg.instanceParamsLayout.itemAt(row, QFormLayout.LabelRole)
                    .widget()
                    .text()
                    .replace("&", "")
                ) 
                paramValue = (
                    dlg.instanceParamsLayout.itemAt(row, QFormLayout.FieldRole)
                    .widget()
                    .text()
                )
                instParamDict[labelText] = paramValue
            item(**instParamDict)

    def extractPcellInstanceParameters(self, instance: lshp.layoutPcell) -> dict:
        initArgs = inspect.signature(instance.__class__.__init__).parameters
        argsUsed = [param for param in initArgs if (param != "self")]
        argDict = {arg: getattr(instance, arg) for arg in argsUsed}
        lineEditDict = {key: edf.shortLineEdit(value) for key, value in argDict.items()}
        return lineEditDict

    def copySelectedItems(self):
        """
        Copy the selected items and create new instances with incremented names.
        """
        newShapes = []
        for item in self.selectedItems():
            # Create a deep copy of the item using JSON serialization
            itemCopyJson = json.dumps(item, cls=layenc.layoutEncoder)
            itemCopyDict = json.loads(itemCopyJson)
            shape = lj.layoutItems(self).create(itemCopyDict)

            match itemCopyDict["type"]:
                case "Inst" | "Pcell":
                    self.itemCounter += 1
                    shape.instanceName = f"I{self.itemCounter}"
                    shape.counter = self.itemCounter

            newShapes.append(shape)
        if newShapes:
            self.undoStack.push(us.addShapesUndo(self, newShapes))
            for shape in newShapes:
                shape.setPos(self.mouseMoveLoc)

    # def copySelectedItems(self):
    #     """
    #     Copy the selected items and create new instances with incremented names.
    #     """
    #     for item in self.selectedItems():
    #         # Create a deep copy of the item using JSON serialization
    #         itemCopyJson = json.dumps(item, cls=layenc.layoutEncoder)
    #         itemCopyDict = json.loads(itemCopyJson)
    #         shape = lj.layoutItems(self).create(itemCopyDict)
    #         match itemCopyDict["type"]:
    #             case "Inst" | "Pcell":
    #                 self.itemCounter += 1
    #                 shape.instanceName = f"I{self.itemCounter}"
    #                 shape.counter = self.itemCounter
    #         self.undoStack.push(us.addShapeUndo(self, shape))
    #         shape.setPos(
    #             QPoint(
    #                 item.pos().x() + 4 * self.snapTuple[0],
    #                 item.pos().y() + 4 * self.snapTuple[1],
    #             )
    #         )

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0.0")
            dlg.yEdit.setText("0.0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(
                        self.snapToBase(
                            float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]
                        ),
                        self.snapToBase(
                            float(dlg.yEdit.text()) * fabproc.dbu, self.snapTuple[1]
                        ),
                    )
                self.editorWindow.messageLine.setText(
                    f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}"
                )
                self.editModes.setMode("selectItem")

    def deleteAllRulers(self):
        for ruler in self.rulersSet:
            undoCommand = us.deleteShapeUndo(self, ruler)
            self.undoStack.push(undoCommand)

    def goDownHier(self):
        if self.selectedItems():
            for item in self.selectedItems():
                if isinstance(item, lshp.layoutInstance):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(
                        self.editorWindow.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [
                        cellItem.child(i).text()
                        for i in range(cellItem.rowCount())
                        # if cellItem.child(i).text() != item.viewName
                        if "layout" in cellItem.child(i).text()
                    ]
                    dlg.viewListCB.addItems(viewNames)
                    if dlg.exec() == QDialog.Accepted:
                        libItem = libm.getLibItem(
                            self.editorWindow.libraryView.libraryModel, item.libraryName
                        )
                        cellItem = libm.getCellItem(libItem, item.cellName)
                        viewItem = libm.getViewItem(
                            cellItem, dlg.viewListCB.currentText()
                        )
                        openViewT = (
                            self.editorWindow.libraryView.libBrowsW.openCellView(
                                viewItem, cellItem, libItem
                            )
                        )
                        if self.editorWindow.appMainW.openViews[openViewT]:
                            childWindow = self.editorWindow.appMainW.openViews[
                                openViewT
                            ]
                            childWindow.parentEditor = self.editorWindow
                            childWindow.layoutToolbar.addAction(childWindow.goUpAction)
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    def stretchPath(self, pathItem: lshp.layoutPath, stretchEnd: str):
        match stretchEnd:
            case "p2":
                self._stretchPath = lshp.layoutPath(
                    QLineF(pathItem.sceneEndPoints[0], pathItem.sceneEndPoints[1]),
                    pathItem.layer,
                    pathItem.width,
                    pathItem.startExtend,
                    pathItem.endExtend,
                    pathItem.mode,
                )
            case "p1":
                self._stretchPath = lshp.layoutPath(
                    QLineF(pathItem.sceneEndPoints[1], pathItem.sceneEndPoints[0]),
                    pathItem.layer,
                    pathItem.width,
                    pathItem.startExtend,
                    pathItem.endExtend,
                    pathItem.mode,
                )
        self._stretchPath.stretch = True
        self._stretchPath.name = pathItem.name

        addDeleteStretchNetCommand = us.addDeleteShapeUndo(
            self, self._stretchPath, pathItem
        )
        self.undoStack.push(addDeleteStretchNetCommand)
    #
    # @staticmethod
    # def rotateVector(mouseLoc: QPoint, vector: layp.layoutPath, transform: QTransform):
    #     """
    #     Rotate the vector based on the mouse location and transform.
    #
    #     Args:
    #         mouseLoc (QPoint): The current mouse location.
    #         vector (layp.layoutPath): The vector to rotate.
    #         transform (QTransform): The transform to apply to the vector.
    #     """
        # start = vector.start
        # xmove = mouseLoc.x() - start.x()
        # ymove = mouseLoc.y() - start.y()

    #     # Determine the new end point of the vector based on the mouse movement
    #     if xmove >= 0 and ymove >= 0:
    #         vector.end = QPoint(start.x(), start.y() + ymove)
    #     elif xmove >= 0 and ymove < 0:
    #         vector.end = QPoint(start.x() + xmove, start.y())
    #     elif xmove < 0 and ymove < 0:
    #         vector.end = QPoint(start.x(), start.y() + ymove)
    #     elif xmove < 0 and ymove >= 0:
    #         vector.end = QPoint(start.x() + xmove, start.y())
    #
    #     vector.setTransform(transform)

    def findClosestFontSize(self,sizes: List[int], target: int = 16) -> int:
        return min(sizes, key=lambda x: abs(x - target))

    def setRulerFont(self, target_size: int = 16) -> QFont:
        fontDatabase = QFontDatabase()
        fixedFamilies = [family for family in fontDatabase.families(QFontDatabase.Latin)
                          if fontDatabase.isFixedPitch(family)]

        if not fixedFamilies:
            self.scene().logger.warning("No fixed-pitch fonts found. Using default font.")
            return QFont()

        for family in fixedFamilies:
            styles = fontDatabase.styles(family)
            if not styles:
                continue

            style = styles[0]  # Use the first available style
            sizes = fontDatabase.pointSizes(family, style)

            if sizes:
                closest_size = self.findClosestFontSize(sizes, target_size)
                font = QFont(family)
                font.setStyleName(style)
                font.setPointSize(closest_size)
                font.setKerning(False)
                return font

        self.scene().logger.warning("No suitable font found. Using default font.")
        return QFont()