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

import datetime
import json
import math

# from hashlib import new
import pathlib
import shutil
from copy import deepcopy

# import os
# if os.environ.get('REVEDASIM_PATH'):
#     import revedasim.simMainWindow as smw

# import numpy as np
from PySide6.QtCore import (
    QEvent,
    QMargins,
    QPoint,
    QPointF,
    QProcess,
    QRect,
    QRectF,
    QRunnable,
    Qt,
    Slot,
    QLineF,
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QCursor,
    QGuiApplication,
    QIcon,
    QImage,
    QKeySequence,
    QPainter,
    QPen,
    QMouseEvent,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
    QUndoStack,
    QTransform,
    QFontDatabase,
    QFont,
    QWheelEvent,
)
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QSplitter,
    QSizePolicy,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QGraphicsLineItem,
)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.schBackEnd as scb
import revedaEditor.backend.undoStack as us
import revedaEditor.common.net as net
import revedaEditor.common.layoutShapes as layp

# import pdk.symLayers as symlyr
import pdk.schLayers as schlyr
import pdk.layoutLayers as laylyr
import pdk.process as fabproc
import revedaEditor.common.shape as shp  # import the shapes
import revedaEditor.common.layoutShapes as lshp  # import layout shapes
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.fileio.symbolEncoder as se
import revedaEditor.fileio.layoutEncoder as le
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.propertyDialogues as pdlg
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.lsw as lsw
import revedaEditor.resources.resources
import revedaEditor.fileio.gdsExport as gdse
import pdk.pcells as pcells


class editorWindow(QMainWindow):
    """
    Base class for editor windows.
    """

    def __init__(
        self, viewItem: scb.viewItem, libraryDict: dict, libraryView
    ):  # file is a pathlib.Path object
        super().__init__()
        self.centralW = None
        self.viewItem = viewItem
        self.file = self.viewItem.data(Qt.UserRole + 2)
        self.cellItem = self.viewItem.parent()
        self.cellName = self.cellItem.cellName
        self.libItem = self.cellItem.parent()
        self.libName = self.libItem.libraryName
        self.viewName = self.viewItem.viewName
        self.libraryDict = libraryDict
        self.libraryView = libraryView
        self.parentView = None
        self._app = QApplication.instance()
        self._createActions()
        self._createTriggers()
        self._createShortcuts()
        self.appMainW = self.libraryView.parent.parent.appMainW
        self.logger = self.appMainW.logger
        self.switchViewList = self.appMainW.switchViewList
        self.stopViewList = self.appMainW.stopViewList
        self.statusLine = self.statusBar()
        self.messageLine = QLabel()  # message line
        self.statusLine.addPermanentWidget(self.messageLine)
        self.majorGrid = 10  # snapping grid size
        self.gridTuple = (self.majorGrid, self.majorGrid)
        self.snapDistance = 20
        if self._app.revedasim_path:
            import revedasim.simMainWindow as smw
        self.init_UI()

    def init_UI(self):
        """
        Placeholder for child classes init_UI function.
        """
        ...

    def _createMenuBar(self):
        self.editorMenuBar = self.menuBar()
        self.editorMenuBar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuFile = self.editorMenuBar.addMenu("&File")
        self.menuView = self.editorMenuBar.addMenu("&View")
        self.menuEdit = self.editorMenuBar.addMenu("&Edit")
        self.menuCreate = self.editorMenuBar.addMenu("C&reate")
        self.menuCheck = self.editorMenuBar.addMenu("&Check")
        self.menuTools = self.editorMenuBar.addMenu("&Tools")
        self.menuWindow = self.editorMenuBar.addMenu("&Window")
        self.menuUtilities = self.editorMenuBar.addMenu("&Utilities")

    def _createActions(self):
        checkCellIcon = QIcon(":/icons/document-task.png")
        self.checkCellAction = QAction(checkCellIcon, "Check-Save", self)

        saveCellIcon = QIcon(":/icons/document--plus.png")
        self.saveCellAction = QAction(saveCellIcon, "Save", self)

        self.readOnlyCellIcon = QIcon(":/icons/lock.png")
        self.readOnlyCellAction = QAction("Read Only", self)
        self.readOnlyCellAction.setCheckable(True)

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)

        printPreviewIcon = QIcon(":/icons/printer--arrow.png")
        self.printPreviewAction = QAction(printPreviewIcon, "Print Preview...", self)

        exportImageIcon = QIcon(":/icons/image-export.png")
        self.exportImageAction = QAction(exportImageIcon, "Export...", self)

        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Close Window", self)
        self.exitAction.setShortcut("Ctrl+Q")

        fitIcon = QIcon(":/icons/zone.png")
        self.fitAction = QAction(fitIcon, "Fit to Window", self)

        zoomInIcon = QIcon(":/icons/zone-resize.png")
        self.zoomInAction = QAction(zoomInIcon, "Zoom In", self)

        zoomOutIcon = QIcon(":/icons/zone-resize-actual.png")
        self.zoomOutAction = QAction(zoomOutIcon, "Zoom Out", self)

        panIcon = QIcon(":/icons/zone--arrow.png")
        self.panAction = QAction(panIcon, "Pan View", self)

        redrawIcon = QIcon(":/icons/arrow-circle.png")
        self.redrawAction = QAction(redrawIcon, "Redraw", self)

        rulerIcon = QIcon(":/icons/ruler.png")
        self.rulerAction = QAction(rulerIcon, "Ruler", self)

        delRulerIcon = QIcon.fromTheme("delete")
        self.delRulerAction = QAction(delRulerIcon, "Delete Rulers", self)

        # display options
        dispConfigIcon = QIcon(":/icons/resource-monitor.png")
        self.dispConfigAction = QAction(dispConfigIcon, "Display Config...", self)

        selectConfigIcon = QIcon(":/icons/zone-select.png")
        self.selectConfigAction = QAction(selectConfigIcon, "Selection Config...", self)

        panZoomConfigIcon = QIcon(":/icons/selection-resize.png")
        self.panZoomConfigAction = QAction(
            panZoomConfigIcon, "Pan/Zoom Config...", self
        )

        undoIcon = QIcon(":/icons/arrow-circle-315-left.png")
        self.undoAction = QAction(undoIcon, "Undo", self)

        redoIcon = QIcon(":/icons/arrow-circle-225.png")
        self.redoAction = QAction(redoIcon, "Redo", self)

        yankIcon = QIcon(":/icons/node-insert.png")
        self.yankAction = QAction(yankIcon, "Yank", self)

        pasteIcon = QIcon(":/icons/clipboard-paste.png")
        self.pasteAction = QAction(pasteIcon, "Paste", self)

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteAction = QAction(deleteIcon, "Delete", self)

        copyIcon = QIcon(":/icons/document-copy.png")
        self.copyAction = QAction(copyIcon, "Copy", self)

        moveIcon = QIcon(":/icons/arrow-move.png")
        self.moveAction = QAction(moveIcon, "Move", self)

        moveByIcon = QIcon(":/icons/arrow-transition.png")
        self.moveByAction = QAction(moveByIcon, "Move By ...", self)

        moveOriginIcon = QIcon(":/icons/arrow-skip.png")
        self.moveOriginAction = QAction(moveOriginIcon, "Move Origin", self)

        stretchIcon = QIcon(":/icons/fill.png")
        self.stretchAction = QAction(stretchIcon, "Stretch", self)

        rotateIcon = QIcon(":/icons/arrow-circle.png")
        self.rotateAction = QAction(rotateIcon, "Rotate...", self)

        scaleIcon = QIcon(":/icons/selection-resize.png")
        self.scaleAction = QAction(scaleIcon, "Scale...", self)

        netNameIcon = QIcon(":/icons/node-design.png")
        self.netNameAction = QAction(netNameIcon, "Net Name...", self)

        # create label action but do not add to any menu.
        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        goUpIcon = QIcon(":/icons/arrow-step-out.png")
        self.goUpAction = QAction(goUpIcon, "Go Up", self)

        goDownIcon = QIcon(":/icons/arrow-step.png")
        self.goDownAction = QAction(goDownIcon, "Go Down", self)

        self.selectAllIcon = QIcon(":/icons/node-select-all.png")
        self.selectAllAction = QAction(self.selectAllIcon, "Select All", self)

        deselectAllIcon = QIcon(":/icons/node.png")
        self.deselectAllAction = QAction(deselectAllIcon, "Unselect All", self)

        objPropIcon = QIcon(":/icons/property-blue.png")
        self.objPropAction = QAction(objPropIcon, "Object Properties...", self)

        viewPropIcon = QIcon(":/icons/property.png")
        self.viewPropAction = QAction(viewPropIcon, "Cellview Properties...", self)

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(deleteErrorsIcon, "Delete Errors...", self)

        netlistIcon = QIcon(":/icons/script-text.png")
        self.netlistAction = QAction(netlistIcon, "Create Netlist...", self)

        simulateIcon = QIcon(":/icons/application-wave.png")
        self.simulateAction = QAction(simulateIcon, "Run RevEDA Sim GUI", self)

        createLineIcon = QIcon(":/icons/edLayer-shape-line.png")
        self.createLineAction = QAction(createLineIcon, "Create Line...", self)

        createRectIcon = QIcon(":/icons/edLayer-shape.png")
        self.createRectAction = QAction(createRectIcon, "Create Rectangle...", self)

        createPolyIcon = QIcon(":/icons/edLayer-shape-polygon.png")
        self.createPolyAction = QAction(createPolyIcon, "Create Polygon...", self)

        createCircleIcon = QIcon(":/icons/edLayer-shape-ellipse.png")
        self.createCircleAction = QAction(createCircleIcon, "Create Circle...", self)

        createArcIcon = QIcon(":/icons/edLayer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(createInstIcon, "Create Instance...", self)

        createWireIcon = QIcon(":/icons/node-insert.png")
        self.createWireAction = QAction(createWireIcon, "Create Wire...", self)

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)

        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(createSymbolIcon, "Create Symbol...", self)

        createTextIcon = QIcon(":icons/sticky-note-text.png")
        self.createTextAction = QAction(createTextIcon, "Create Text...", self)

        self.createLabelAction = QAction(createTextIcon, "Create Label...", self)

        ignoreIcon = QIcon(":/icons/minus-circle.png")
        self.ignoreAction = QAction(ignoreIcon, "Ignore", self)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        self.toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.exportImageAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.deleteAction)
        self.toolbar.addAction(self.moveAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.stretchAction)
        self.toolbar.addAction(self.rotateAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.fitAction)
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.objPropAction)

    def _addActions(self):
        # file menu
        self.menuFile.addAction(self.checkCellAction)
        self.menuFile.addAction(self.saveCellAction)
        self.menuFile.addAction(self.printAction)
        self.menuFile.addAction(self.printPreviewAction)
        self.menuFile.addAction(self.exportImageAction)
        self.menuFile.addAction(self.exitAction)
        # view menu
        self.menuView.addAction(self.fitAction)
        self.menuView.addAction(self.zoomInAction)
        self.menuView.addAction(self.zoomOutAction)
        self.menuView.addAction(self.panAction)
        self.menuView.addAction(self.redrawAction)
        self.menuView.addAction(self.dispConfigAction)
        self.menuView.addAction(self.selectConfigAction)
        self.menuView.addAction(self.panZoomConfigAction)
        # edit menu
        self.menuEdit.addAction(self.undoAction)
        self.menuEdit.addAction(self.redoAction)
        # self.menuEdit.addAction(self.yankAction)
        self.menuEdit.addAction(self.pasteAction)
        self.menuEdit.addAction(self.deleteAction)
        self.menuEdit.addAction(self.copyAction)
        self.menuEdit.addAction(self.moveAction)
        self.menuEdit.addAction(self.moveByAction)
        self.menuEdit.addAction(self.moveOriginAction)
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.rotateAction)
        self.menuTools.addAction(self.readOnlyCellAction)
        self.menuCheck.addAction(self.viewCheckAction)

    def _createTriggers(self):
        self.readOnlyCellAction.triggered.connect(self.readOnlyCellClick)
        self.printAction.triggered.connect(self.printClick)
        self.printPreviewAction.triggered.connect(self.printPreviewClick)
        self.exportImageAction.triggered.connect(self.imageExportClick)
        self.exitAction.triggered.connect(self.closeWindow)
        self.fitAction.triggered.connect(self.fitToWindow)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.dispConfigAction.triggered.connect(self.dispConfigEdit)
        self.selectConfigAction.triggered.connect(self.selectConfigEdit)
        self.moveOriginAction.triggered.connect(self.moveOrigin)
        self.selectAllAction.triggered.connect(self.selectAllClick)
        self.deselectAllAction.triggered.connect(self.deselectAllClick)
        self.deleteAction.triggered.connect(self.deleteClick)

    def _createShortcuts(self):
        self.redoAction.setShortcut("Shift+U")
        self.undoAction.setShortcut(Qt.Key_U)
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut(Qt.Key_C)
        self.rotateAction.setShortcut("Ctrl+R")
        self.createTextAction.setShortcut("Shift+L")
        self.fitAction.setShortcut(Qt.Key_F)
        self.deleteAction.setShortcut(QKeySequence.Delete)
        self.selectAllAction.setShortcut("Ctrl+A")

    def dispConfigEdit(self):
        dcd = pdlg.displayConfigDialog(self)
        dcd.majorGridEntry.setText(str(self.majorGrid))
        dcd.snapDistanceEntry.setText(str(self.snapDistance))
        if dcd.exec() == QDialog.Accepted:
            self.majorGrid = int(float(dcd.majorGridEntry.text()))
            self.snapDistance = int(float(dcd.snapDistanceEntry.text()))
            self.gridTuple = (self.majorGrid, self.majorGrid)

            if dcd.dotType.isChecked():
                self.centralW.view.gridbackg = True
                self.centralW.view.linebackg = False
            elif dcd.lineType.isChecked():
                self.centralW.view.gridbackg = False
                self.centralW.view.linebackg = True
            else:
                self.centralW.view.gridbackg = False
                self.centralW.view.linebackg = False
            self.centralW.view.resetCachedContent()

    def selectConfigEdit(self):
        scd = pdlg.selectConfigDialogue(self)
        if self.centralW.scene.partialSelection:
            scd.partialSelection.setChecked(True)
        else:
            scd.fullSelection.setChecked(True)
        if scd.exec() == QDialog.Accepted:
            self.centralW.scene.partialSelection = scd.partialSelection.isChecked()

    def readOnlyCellClick(self):
        self.centralW.scene.readOnly = self.readOnlyCellAction.isChecked()

    def printClick(self):
        dlg = QPrintDialog(self)
        if dlg.exec() == QDialog.Accepted:
            printer = dlg.printer()
            printRunner = startThread(self.centralW.view.printView(printer))
            self.appMainW.threadPool.start(printRunner)
            self.logger.info(
                "Printing started"
            )  # self.centralW.view.printView(printer)

    def printPreviewClick(self):
        printer = QPrinter(QPrinter.ScreenResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        ppdlg = QPrintPreviewDialog(self)
        ppdlg.paintRequested.connect(self.centralW.view.printView)
        ppdlg.exec()

    def imageExportClick(self):
        image = QImage(
            self.centralW.view.viewport().size(), QImage.Format_ARGB32_Premultiplied
        )
        self.centralW.view.printView(image)
        fdlg = QFileDialog(self, caption="Select or create an image file")
        fdlg.setDefaultSuffix("png")
        fdlg.setFileMode(QFileDialog.AnyFile)
        fdlg.setViewMode(QFileDialog.Detail)
        fdlg.setNameFilter("Image Files (*.png *.jpg *.bmp *.gif *.jpeg")
        if fdlg.exec() == QDialog.Accepted:
            imageFile = fdlg.selectedFiles()[0]
            image.save(imageFile)

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItems()

    def selectAllClick(self):
        self.centralW.scene.selectAll()

    def deselectAllClick(self):
        self.centralW.scene.deselectAll()

    def fitToWindow(self):
        self.centralW.view.fitToView()

    def zoomIn(self):
        self.centralW.view.scale(1.25, 1.25)

    def zoomOut(self):
        self.centralW.view.scale(0.8, 0.8)

    def closeWindow(self):
        self.close()

    def closeEvent(self, event):
        cellViewTuple = ddef.viewTuple(self.libName, self.cellName, self.viewName)
        self.appMainW.openViews.pop(cellViewTuple)
        event.accept()

    def _createMenu(self):
        pass

    def moveOrigin(self):
        self.centralW.scene.changeOrigin = True

    def undoClick(self, s):
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()


class layoutEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict, libraryView) -> None:
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Layout Editor - {self.cellName} - {self.viewName}")
        self.setWindowIcon(QIcon(":/icons/edLayer-shape.png"))
        self.layoutViews = ["layout", "pcell"]
        self.layoutChooser = None
        self._addActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = layoutContainer(self)
        self.setCentralWidget(self.centralW)

    def _createActions(self):
        super()._createActions()
        self.exportGDSAction = QAction("Export GDS", self)

    def _addActions(self):
        super()._addActions()
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createRectAction)
        self.menuCreate.addAction(self.createWireAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuTools.addAction(self.exportGDSAction)

    def _createTriggers(self):
        super()._createTriggers()
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createInstAction.triggered.connect(self.createInstClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.exportGDSAction.triggered.connect(self.exportGDSClick)
        self.createWireAction.triggered.connect(self.createPathClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.createLabelAction.triggered.connect(self.createLabelClick)
        self.deleteAction.triggered.connect(self.deleteClick)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createRectAction.setShortcut(Qt.Key_R)
        self.createWireAction.setShortcut(Qt.Key_W)
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createPinAction.setShortcut(Qt.Key_P)
        self.createLabelAction.setShortcut(Qt.Key_L)

    def setDrawMode(self, *args):
        """
        Sets the drawing mode in the symbol editor.
        """
        self.centralW.scene.drawPin = args[0]  # draw pin
        self.centralW.scene.itemSelect = args[1]
        self.centralW.scene.drawArc = args[2]  # draw arc
        self.centralW.scene.drawRect = args[3]  # draw rect
        self.centralW.scene.drawPath = args[4]  # draw line
        self.centralW.scene.addLabel = args[5]
        self.centralW.scene.drawCircle = args[6]
        self.centralW.scene.rotateItem = args[7]

    def createRectClick(self, s):
        modeList = [False for _ in range(8)]
        modeList[3] = True
        self.setDrawMode(*modeList)

    def createPathClick(self, s):
        dlg = ldlg.pathSettingsDialogue(self)
        dlg.pathWidth.setText("1.0")
        self.centralW.scene.pathMode = [False for _ in range(5)]
        if dlg.exec() == QDialog.Accepted:
            if dlg.manhattanButton.isChecked():
                self.centralW.scene.pathMode[0] = True
            elif dlg.diagonalButton.isChecked():
                self.centralW.scene.pathMode[1] = True
            elif dlg.anyButton.isChecked():
                self.centralW.scene.pathMode[2] = True
            elif dlg.horizontalButton.isChecked():
                self.centralW.scene.pathMode[3] = True
            elif dlg.verticalButton.isChecked():
                self.centralW.scene.pathMode[4] = True
            if dlg.pathWidth.text().strip():
                self.centralW.scene.newPathWidth = fabproc.dbu * float(
                    dlg.pathWidth.text().strip()
                )
            else:
                self.centralW.scene.newPathWidth = fabproc.dbu * 1.0

        modeList = [False for _ in range(8)]
        modeList[4] = True
        self.setDrawMode(*modeList)

    def createPinClick(self):
        modeList = [False for _ in range(8)]
        modeList[0] = True
        self.setDrawMode(*modeList)
        dlg = ldlg.createLayoutPinDialog(self)
        pinLayersNames = [item.name for item in laylyr.pdkPinLayers]
        textLayersNames = [item.name for item in laylyr.pdkTextLayers]
        dlg.pinLayerCB.addItems(pinLayersNames)
        dlg.labelLayerCB.addItems(textLayersNames)

        if self.centralW.scene.newPinTuple is not None:
            dlg.pinLayerCB.setCurrentText(self.centralW.scene.newPinTuple.pinLayer.name)
        if self.centralW.scene.newLabelTuple is not None:
            dlg.labelLayerCB.setCurrentText(
                self.centralW.scene.newLabelTuple.labelLayer.name
            )
            dlg.familyCB.setCurrentText(self.centralW.scene.newLabelTuple.fontFamily)
            dlg.fontStyleCB.setCurrentText(self.centralW.scene.newLabelTuple.fontStyle)
            dlg.labelHeightCB.setCurrentText(
                str(self.centralW.scene.newLabelTuple.labelHeight)
            )
            dlg.labelAlignCB.setCurrentText(
                self.centralW.scene.newLabelTuple.labelAlign
            )
            dlg.labelOrientCB.setCurrentText(
                self.centralW.scene.newLabelTuple.labelOrient
            )
        if dlg.exec() == QDialog.Accepted:
            pinName = dlg.pinName.text()
            pinDir = dlg.pinDir.currentText()
            pinType = dlg.pinType.currentText()
            pinLayerName = dlg.pinLayerCB.currentText()
            pinLayer = [
                item for item in laylyr.pdkPinLayers if item.name == pinLayerName
            ][0]
            labelLayerName = dlg.labelLayerCB.currentText()
            labelLayer = [
                item for item in laylyr.pdkTextLayers if item.name == labelLayerName
            ][0]
            fontFamily = dlg.familyCB.currentText()
            fontStyle = dlg.fontStyleCB.currentText()
            labelHeight = float(dlg.labelHeightCB.currentText())
            labelAlign = dlg.labelAlignCB.currentText()
            labelOrient = dlg.labelOrientCB.currentText()
            self.centralW.scene.newPinTuple = ddef.layoutPinTuple(
                pinName, pinDir, pinType, pinLayer
            )
            self.centralW.scene.newLabelTuple = ddef.layoutLabelTuple(
                pinName,
                fontFamily,
                fontStyle,
                labelHeight,
                labelAlign,
                labelOrient,
                labelLayer,
            )

    def createLabelClick(self):
        modeList = [False for _ in range(8)]
        modeList[5] = True
        self.setDrawMode(*modeList)
        dlg = ldlg.createLayoutLabelDialog(self)
        textLayersNames = [item.name for item in laylyr.pdkTextLayers]
        dlg.labelLayerCB.addItems(textLayersNames)
        # if self.centralW.scene.newLabelTuple is not None:
        #     dlg.labelName.setText(self.centralW.scene.newLabelTuple.labelName)
        #     dlg.labelLayerCB.setCurrentText(
        #         self.centralW.scene.newLabelTuple.labelLayer.name
        #     )
        #     dlg.familyCB.setCurrentText(self.centralW.scene.newLabelTuple.fontFamily)
        #     dlg.fontStyleCB.setCurrentText(self.centralW.scene.newLabelTuple.fontStyle)
        #     dlg.labelHeightCB.setCurrentText(
        #         str(self.centralW.scene.newLabelTuple.labelHeight)
        #     )
        #     dlg.labelAlignCB.setCurrentText(
        #         self.centralW.scene.newLabelTuple.labelAlign
        #     )
        #     dlg.labelOrientCB.setCurrentText(
        #         self.centralW.scene.newLabelTuple.labelOrient
        #     )
        if dlg.exec() == QDialog.Accepted:
            labelName = dlg.labelName.text()
            labelLayerName = dlg.labelLayerCB.currentText()
            labelLayer = [
                item for item in laylyr.pdkTextLayers if item.name == labelLayerName
            ][0]
            fontFamily = dlg.familyCB.currentText()
            fontStyle = dlg.fontStyleCB.currentText()
            labelHeight = float(dlg.labelHeightCB.currentText())
            labelAlign = dlg.labelAlignCB.currentText()
            labelOrient = dlg.labelOrientCB.currentText()
            self.centralW.scene.newLabelTuple = ddef.layoutLabelTuple(
                labelName,
                fontFamily,
                fontStyle,
                labelHeight,
                labelAlign,
                labelOrient,
                labelLayer,
            )

    def checkSaveCell(self):
        self.centralW.scene.saveLayoutCell(self.file)

    def loadLayout(self):
        with open(self.file) as tempFile:
            items = json.load(tempFile)
        self.centralW.scene.loadLayoutCell(items)

    def createInstClick(self, s):

        # create a designLibrariesView
        libraryModel = layoutViewsModel(self.libraryDict, self.layoutViews)
        if self.layoutChooser is None:
            self.layoutChooser = fd.selectCellViewDialog(self, libraryModel)
            self.layoutChooser.show()
        else:
            self.layoutChooser.raise_()
        if self.layoutChooser.exec() == QDialog.Accepted:
            self.centralW.scene.addInstance = True
            libItem = libm.getLibItem(
                libraryModel, self.layoutChooser.libNamesCB.currentText()
            )
            cellItem = libm.getCellItem(
                libItem, self.layoutChooser.cellCB.currentText()
            )
            viewItem = libm.getViewItem(
                cellItem, self.layoutChooser.viewCB.currentText()
            )
            self.centralW.scene.layoutInstanceTuple = ddef.viewItemTuple(
                libItem, cellItem, viewItem
            )

    def exportGDSClick(self):
        dlg = fd.gdsExportDialogue(self)

        if dlg.exec() == QDialog.Accepted:
            exportPathObj = pathlib.Path(dlg.exportPathEdit.text().strip())
            layoutItems = self.centralW.scene.items()
            gdsExportObj = gdse.gdsExporter(self.cellName, layoutItems, exportPathObj)
            gdsExportObj.gds_export()

    def closeEvent(self, event):
        self.checkSaveCell()
        super().closeEvent(event)
        event.accept()


class schematicEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict, libraryView) -> None:
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Schematic Editor - {self.cellName} - {self.viewName}")
        self.setWindowIcon(QIcon(":/icons/edLayer-shape.png"))
        self.configDict = dict()
        self.processedCells = set()  # cells included in config view
        self.symbolChooser = None
        self.symbolViews = [
            "symbol"
        ]  # only symbol can be instantiated in the schematic window.
        self._schematicActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)

    def _createActions(self):

        super()._createActions()
        self.netNameAction = QAction("Net Name", self)
        self.netNameAction.setShortcut("l")
        self.hilightNetAction = QAction("Highlight Net", self)
        self.hilightNetAction.setCheckable(True)

    def _createTriggers(self):
        super()._createTriggers()
        self.checkCellAction.triggered.connect(self.checkSaveCellClick)
        self.saveCellAction.triggered.connect(self.saveCellClick)
        self.createWireAction.triggered.connect(self.createWireClick)
        self.createInstAction.triggered.connect(self.createInstClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.createTextAction.triggered.connect(self.createNoteClick)
        self.createSymbolAction.triggered.connect(self.createSymbolClick)
        self.copyAction.triggered.connect(self.copyClick)

        self.objPropAction.triggered.connect(self.objPropClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.netlistAction.triggered.connect(self.createNetlistClick)
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.simulateAction.triggered.connect(self.startSimClick)
        self.ignoreAction.triggered.connect(self.ignoreClick)
        self.goDownAction.triggered.connect(self.goDownClick)
        self.goUpAction.triggered.connect(self.goUpClick)
        self.hilightNetAction.triggered.connect(self.hilightNetClick)
        self.netNameAction.triggered.connect(self.netNameClick)

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuSimulation = self.editorMenuBar.addMenu("&Simulation")
        self.menuHelp = self.editorMenuBar.addMenu("&Help")
        self._addActions()

    def _addActions(self):
        super()._addActions()
        # edit menu

        self.menuEdit.addAction(self.netNameAction)

        self.propertyMenu = self.menuEdit.addMenu("Properties")
        self.propertyMenu.addAction(self.objPropAction)

        self.selectMenu = self.menuEdit.addMenu("Select")
        self.selectMenu.addAction(self.selectAllAction)
        self.selectMenu.addAction(self.deselectAllAction)

        # hierarchy submenu
        self.hierMenu = self.menuEdit.addMenu("Hierarchy")
        self.hierMenu.addAction(self.goUpAction)
        self.hierMenu.addAction(self.goDownAction)

        # create menu
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createWireAction)
        self.menuCreate.addAction(self.createBusAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createTextAction)
        self.menuCreate.addAction(self.createSymbolAction)

        # check menu
        self.menuCheck.addAction(self.viewErrorsAction)
        self.menuCheck.addAction(self.deleteErrorsAction)

        # tools menu
        self.menuTools.addAction(self.hilightNetAction)
        self.menuTools.addAction(self.netNameAction)

        # help menu

        self.menuSimulation.addAction(self.netlistAction)
        if self._app.revedasim_path:
            self.menuSimulation.addAction(self.simulateAction)

    def _createToolBars(self):
        super()._createToolBars()
        # toolbar.addAction(self.rulerAction)
        # toolbar.addAction(self.delRulerAction)
        self.toolbar.addAction(self.objPropAction)
        self.toolbar.addAction(self.viewPropAction)

        self.schematicToolbar = QToolBar("Schematic Toolbar", self)
        self.addToolBar(self.schematicToolbar)
        self.schematicToolbar.addAction(self.createInstAction)
        self.schematicToolbar.addAction(self.createWireAction)
        self.schematicToolbar.addAction(self.createBusAction)
        self.schematicToolbar.addAction(self.createPinAction)
        # self.schematicToolbar.addAction(self.createLabelAction)
        self.schematicToolbar.addAction(self.createSymbolAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.viewCheckAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.goDownAction)

    def _schematicActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)
        self.centralW.scene.itemContextMenu.addAction(self.ignoreAction)
        self.centralW.scene.itemContextMenu.addAction(self.goDownAction)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createWireAction.setShortcut(Qt.Key_W)
        self.createPinAction.setShortcut(Qt.Key_P)
        self.goDownAction.setShortcut("Shift+E")

    def createWireClick(self, s):
        self.centralW.scene.drawWire = True

    def createInstClick(self, s):

        # create a designLibrariesView
        libraryModel = symbolViewsModel(self.libraryDict, self.symbolViews)
        if self.symbolChooser is None:
            self.symbolChooser = fd.selectCellViewDialog(self, libraryModel)
            self.symbolChooser.show()
        else:
            self.symbolChooser.raise_()
        if self.symbolChooser.exec() == QDialog.Accepted:
            self.centralW.scene.addInstance = True
            libItem = libm.getLibItem(
                libraryModel, self.symbolChooser.libNamesCB.currentText()
            )
            cellItem = libm.getCellItem(
                libItem, self.symbolChooser.cellCB.currentText()
            )
            viewItem = libm.getViewItem(
                cellItem, self.symbolChooser.viewCB.currentText()
            )
            self.centralW.scene.instanceSymbolTuple = ddef.viewItemTuple(
                libItem, cellItem, viewItem
            )

    def createPinClick(self, s):
        createPinDlg = pdlg.createSchematicPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.centralW.scene.drawPin = True

    def createNoteClick(self, s):
        textDlg = pdlg.noteTextEdit(self)
        if textDlg.exec() == QDialog.Accepted:
            self.centralW.scene.noteText = textDlg.plainTextEdit.toPlainText()
            self.centralW.scene.noteFontFamily = textDlg.familyCB.currentText()
            self.centralW.scene.noteFontSize = textDlg.fontsizeCB.currentText()
            self.centralW.scene.noteFontStyle = textDlg.fontStyleCB.currentText()
            self.centralW.scene.noteAlign = textDlg.textAlignmCB.currentText()
            self.centralW.scene.noteOrient = textDlg.textOrientCB.currentText()
            self.centralW.scene.drawText = True

    def createSymbolClick(self, s):
        self.centralW.scene.createSymbol()

    def objPropClick(self, s):
        self.centralW.scene.viewObjProperties()

    def copyClick(self, s):
        self.centralW.scene.copySelectedItems()

    def rotateItemClick(self, s):
        self.centralW.scene.rotateItem = True
        self.centralW.scene.itemSelect = False

    def startSimClick(self, s):
        import revedasim.simMainWindow as smw

        simguiw = smw.simMainWindow(self)
        simguiw.show()

    def checkSaveCellClick(self):
        self.centralW.scene.groupAllNets()
        self.centralW.scene.saveSchematicCell(self.file)

    def saveCellClick(self):
        self.centralW.scene.saveSchematicCell(self.file)

    def loadSchematic(self):
        with open(self.file) as tempFile:
            items = json.load(tempFile)
        self.centralW.scene.loadSchematicCell(items)
        sceneNetsSet = self.centralW.scene.findSceneNetsSet()
        # because do not save dot points, it is necessary to recreate them.
        for netItem in sceneNetsSet:
            netItem.findDotPoints()

    def createConfigView(
        self,
        configItem: scb.viewItem,
        configDict: dict,
        newConfigDict: dict,
        processedCells: set,
    ):

        sceneSymbolSet = self.centralW.scene.findSceneSymbolSet()
        for item in sceneSymbolSet:
            libItem = libm.getLibItem(self.libraryView.libraryModel, item.libraryName)
            cellItem = libm.getCellItem(libItem, item.cellName)
            viewItems = [cellItem.child(row) for row in range(cellItem.rowCount())]
            viewNames = [viewItem.viewName for viewItem in viewItems]
            netlistableViews = [
                viewItemName
                for viewItemName in self.switchViewList
                if viewItemName in viewNames
            ]
            itemSwitchViewList = deepcopy(netlistableViews)
            viewDict = dict(zip(viewNames, viewItems))
            itemCellTuple = ddef.cellTuple(libItem.libraryName, cellItem.cellName)
            if itemCellTuple not in processedCells:
                if cellLine := configDict.get(cellItem.cellName):
                    netlistableViews = [cellLine[1]]
                for viewName in netlistableViews:
                    match viewDict[viewName].viewType:
                        case "schematic":
                            newConfigDict[cellItem.cellName] = [
                                libItem.libraryName,
                                viewName,
                                itemSwitchViewList,
                            ]
                            schematicObj = schematicEditor(
                                viewDict[viewName],
                                self.libraryDict,
                                self.libraryView,
                            )
                            schematicObj.loadSchematic()
                            schematicObj.createConfigView(
                                configItem,
                                configDict,
                                newConfigDict,
                                processedCells,
                            )
                            break
                        case other:
                            newConfigDict[cellItem.cellName] = [
                                libItem.libraryName,
                                viewName,
                                itemSwitchViewList,
                            ]
                            break
                processedCells.add(itemCellTuple)

    def closeEvent(self, event):
        self.centralW.scene.saveSchematicCell(self.file)
        super().closeEvent(event)
        event.accept()

    def createNetlistClick(self, s):
        dlg = fd.netlistExportDialogue(self)
        dlg.libNameEdit.setText(self.libName)
        dlg.cellNameEdit.setText(self.cellName)
        configViewItems = [
            self.cellItem.child(row)
            for row in range(self.cellItem.rowCount())
            if self.cellItem.child(row).viewType == "config"
        ]
        netlistableViews = [self.viewItem.viewName]
        for item in configViewItems:
            # is there a better way of doing it?
            with item.data(Qt.UserRole + 2).open(mode="r") as f:
                configItems = json.load(f)
                if configItems[1]["reference"] == self.viewItem.viewName:
                    netlistableViews.append(item.viewName)
        dlg.viewNameCombo.addItems(netlistableViews)
        if hasattr(self.appMainW, "simulationPath"):
            dlg.netlistDirEdit.setText(str(self.appMainW.simulationPath))
        if dlg.exec() == QDialog.Accepted:
            netlistObj = None
            try:
                self._startNetlisting(dlg, netlistObj)
            except Exception as e:
                self.logger.error(f"Error in creating netlist: {e}")

    def _startNetlisting(self, dlg, netlistObj):
        self.appMainW.simulationPath = pathlib.Path(dlg.netlistDirEdit.text())
        selectedViewName = dlg.viewNameCombo.currentText()
        self.switchViewList = [
            item.strip() for item in dlg.switchViewEdit.text().split(",")
        ]
        self.stopViewList = [dlg.stopViewEdit.text().strip()]
        subDirPathObj = self.appMainW.simulationPath.joinpath(self.cellName)
        subDirPathObj.mkdir(parents=True, exist_ok=True)
        netlistFilePathObj = subDirPathObj.joinpath(
            f"{self.cellName}_" f"{selectedViewName}"
        ).with_suffix(".cir")
        simViewName = dlg.viewNameCombo.currentText()
        if "schematic" in simViewName:
            netlistObj = xyceNetlist(self, netlistFilePathObj)
        elif "config" in simViewName:
            netlistObj = xyceNetlist(self, netlistFilePathObj, True)
            configItem = libm.findViewItem(
                self.libraryView.libraryModel,
                self.libName,
                self.cellName,
                dlg.viewNameCombo.currentText(),
            )
            with configItem.data(Qt.UserRole + 2).open(mode="r") as f:
                netlistObj.configDict = json.load(f)[2]

        if netlistObj:
            xyceNetlRunner = startThread(netlistObj.writeNetlist())
            self.appMainW.threadPool.start(xyceNetlRunner)
            # netlistObj.writeNetlist()
            self.logger.info("Netlisting finished.")

    def goDownClick(self, s):
        self.centralW.scene.goDownHier()

    def goUpClick(self, s):
        self.centralW.scene.goUpHier()

    def ignoreClick(self, s):
        self.centralW.scene.ignoreSymbol()

    def netNameClick(self, s):
        self.centralW.scene.netNameEdit()

    def hilightNetClick(self, s):
        self.centralW.scene.hilightNets()


class symbolEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict, libraryView):
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Symbol Editor - {self.cellName} - {self.viewName}")
        self._symbolActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = symbolContainer(self)
        self.setCentralWidget(self.centralW)

    def _createActions(self):
        super()._createActions()

    def _createShortcuts(self):
        super()._createShortcuts()
        self.stretchAction.setShortcut(Qt.Key_M)
        self.createRectAction.setShortcut(Qt.Key_R)
        self.createLineAction.setShortcut(Qt.Key_W)
        self.createLabelAction.setShortcut(Qt.Key_L)
        self.createPinAction.setShortcut(Qt.Key_P)

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuHelp = self.editorMenuBar.addMenu("&Help")
        self._addActions()

    def _createToolBars(self):  # redefine the toolbar in the editorWindow class
        super()._createToolBars()
        self.symbolToolbar = QToolBar("Symbol Toolbar", self)
        self.addToolBar(self.symbolToolbar)
        self.symbolToolbar.addAction(self.createLineAction)
        self.symbolToolbar.addAction(self.createRectAction)
        self.symbolToolbar.addAction(self.createPolyAction)
        self.symbolToolbar.addAction(self.createCircleAction)
        self.symbolToolbar.addAction(self.createArcAction)
        self.symbolToolbar.addAction(self.createLabelAction)
        self.symbolToolbar.addAction(self.createPinAction)

    def _addActions(self):
        super()._addActions()
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.viewPropAction)
        self.selectMenu = self.menuEdit.addMenu("Select")
        self.selectMenu.addAction(self.selectAllAction)
        self.selectMenu.addAction(self.deselectAllAction)
        self.menuCreate.addAction(self.createLineAction)
        self.menuCreate.addAction(self.createRectAction)
        self.menuCreate.addAction(self.createPolyAction)
        self.menuCreate.addAction(self.createCircleAction)
        self.menuCreate.addAction(self.createArcAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)

    def _createTriggers(self):
        super()._createTriggers()
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createLineAction.triggered.connect(self.createLineClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.createPolyAction.triggered.connect(self.createPolyClick)
        self.createArcAction.triggered.connect(self.createArcClick)
        self.createCircleAction.triggered.connect(self.createCircleClick)
        self.createLabelAction.triggered.connect(self.createLabelClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.objPropAction.triggered.connect(self.objPropClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.stretchAction.triggered.connect(self.stretchClick)
        self.viewPropAction.triggered.connect(self.viewPropClick)

    def _symbolActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.stretchAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)

    def objPropClick(self):
        self.centralW.scene.itemProperties()

    def checkSaveCell(self):
        self.centralW.scene.saveSymbolCell(self.file)

    def setDrawMode(self, *args):
        """
        Sets the drawing mode in the symbol editor.
        """
        self.centralW.scene.drawPin = args[0]
        self.centralW.scene.itemSelect = args[1]
        self.centralW.scene.drawArc = args[2]  # draw arc
        self.centralW.scene.drawRect = args[3]  # draw rect
        self.centralW.scene.drawLine = args[4]  # draw line
        self.centralW.scene.addLabel = args[5]
        self.centralW.scene.drawCircle = args[6]
        self.centralW.scene.rotateItem = args[7]

    def createRectClick(self, s):
        modeList = [False for _ in range(8)]
        modeList[3] = True
        self.setDrawMode(*modeList)

    def createLineClick(self, s):
        modeList = [False for _ in range(8)]
        modeList[4] = True
        self.setDrawMode(*modeList)

    def createPolyClick(self, s):
        pass

    def createArcClick(self, s):
        modeList = [False for _ in range(8)]
        modeList[2] = True
        self.setDrawMode(*modeList)

    def createCircleClick(self, s):
        modeList = [False for _ in range(8)]
        modeList[6] = True
        self.setDrawMode(*modeList)

    def createPinClick(self, s):
        createPinDlg = pdlg.createPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            modeList = [False for _ in range(8)]
            modeList[0] = True
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.setDrawMode(*modeList)

    def rotateItemClick(self, s):
        self.centralW.scene.rotateItem = True
        modeList = [False for _ in range(8)]
        modeList[7] = True
        self.setDrawMode(*modeList)
        self.messageLine.setText("Click on an item to rotate CW 90 degrees.")

    def copyClick(self, s):
        self.centralW.scene.copySelectedItems()

    def stretchClick(self, s):
        self.centralW.scene.stretchSelectedItem()

    def viewPropClick(self, s):
        self.centralW.scene.viewSymbolProperties()

    def loadSymbol(self):
        """
        symbol is loaded to the scene.
        """
        with open(self.file) as tempFile:
            try:
                items = json.load(tempFile)
            except json.decoder.JSONDecodeError:
                self.logger.error("Cannot load symbol. JSON Decode Error")
        self.centralW.scene.loadSymbol(items)

    def createLabelClick(self):
        createLabelDlg = pdlg.createSymbolLabelDialog(self)
        self.messageLine.setText("Place a label")
        createLabelDlg.labelHeightEdit.setText("12")
        if createLabelDlg.exec() == QDialog.Accepted:
            modeList = [False for _ in range(8)]
            modeList[5] = True
            self.setDrawMode(*modeList)
            # directly setting scene class attributes here to pass the information.
            self.centralW.scene.labelDefinition = createLabelDlg.labelDefinition.text()
            self.centralW.scene.labelHeight = (
                createLabelDlg.labelHeightEdit.text().strip()
            )
            self.centralW.scene.labelAlignment = (
                createLabelDlg.labelAlignCombo.currentText()
            )
            self.centralW.scene.labelOrient = (
                createLabelDlg.labelOrientCombo.currentText()
            )
            self.centralW.scene.labelUse = createLabelDlg.labelUseCombo.currentText()
            self.centralW.scene.labelOpaque = (
                createLabelDlg.labelVisiCombo.currentText() == "Yes"
            )
            self.centralW.scene.labelType = "Normal"  # default button
            if createLabelDlg.normalType.isChecked():
                self.centralW.scene.labelType = "Normal"
            elif createLabelDlg.NLPType.isChecked():
                self.centralW.scene.labelType = "NLPLabel"
            elif createLabelDlg.pyLType.isChecked():
                self.centralW.scene.labelType = "PyLabel"

    def closeEvent(self, event):
        """
        Closes the application.
        """
        super().closeEvent(event)
        self.centralW.scene.saveSymbolCell(self.file)
        event.accept()


class symbolContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.scene = symbol_scene(self)
        self.view = symbol_view(self.scene, self)
        self.init_UI()

    def init_UI(self):
        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class schematicContainer(QWidget):
    def __init__(self, parent: schematicEditor):
        super().__init__(parent=parent)
        assert isinstance(parent, schematicEditor)
        self.parent = parent
        self.scene = schematic_scene(self)
        self.view = schematic_view(self.scene, self)
        self.init_UI()

    def init_UI(self):
        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class layoutContainer(QWidget):
    def __init__(self, parent: layoutEditor):
        super().__init__(parent=parent)
        assert isinstance(parent, layoutEditor)
        self.parent = parent
        self.lswModel = lsw.layerDataModel(laylyr.pdkAllLayers)
        self.lswWidget = lsw.layerViewTable(self, self.lswModel)
        self.lswWidget.dataSelected.connect(self.layerSelected)
        self.scene = layout_scene(self)
        self.view = layout_view(self.scene, self)
        self.init_UI()

    def init_UI(self):
        # there could be other widgets in the grid layout, such as edLayer
        # viewer/editor.
        vLayout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        splitter.insertWidget(0, self.lswWidget)
        splitter.insertWidget(1, self.view)
        # ratio of first column to second column is 5
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)
        vLayout.addWidget(splitter)

        self.setLayout(vLayout)

    def layerSelected(self, layerName):
        self.scene.selectEdLayer = [
            item for item in laylyr.pdkLayoutLayers if item.name == layerName
        ][0]


class editor_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editorWindow = self.parent.parent
        self.majorGrid = self.editorWindow.majorGrid
        self.gridTuple = self.editorWindow.gridTuple
        self.mousePressLoc = None
        self.mouseMoveLoc = None
        self.mouseReleaseLoc = None
        self.readOnly = False  # if the scene is not editable
        self.undoStack = QUndoStack()
        self.changeOrigin = False
        self.origin = QPoint(0, 0)
        self.snapDistance = self.editorWindow.snapDistance
        self.cellName = self.editorWindow.file.parent.stem
        self.partialSelection = True
        self.selectionRectItem = None
        self.libraryDict = self.editorWindow.libraryDict
        self.rotateItem = False
        self.itemContextMenu = QMenu()
        self.appMainW = self.editorWindow.appMainW
        self.logger = self.appMainW.logger
        self.messageLine = self.editorWindow.messageLine
        self.statusLine = self.editorWindow.statusLine
        self.itemsAtMousePress = list()
        self.installEventFilter(self)

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(base * int(round(number / base)))

    def snapToGrid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            self.snapToBase(point.x(), gridTuple[0]),
            self.snapToBase(point.y(), gridTuple[1]),
        )

    def rotateSelectedItems(self, point: QPoint):
        """
        Rotate selected items by 90 degree.
        """
        for item in self.selectedItems():
            self.rotateAnItem(point, item, 90)
        self.rotateItem = False
        self.itemSelect = True

    def rotateAnItem(self, point: QPoint, item, angle):
        rotationOriginPoint = item.mapFromScene(point)
        item.setTransformOriginPoint(rotationOriginPoint)
        item.angle += angle
        item.setRotation(item.angle)
        undoCommand = us.undoRotateShape(self, item, item.angle)
        self.undoStack.push(undoCommand)

    def eventFilter(self, source, event):
        """
        Mouse events should snap to background grid points.
        """
        if self.readOnly:  # if read only do not propagate any mouse events
            return True
        elif event.type() in [
            QEvent.GraphicsSceneMouseMove,
            QEvent.GraphicsSceneMousePress,
            QEvent.GraphicsSceneMouseRelease,
        ]:
            event.setScenePos(
                self.snapToGrid(event.scenePos(), self.gridTuple).toPointF()
            )
            return False
        else:
            return super().eventFilter(source, event)

    def selectSceneItems(self, modifiers):
        """
        Selects scene items based on the given modifiers.
        A selection rectangle is drawn if ShiftModifier is pressed,
        else a single item is selected. The function does not return anything.

        :param modifiers: The keyboard modifiers that determine the selection type.
        :type modifiers: Qt.KeyboardModifiers
        """
        if modifiers == Qt.ShiftModifier:
            self.editorWindow.messageLine.setText("Draw Selection Rectangle")
            self.selectionRectItem = QGraphicsRectItem(
                QRectF(self.mousePressLoc, self.mousePressLoc)
            )
            self.selectionRectItem.setPen(schlyr.draftPen)
            self.addItem(self.selectionRectItem)
        else:
            self.editorWindow.messageLine.setText("Select an item")
            itemsAtMousePress = self.items(self.mousePressLoc)
            if itemsAtMousePress:
                [item.setSelected(True) for item in itemsAtMousePress]
        self.editorWindow.messageLine.setText(
            "Item selected" if self.selectedItems() else "Nothing selected"
        )

    def selectInRectItems(self, selectionRect: QRect, partialSelection=False):
        """
        Select items in the scene.
        """

        mode = Qt.IntersectsItemShape if partialSelection else Qt.ContainsItemShape
        [item.setSelected(True) for item in self.items(selectionRect, mode=mode)]

    def selectAll(self):
        """
        Select all items in the scene.
        """
        [item.setSelected(True) for item in self.items()]

    def deselectAll(self):
        """
        Deselect all items in the scene.
        """
        [item.setSelected(False) for item in self.selectedItems()]

    def deleteSelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                # self.removeItem(item)
                undoCommand = us.deleteShapeUndo(self, item)
                self.undoStack.push(undoCommand)
            self.update()  # self.selectMode()


class symbol_scene(editor_scene):
    """
    Scene for Symbol editor.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # drawing switches
        self.selectMode()  # reset to select mode
        self.drawPin = False
        self.itemSelect = False
        self.drawArc = False  # draw arc
        self.drawRect = False  # draw rect
        self.drawLine = False  # draw line
        self.addLabel = False  # add label
        self.drawCircle = False  # draw Circle
        self.rotateItem = False
        self.symbolShapes = ["line", "arc", "rect", "circle", "pin", "label"]
        self.changeOrigin = False
        self.origin = QPoint(0, 0)
        # some default attributes
        self.newPin = None
        self.pinName = ""
        self.pinType = shp.pin.pinTypes[0]
        self.pinDir = shp.pin.pinDirs[0]
        self.labelDefinition = ""
        self.labelType = shp.label.labelTypes[0]
        self.labelOrient = shp.label.labelOrients[0]
        self.labelAlignment = shp.label.labelAlignments[0]
        self.labelUse = shp.label.labelUses[0]
        self.labelVisible = False
        self.labelHeight = "12"
        self.labelOpaque = True
        self.newLine = None
        self.newRect = None
        self.newCirc = None
        self.newArc = None

    @property
    def drawMode(self):
        return any(
            (
                self.drawPin,
                self.drawArc,
                self.drawRect,
                self.drawLine,
                self.addLabel,
                self.drawCircle,
                self.rotateItem,
            )
        )

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        try:
            modifiers = QGuiApplication.keyboardModifiers()
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()
            if mouse_event.button() == Qt.LeftButton:
                self.mousePressLoc = mouse_event.scenePos().toPoint()
                if self.changeOrigin:  # change origin of the symbol
                    self.origin = self.mousePressLoc
                    self.changeOrigin = False
                if self.itemSelect:
                    self.selectSceneItems(modifiers)
                if self.drawPin:
                    self.editorWindow.messageLine.setText("Add Symbol Pin")
                    self.newPin = self.pinDraw(self.mousePressLoc)
                    self.newPin.setSelected(True)
                elif self.drawLine:
                    self.editorWindow.messageLine.setText("Drawing a Line")
                    self.newLine = self.lineDraw(self.mousePressLoc, self.mousePressLoc)
                    self.newLine.setSelected(True)
                elif self.addLabel:
                    self.newLabel = self.labelDraw(
                        self.mousePressLoc,
                        self.labelDefinition,
                        self.labelType,
                        self.labelHeight,
                        self.labelAlignment,
                        self.labelOrient,
                        self.labelUse,
                    )
                    self.newLabel.setSelected(True)
                elif self.drawRect:
                    self.newRect = self.rectDraw(self.mousePressLoc, self.mousePressLoc)
                elif self.drawCircle:
                    self.editorWindow.messageLine.setText(
                        "Click on the center of the circle"
                    )
                    self.newCircle = self.circleDraw(
                        self.mousePressLoc, self.mousePressLoc
                    )
                elif self.drawArc:
                    self.editorWindow.messageLine.setText("Start drawing an arc")
                    self.newArc = self.arcDraw(self.mousePressLoc, self.mousePressLoc)
                if self.rotateItem and self.selectedItems:
                    self.rotateSelectedItems(self.mousePressLoc)
        except Exception as e:
            print(e)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:

        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if self.drawLine:
                self.editorWindow.messageLine.setText("Release mouse on the end point")
                self.newLine.end = self.mouseMoveLoc
            elif self.drawPin and self.newPin.isSelected():
                self.newPin.setPos(self.mouseMoveLoc - self.mousePressLoc)
            elif self.drawRect:
                self.editorWindow.messageLine.setText(
                    "Release mouse on the bottom left point"
                )
                self.newRect.end = self.mouseMoveLoc
            elif self.drawCircle:
                self.editorWindow.messageLine.setText("Extend Circle")
                radius = (
                    (self.mouseMoveLoc.x() - self.mousePressLoc.x()) ** 2
                    + (self.mouseMoveLoc.y() - self.mousePressLoc.y()) ** 2
                ) ** 0.5
                self.newCircle.radius = radius
            elif self.drawArc:
                self.editorWindow.messageLine.setText("Extend Arc")
                self.newArc.end = self.mouseMoveLoc
            elif self.itemSelect and modifiers == Qt.ShiftModifier:
                self.selectionRectItem.setRect(
                    QRectF(self.mousePressLoc, self.mouseMoveLoc)
                )
        self.statusLine.showMessage(
            f"Cursor Position: {(self.mouseMoveLoc - self.origin).toTuple()}"
        )

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        try:
            self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                if self.drawLine:
                    self.newLine.setSelected(False)
                elif self.drawCircle:
                    self.newCircle.setSelected(False)
                    self.newCircle.update()
                elif self.drawPin:
                    self.newPin.setSelected(False)
                    self.newPin = None
                elif self.drawRect:
                    self.newRect.setSelected(False)
                elif self.drawArc:
                    self.newArc.setSelected(False)
                elif self.addLabel:
                    self.newLabel.setSelected(False)
                    self.addLabel = False
                elif self.itemSelect and modifiers == Qt.ShiftModifier:
                    self.selectInRectItems(
                        self.selectionRectItem.rect(), self.partialSelection
                    )
                    self.removeItem(self.selectionRectItem)
                    self.selectionRectItem = None
        except Exception as e:
            print(e)

            self.selectMode()

    def lineDraw(self, start: QPoint, current: QPoint):
        line = shp.line(start, current, self.gridTuple)
        # self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        return line

    def rectDraw(self, start: QPoint, end: QPoint):
        """
        Draws a rectangle on the scene
        """
        # rect = shp.rectangle(start, end - QPoint(pen.width() / 2, pen.width() / 2), pen,
        #                      gridTuple)
        rect = shp.rectangle(start, end, self.gridTuple)
        # self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        return rect

    def circleDraw(self, start: QPoint, end: QPoint):
        """
        Draws a circle on the scene
        """
        # snappedEnd = self.snapToGrid(end, gridTuple)
        circle = shp.circle(start, end, self.gridTuple)
        # self.addItem(circle)
        undoCommand = us.addShapeUndo(self, circle)
        self.undoStack.push(undoCommand)
        return circle

    def arcDraw(self, start: QPoint, end: QPoint):
        """
        Draws an arc inside the rectangle defined by start and end points.
        """
        arc = shp.arc(start, end, self.gridTuple)
        # self.addItem(arc)
        undoCommand = us.addShapeUndo(self, arc)
        self.undoStack.push(undoCommand)
        return arc

    def pinDraw(self, current):
        pin = shp.pin(current, self.pinName, self.pinDir, self.pinType, self.gridTuple)
        # self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        return pin

    def labelDraw(
        self,
        current,
        labelDefinition,
        labelType,
        labelHeight,
        labelAlignment,
        labelOrient,
        labelUse,
    ):
        label = shp.label(
            current,
            labelDefinition,
            labelType,
            labelHeight,
            labelAlignment,
            labelOrient,
            labelUse,
            self.gridTuple,
        )
        label.labelVisible = self.labelOpaque
        label.labelDefs()
        label.setOpacity(1)
        # self.addItem(label)
        undoCommand = us.addShapeUndo(self, label)
        self.undoStack.push(undoCommand)
        return label

    def keyPressEvent(self, key_event):
        super().keyPressEvent(key_event)
        if key_event.key() == Qt.Key_Escape:
            self.selectMode()
        elif key_event.key() == Qt.Key_C:
            self.copySelectedItems()
        elif key_event.key() == Qt.Key_M:
            self.stretchSelectedItem()

    def selectMode(self):
        """
        Reset the scene mode to default. Select mode is set to True.
        """
        self.editorWindow.messageLine.setText("Select Mode")
        self.drawPin = False
        self.itemSelect = True
        self.drawArc = False  # draw arc
        self.drawRect = False  # draw rect
        self.drawLine = False  # draw line
        self.addLabel = False
        self.drawCircle = False
        self.rotateItem = False

    def copySelectedItems(self):
        if hasattr(self, "selectedItems"):
            for item in self.selectedItems():
                selectedItemJson = json.dumps(item, cls=se.symbolEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.createSymbolItems(itemCopyDict, self.gridTuple)
                self.addItem(shape)
                undoCommand = us.addShapeUndo(self, shape)
                self.undoStack.push(undoCommand)
                # shift position by one grid unit to right and down
                shape.setPos(
                    QPoint(
                        item.pos().x() + 2 * self.gridTuple[0],
                        item.pos().y() + 2 * self.gridTuple[1],
                    )
                )

    def itemProperties(self):
        """
        When item properties is queried.
        """
        if not self.selectedItems():
            return
        for item in self.selectedItems():
            if isinstance(item, shp.rectangle):
                self.queryDlg = pdlg.rectPropertyDialog(self.editorWindow)
                [left, top, width, height] = item.rect.getRect()
                sceneTopLeftPoint = item.mapToScene(QPoint(left, top))
                self.queryDlg.rectLeftLine.setText(str(sceneTopLeftPoint.x()))
                self.queryDlg.rectTopLine.setText(str(sceneTopLeftPoint.y()))
                self.queryDlg.rectWidthLine.setText(str(width))  # str(width))
                self.queryDlg.rectHeightLine.setText(str(height))  # str(height))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateRectangleShape(item)
            if isinstance(item, shp.circle):
                self.queryDlg = pdlg.circlePropertyDialog(self.editorWindow)
                centre = item.mapToScene(item.centre).toTuple()
                radius = item.radius
                self.queryDlg.centerXEdit.setText(str(centre[0]))
                self.queryDlg.centerYEdit.setText(str(centre[1]))
                self.queryDlg.radiusEdit.setText(str(radius))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateCircleShape(item)
            if isinstance(item, shp.arc):
                self.queryDlg = pdlg.arcPropertyDialog(self.editorWindow)
                sceneStartPoint = item.mapToScene(item.start)
                self.queryDlg.startXEdit.setText(str(sceneStartPoint.x()))
                self.queryDlg.startYEdit.setText(str(sceneStartPoint.y()))
                self.queryDlg.widthEdit.setText(str(item.width))
                self.queryDlg.heightEdit.setText(str(item.height))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateArcShape(item)
            elif isinstance(item, shp.line):
                self.queryDlg = pdlg.linePropertyDialog(self.editorWindow)
                sceneLineStartPoint = item.mapToScene(item.start).toPoint()
                sceneLineEndPoint = item.mapToScene(item.end).toPoint()
                self.queryDlg.startXLine.setText(str(sceneLineStartPoint.x()))
                self.queryDlg.startYLine.setText(str(sceneLineStartPoint.y()))
                self.queryDlg.endXLine.setText(str(sceneLineEndPoint.x()))
                self.queryDlg.endYLine.setText(str(sceneLineEndPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLineShape(item)
            elif isinstance(item, shp.pin):
                self.queryDlg = pdlg.pinPropertyDialog(self.editorWindow)
                self.queryDlg.pinName.setText(str(item.pinName))
                self.queryDlg.pinType.setCurrentText(item.pinType)
                self.queryDlg.pinDir.setCurrentText(item.pinDir)
                sceneStartPoint = item.mapToScene(item.start).toPoint()
                self.queryDlg.pinXLine.setText(str(sceneStartPoint.x()))
                self.queryDlg.pinYLine.setText(str(sceneStartPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updatePinShape(item)
            elif isinstance(item, shp.label):
                self.queryDlg = pdlg.labelPropertyDialog(self.editorWindow)
                self.queryDlg.labelDefinition.setText(str(item.labelDefinition))
                self.queryDlg.labelHeightEdit.setText(str(item.labelHeight))
                self.queryDlg.labelAlignCombo.setCurrentText(item.labelAlign)
                self.queryDlg.labelOrientCombo.setCurrentText(item.labelOrient)
                self.queryDlg.labelUseCombo.setCurrentText(item.labelUse)
                if item.labelVisible:
                    self.queryDlg.labelVisiCombo.setCurrentText("Yes")
                else:
                    self.queryDlg.labelVisiCombo.setCurrentText("No")
                if item.labelType == "Normal":
                    self.queryDlg.normalType.setChecked(True)
                elif item.labelType == "NLPLabel":
                    self.queryDlg.NLPType.setChecked(True)
                elif item.labelType == "PyLabel":
                    self.queryDlg.pyLType.setChecked(True)
                sceneStartPoint = item.mapToScene(item.start)
                self.queryDlg.labelXLine.setText(str(sceneStartPoint.x()))
                self.queryDlg.labelYLine.setText(str(sceneStartPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLabelShape(item)

    def updateRectangleShape(self, item: shp.rectangle):
        """
        Both dictionaries have the topleft corner of rectangle in scene coordinates.
        """
        origItemList = item.rect.getRect()  # in item coordinates
        left = self.snapToBase(
            float(self.queryDlg.rectLeftLine.text()), self.gridTuple[0]
        )
        top = self.snapToBase(
            float(self.queryDlg.rectTopLine.text()), self.gridTuple[1]
        )
        width = self.snapToBase(
            float(self.queryDlg.rectWidthLine.text()), self.gridTuple[0]
        )
        height = self.snapToBase(
            float(self.queryDlg.rectHeightLine.text()), self.gridTuple[1]
        )
        topLeftPoint = item.mapFromScene(QPoint(left, top))
        newItemList = [topLeftPoint.x(), topLeftPoint.y(), width, height]
        # topLeft = item.mapFromScene(QPoint(left, top))
        # item.rect = QRect(topLeft.x(), topLeft.y(), width, height)
        undoCommand = us.updateSymRectUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateCircleShape(self, item: shp.circle):
        origItemList = [item.centre.x(), item.centre.y(), item.radius]
        centerX = self.snapToBase(
            float(self.queryDlg.centerXEdit.text()), self.gridTuple[0]
        )
        centerY = self.snapToBase(
            float(self.queryDlg.centerYEdit.text()), self.gridTuple[1]
        )
        radius = self.snapToBase(
            float(self.queryDlg.radiusEdit.text()), self.gridTuple[0]
        )
        centrePoint = item.mapFromScene(
            self.snapToGrid(QPoint(centerX, centerY), self.gridTuple)
        )
        newItemList = [centrePoint.x(), centrePoint.y(), radius]
        undoCommand = us.updateSymCircleUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateArcShape(self, item: shp.arc):
        origItemList = [item.start.x(), item.start.y(), item.width, item.height]
        startX = self.snapToBase(
            float(self.queryDlg.startXEdit.text()), self.gridTuple[0]
        )
        startY = self.snapToBase(
            float(self.queryDlg.startYEdit.text()), self.gridTuple[1]
        )
        start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        width = self.snapToBase(
            float(self.queryDlg.widthEdit.text()), self.gridTuple[0]
        )
        height = self.snapToBase(
            float(self.queryDlg.heightEdit.text()), self.gridTuple[1]
        )
        newItemList = [start.x(), start.y(), width, height]
        undoCommand = us.updateSymArcUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateLineShape(self, item: shp.line):
        """
        Updates line shape from dialogue entries.
        """
        origItemList = [item.start.x(), item.start.y(), item.end.x(), item.end.y()]
        startX = self.snapToBase(
            float(self.queryDlg.startXLine.text()), self.gridTuple[0]
        )
        startY = self.snapToBase(
            float(self.queryDlg.startYLine.text()), self.gridTuple[1]
        )
        endX = self.snapToBase(float(self.queryDlg.endXLine.text()), self.gridTuple[0])
        endY = self.snapToBase(float(self.queryDlg.endYLine.text()), self.gridTuple[1])
        start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        end = item.mapFromScene(QPoint(endX, endY)).toPoint()
        newItemList = [start.x(), start.y(), end.x(), end.y()]
        undoCommand = us.updateSymLineUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updatePinShape(self, item: shp.pin):
        origItemList = [
            item.start.x(),
            item.start.y(),
            item.pinName,
            item.pinDir,
            item.pinType,
        ]
        sceneStartX = self.snapToBase(
            float(self.queryDlg.pinXLine.text()), self.gridTuple[0]
        )
        sceneStartY = self.snapToBase(
            float(self.queryDlg.pinYLine.text()), self.gridTuple[1]
        )

        start = item.mapFromScene(QPoint(sceneStartX, sceneStartY)).toPoint()
        pinName = self.queryDlg.pinName.text()
        pinType = self.queryDlg.pinType.currentText()
        pinDir = self.queryDlg.pinDir.currentText()
        newItemList = [start.x(), start.y(), pinName, pinDir, pinType]
        undoCommand = us.updateSymPinUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateLabelShape(self, item: shp.label):
        """
        update label with new values.
        """
        origItemList = [
            item.start.x(),
            item.start.y(),
            item.labelDefinition,
            item.labelType,
            item.labelHeight,
            item.labelAlign,
            item.labelOrient,
            item.labelUse,
        ]
        sceneStartX = self.snapToBase(
            float(self.queryDlg.labelXLine.text()), self.gridTuple[0]
        )
        sceneStartY = self.snapToBase(
            float(self.queryDlg.labelYLine.text()), self.gridTuple[1]
        )
        start = item.mapFromScene(QPoint(sceneStartX, sceneStartY))
        labelDefinition = self.queryDlg.labelDefinition.text()
        labelHeight = self.queryDlg.labelHeightEdit.text()
        labelAlign = self.queryDlg.labelAlignCombo.currentText()
        labelOrient = self.queryDlg.labelOrientCombo.currentText()
        labelUse = self.queryDlg.labelUseCombo.currentText()
        labelVisible = self.queryDlg.labelVisiCombo.currentText() == "Yes"
        if self.queryDlg.normalType.isChecked():
            labelType = shp.label.labelTypes[0]
        elif self.queryDlg.NLPType.isChecked():
            labelType = shp.label.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            labelType = shp.label.labelTypes[2]
        # set opacity to 1 so that the label is still visible on symbol editor
        item.setOpacity(1)
        newItemList = [
            start.x(),
            start.y(),
            labelDefinition,
            labelType,
            labelHeight,
            labelAlign,
            labelOrient,
            labelUse,
        ]
        undoCommand = us.updateSymLabelUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def loadSymbol(self, itemsList: list):
        self.attributeList = []
        for item in itemsList[1:]:
            if item is not None:
                if item["type"] in self.symbolShapes:
                    itemShape = lj.createSymbolItems(item, self.gridTuple)
                    # items should be always visible in symbol view
                    if isinstance(itemShape, shp.label):
                        itemShape.setOpacity(1)
                    self.addItem(itemShape)
                elif item["type"] == "attr":
                    attr = lj.createSymbolAttribute(item)
                    self.attributeList.append(attr)

    def saveSymbolCell(self, fileName):
        # items = self.items(self.sceneRect())  # get items in scene rect
        items = self.items()
        items.insert(0, {"cellView": "symbol"})
        if hasattr(self, "attributeList"):
            items.extend(self.attributeList)  # add attribute list to list
        with open(fileName, "w") as f:
            try:
                json.dump(items, f, cls=se.symbolEncoder, indent=4)
            except Exception as e:
                self.logger.error(e)

    def stretchSelectedItem(self):
        if self.selectedItems() is not None:
            try:
                for item in self.selectedItems():
                    if hasattr(item, "stretch"):
                        item.stretch = True

            except AttributeError:
                self.messageLine.setText("Nothing selected")

    def viewSymbolProperties(self):
        """
        View symbol properties dialog.
        """
        # copy symbol attribute list to another list by deepcopy to be safe
        attributeListCopy = deepcopy(self.attributeList)
        symbolPropDialogue = pdlg.symbolLabelsDialogue(
            self.parent.parent, self.items(), attributeListCopy
        )
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = symbolPropDialogue.labelHeightList[i].text()
                item.labelAlign = symbolPropDialogue.labelAlignmentList[i].currentText()
                item.labelOrient = symbolPropDialogue.labelOrientationList[
                    i
                ].currentText()
                item.labelUse = symbolPropDialogue.labelUseList[i].currentText()
                item.labelType = symbolPropDialogue.labelTypeList[i].currentText()
                item.update(item.boundingRect())
            # create an empty attribute list. If the dialog is OK, the local attribute list
            # will be copied to the symbol attribute list.
            localAttributeList = []
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    localAttributeList.append(
                        se.symbolAttribute(
                            item.text(), symbolPropDialogue.attributeDefList[i].text()
                        )
                    )
                self.attributeList = deepcopy(localAttributeList)


class schematic_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.instCounter = 0
        self.start = QPoint(0, 0)
        self.current = QPoint(0, 0)
        self.itemsAtMousePress = list()
        self.drawWire = False  # flag to add wire
        self.drawPin = False  # flag to add pin
        self.drawText = False  # flat to add text
        self.itemSelect = True  # flag to select item
        self.drawMode = self.drawWire or self.drawPin
        self.draftPin = None
        self.draftText = None
        self.itemCounter = 0
        self.netCounter = 0
        self.schematicNets = {}  # netName: list of nets with the same name
        self.crossDots = set()  # list of cross dots
        self.draftItem = None
        self.viewRect = None
        # add instance attributes
        self.addInstance = False
        self.instanceSymbolTuple = None
        # pin attribute defaults
        self.pinName = ""
        self.pinType = "Signal"
        self.pinDir = "Input"
        self.parentView = None
        self.wires = None
        self.newInstance = None
        self.newPin = None
        self.newText = None
        self.snapPointRect = None
        self.highlightNets = False

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:

        super().mousePressEvent(mouse_event)
        try:
            modifiers = QGuiApplication.keyboardModifiers()
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()

            if mouse_event.button() == Qt.LeftButton:
                self.mousePressLoc = mouse_event.scenePos().toPoint()

                if self.addInstance:
                    self.newInstance = self.drawInstance(self.mousePressLoc)
                    self.newInstance.setSelected(True)

                elif self.drawWire:
                    self.editorWindow.messageLine.setText("Wire Mode")
                    self.wires = self.addWires(self.mousePressLoc)

                elif self.changeOrigin:  # change origin of the symbol
                    self.origin = self.mousePressLoc
                    self.changeOrigin = False

                elif self.drawPin:
                    self.editorWindow.messageLine.setText("Add a pin")
                    self.newPin = self.addPin(self.mousePressLoc)
                    self.newPin.setSelected(True)

                elif self.drawText:
                    self.editorWindow.messageLine.setText("Add a text note")
                    self.newText = self.addNote(self.mousePressLoc)
                    self.rotateAnItem(
                        self.mousePressLoc, self.newText, float(self.noteOrient[1:])
                    )
                    self.newText.setSelected(True)
                elif self.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        self.rotateSelectedItems(self.mousePressLoc)

                elif self.itemSelect:
                    self.selectSceneItems(modifiers)
        except Exception as e:
            self.logger.error(f"mouse press error: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.buttons() == Qt.LeftButton:
                if self.addInstance:
                    # TODO: think how to do it with mapFromScene
                    self.newInstance.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.drawWire:
                    self.mouseMoveLoc = self.findSnapPoint(
                        self.mouseMoveLoc, self.snapDistance, set(self.wires)
                    )
                    if self.snapPointRect is None:
                        rect = QRectF(QPointF(-5, -5), QPointF(5, 5))
                        self.snapPointRect = QGraphicsRectItem(rect)
                        self.snapPointRect.setPen(schlyr.draftPen)
                        self.addItem(self.snapPointRect)
                    self.snapPointRect.setPos(self.mouseMoveLoc)

                    self.extendWires(self.wires, self.mousePressLoc, self.mouseMoveLoc)
                elif self.drawPin and self.newPin.isSelected():
                    self.newPin.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.drawText and self.newText.isSelected():
                    self.newText.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.itemSelect and modifiers == Qt.ShiftModifier:
                    self.selectionRectItem.setRect(
                        QRectF(self.mousePressLoc, self.mouseMoveLoc)
                    )

            self.editorWindow.statusLine.showMessage(
                f"Cursor Position: {str((self.mouseMoveLoc - self.origin).toTuple())}"
            )
        except Exception as e:
            self.logger.error(e)

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        try:
            self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                if self.drawWire and self.wires:
                    self.mouseReleaseLoc = self.findSnapPoint(
                        self.mouseReleaseLoc, self.snapDistance, set(self.wires)
                    )
                    self.extendWires(
                        self.wires, self.mousePressLoc, self.mouseReleaseLoc
                    )
                    if self.snapPointRect:
                        self.removeItem(self.snapPointRect)
                        self.snapPointRect = None

                    if lines := self.pruneWires(self.wires, schlyr.wirePen):
                        for line in lines:
                            line.mergeNets()
                    self.wires = None  # self.mergeNets()
                    viewNets = {
                        netItem
                        for netItem in self.editorWindow.centralW.view.items()
                        if isinstance(netItem, net.schematicNet)
                    }
                    [netItem.findDotPoints() for netItem in viewNets]

                elif self.addInstance:
                    self.addInstance = False

                elif self.drawText:
                    self.parent.parent.messageLine.setText("Note added.")
                    self.drawText = False
                    self.newText = None
                elif self.drawPin:
                    self.parent.parent.messageLine.setText("Pin added")
                    self.drawPin = False
                    self.newPin = None
                elif self.itemSelect and modifiers == Qt.ShiftModifier:
                    self.selectInRectItems(
                        self.selectionRectItem.rect(), self.partialSelection
                    )
                    self.removeItem(self.selectionRectItem)
                    self.selectionRectItem = None
        except Exception as e:
            print(f"mouse release error: {e}")

    def findSnapPoint(self, eventLoc: QPoint, snapDistance: int, ignoredNetSet: set):
        # sourcery skip: simplify-len-comparison
        snapRect = QRect(
            eventLoc.x() - snapDistance,
            eventLoc.y() - snapDistance,
            2 * snapDistance,
            2 * snapDistance,
        )
        snapItems = {
            item
            for item in self.items(snapRect)
            if isinstance(item, (shp.pin, net.schematicNet))
        }

        try:
            snapItems -= ignoredNetSet
            lengths = list()
            points = list()
            items = list()
            if len(snapItems) > 0:
                for item in snapItems:
                    if isinstance(item, shp.pin):
                        items.append(item)
                        points.append(item.mapToScene(item.start))
                        lengths.append(
                            (item.mapToScene(item.start) - eventLoc).manhattanLength()
                        )
                    elif isinstance(item, net.schematicNet):
                        if snapRect.contains(item.line().p1().toPoint()):
                            items.append(item)

                            points.append(item.line().p1().toPoint())
                            lengths.append(
                                (
                                    item.mapToScene(item.line().p1()) - eventLoc
                                ).manhattanLength()
                            )
                        elif snapRect.contains(item.line().p2().toPoint()):
                            items.append(item)
                            points.append(item.line().p2().toPoint())
                            # print(f'net end:{item.end}')
                            lengths.append(
                                (
                                    item.mapToScene(item.line().p2()) - eventLoc
                                ).manhattanLength()
                            )
                if len(lengths) > 0:
                    indexClosestPoint = lengths.index(min(lengths))
                    eventLoc = points[indexClosestPoint]

            return eventLoc
        except Exception as e:
            self.logger.error(e)  # no items found
            return eventLoc

    def clearNetStatus(self, netsSet: set):
        """
        Clear all assigned net names
        """
        for netItem in netsSet:
            netItem.nameAdded = False
            netItem.nameConflict = False

    def groupAllNets(self) -> None:
        # sourcery skip: collection-builtin-to-comprehension, comprehension-to-generator
        """
        This method starting from nets connected to pins, then named nets and unnamed
        nets, groups all the nets in the schematic.
        """
        try:
            # all the nets in the schematic in a set to remove duplicates
            sceneNetsSet = self.findSceneNetsSet()
            self.clearNetStatus(sceneNetsSet)
            # first find nets connected to pins designating global nets.
            globalNetsSet = self.findGlobalNets()
            sceneNetsSet -= globalNetsSet  # remove these nets from all nets set.
            # now remove nets connected to global nets from this set.
            sceneNetsSet = self.groupNamedNets(globalNetsSet, sceneNetsSet)
            # now find nets connected to schematic pins
            schemPinConNetsSet = self.findSchPinNets()
            sceneNetsSet -= schemPinConNetsSet
            # use these nets as starting nets to find other nets connected to them
            sceneNetsSet = self.groupNamedNets(schemPinConNetsSet, sceneNetsSet)
            # now find the set of nets whose name is set by the user
            namedNetsSet = set([netItem for netItem in sceneNetsSet if netItem.nameSet])
            sceneNetsSet -= namedNetsSet
            # now remove already named net set from firstNetSet
            unnamedNets = self.groupNamedNets(namedNetsSet, sceneNetsSet)
            # now start netlisting from the unnamed nets
            self.groupUnnamedNets(unnamedNets, self.netCounter)
        except Exception as e:
            self.logger.error(e)

    def findGlobalNets(self) -> set:
        """
        This method finds all nets connected to global pins.
        """
        try:
            globalPinsSet = set()
            globalNetsSet = set()
            for symbolItem in self.findSceneSymbolSet():
                for pinName, pinItem in symbolItem.pins.items():
                    if pinName[-1] == "!":
                        globalPinsSet.add(pinItem)
            # self.logger.warning(f'global pins:{globalPinsSet}')
            for pinItem in globalPinsSet:
                pinNetSet = {
                    netItem
                    for netItem in self.items(pinItem.sceneBoundingRect())
                    if isinstance(netItem, net.schematicNet)
                }
                for netItem in pinNetSet:
                    if netItem.nameSet or netItem.nameAdded:
                        # check if net is already named explicitly
                        if netItem.name != pinItem.pinName:
                            netItem.nameConflict = True
                            self.logger.error(
                                f"Net name conflict at {pinItem.pinName} of "
                                f"{pinItem.parent.instanceName}."
                            )
                        else:
                            globalNetsSet.add(netItem)
                    else:
                        globalNetsSet.add(netItem)
                        netItem.name = pinItem.pinName
                        netItem.nameAdded = True
            return globalNetsSet
        except Exception as e:
            self.logger.error(e)

    def findSchPinNets(self):
        # nets connected to schematic pins.
        schemPinConNetsSet = set()
        # first start from schematic pins
        sceneSchemPinsSet = self.findSceneSchemPinsSet()
        for sceneSchemPin in sceneSchemPinsSet:
            pinNetSet = {
                netItem
                for netItem in self.items(sceneSchemPin.sceneBoundingRect())
                if isinstance(netItem, net.schematicNet)
            }
            for netItem in pinNetSet:
                if netItem.nameSet or netItem.nameAdded:  # check if net is named
                    if netItem.name == sceneSchemPin.pinName:
                        schemPinConNetsSet.add(netItem)
                    else:
                        netItem.nameConflict = True
                        self.parent.parent.logger.error(
                            f"Net name conflict at {sceneSchemPin.pinName} of "
                            f"{sceneSchemPin.parent.instanceName}."
                        )
                else:
                    schemPinConNetsSet.add(netItem)
                    netItem.name = sceneSchemPin.pinName
                    netItem.nameAdded = True
                netItem.update()
            schemPinConNetsSet.update(pinNetSet)
        return schemPinConNetsSet

    def groupNamedNets(self, namedNetsSet, unnamedNetsSet):
        """
        Groups nets with the same name using namedNetsSet members as seeds and going
        through connections. Returns the set of still unnamed nets.
        """
        for netItem in namedNetsSet:
            if self.schematicNets.get(netItem.name) is None:
                self.schematicNets[netItem.name] = set()
            connectedNets, unnamedNetsSet = self.traverseNets(
                {
                    netItem,
                },
                unnamedNetsSet,
            )
            self.schematicNets[netItem.name] |= connectedNets
        # These are the nets not connected to any named net
        return unnamedNetsSet

    def groupUnnamedNets(self, unnamedNetsSet: set[net.schematicNet], nameCounter: int):
        """
        Groups nets together if they are connected and assign them default names
        if they don't have a name assigned.
        """
        # select a net from the set and remove it from the set
        try:
            initialNet = (
                unnamedNetsSet.pop()
            )  # assign it a name, net0, net1, net2, etc.
        except KeyError:  # initialNet set is empty
            pass
        else:
            initialNet.name = "net" + str(nameCounter)
            # now go through the set and see if any of the
            # nets are connected to the initial net
            # remove them from the set and add them to the initial net's set
            self.schematicNets[initialNet.name], unnamedNetsSet = self.traverseNets(
                {
                    initialNet,
                },
                unnamedNetsSet,
            )
            nameCounter += 1
            if len(unnamedNetsSet) > 1:
                self.groupUnnamedNets(unnamedNetsSet, nameCounter)
            elif len(unnamedNetsSet) == 1:
                lastNet = unnamedNetsSet.pop()
                lastNet.name = "net" + str(nameCounter)
                self.schematicNets[lastNet.name] = {lastNet}

    def traverseNets(self, connectedSet, otherNetsSet):
        """
        Start from a net and traverse the schematic to find all connected nets. If the connected net search
        is exhausted, remove those nets from the scene nets set and start again in another net until all
        the nets in the scene are exhausted.
        """
        newFoundConnectedSet = set()
        for netItem in connectedSet:
            for netItem2 in otherNetsSet:
                if self.checkNetConnect(netItem, netItem2):
                    if (
                        (netItem2.nameSet or netItem2.nameAdded)
                        and (netItem.nameSet or netItem.nameAdded)
                        and (netItem.name != netItem2.name)
                    ):
                        self.editorWindow.messageLine.setText(
                            "Error: multiple names assigned to same net"
                        )
                        netItem2.nameConflict = True
                        netItem.nameConflict = True
                        break
                    else:
                        netItem2.name = netItem.name
                        netItem2.nameAdded = True
                    newFoundConnectedSet.add(netItem2)
        # keep searching if you already found a net connected to the initial net
        if len(newFoundConnectedSet) > 0:
            connectedSet.update(newFoundConnectedSet)
            otherNetsSet -= newFoundConnectedSet
            self.traverseNets(connectedSet, otherNetsSet)
        return connectedSet, otherNetsSet

    def checkPinNetConnect(self, pinItem: shp.schematicPin, netItem: net.schematicNet):
        """
        Determine if a pin is connected to a net.
        """
        return bool(pinItem.sceneBoundingRect().intersects(netItem.sceneBoundingRect()))

    def checkNetConnect(self, netItem, otherNetItem):
        """
        Determine if a net is connected to another one. One net should end on the other net.
        """
        netBRect = netItem.sceneBoundingRect().adjusted(-2, -2, 2, 2)
        if otherNetItem is not netItem:
            otherBRect = otherNetItem.sceneBoundingRect().adjusted(-2, -2, 2, 2)
            for endPoint in netItem.endPoints:
                if otherBRect.contains(endPoint):
                    return True
            for endPoint in otherNetItem.endPoints:
                if netBRect.contains(endPoint):
                    return True
        else:
            return False

    def generatePinNetMap(self, sceneSymbolSet):
        """
        For symbols in sceneSymbolSet, find which pin is connected to which net. If a
        pin is not connected, assign to it a default net starting with d prefix.
        """
        netCounter = 0
        for symbolItem in sceneSymbolSet:
            for pinName, pinItem in symbolItem.pins.items():
                pinItem.connected = False  # clear connections

                pinConnectedNets = [
                    netItem
                    for netItem in self.items(
                        pinItem.sceneBoundingRect().adjusted(-2, -2, 2, 2)
                    )
                    if isinstance(netItem, net.schematicNet)
                ]
                # this will name the pin by first net it finds in the bounding rectangle of
                # the pin. If there are multiple nets in the bounding rectangle, the first
                # net in the list will be the one used.
                if pinConnectedNets:
                    symbolItem.pinNetMap[pinName] = pinConnectedNets[0].name
                    pinItem.connected = True

                if not pinItem.connected:
                    # assign a default net name prefixed with d(efault).
                    symbolItem.pinNetMap[pinName] = f"dnet{netCounter}"
                    self.logger.warning(
                        f"left unconnected:{symbolItem.pinNetMap[pinName]}"
                    )
                    netCounter += 1
            # now reorder pinNetMap according pinOrder attribute
            if symbolItem.attr.get("pinOrder"):
                pinOrderList = list()
                [
                    pinOrderList.append(item.strip())
                    for item in symbolItem.attr.get("pinOrder").split(",")
                ]
                symbolItem.pinNetMap = {
                    pinName: symbolItem.pinNetMap[pinName] for pinName in pinOrderList
                }

    def findSceneCells(self, symbolSet):
        """
        This function just goes through set of symbol items in the scene and
        checks if that symbol's cell is encountered first time. If so, it adds
        it to a dictionary   cell_name:symbol
        """
        symbolGroupDict = dict()
        for symbolItem in symbolSet:
            if symbolItem.cellName not in symbolGroupDict.keys():
                symbolGroupDict[symbolItem.cellName] = symbolItem
        return symbolGroupDict

    def findSceneSymbolSet(self) -> set[shp.symbolShape]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, shp.symbolShape)}

    def findSceneNetsSet(self) -> set[net.schematicNet]:
        return {item for item in self.items() if isinstance(item, net.schematicNet)}

    def findSceneSchemPinsSet(self) -> set[shp.schematicPin]:
        pinsSceneSet = {
            item for item in self.items() if isinstance(item, shp.schematicPin)
        }
        if pinsSceneSet:  # check pinsSceneSet is empty
            return pinsSceneSet
        else:
            return set()

    def findSceneTextSet(self) -> set[shp.text]:
        if textSceneSet := {
            item for item in self.items() if isinstance(item, shp.text)
        }:
            return textSceneSet
        else:
            return set()

    def keyPressEvent(self, key_event):
        super().keyPressEvent(key_event)
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()

    def resetSceneMode(self):
        self.itemSelect = True
        self.drawWire = False
        self.drawPin = False
        self.parent.parent.messageLine.setText("Select Mode")

    def addWires(self, start: QPoint) -> net.schematicNet:
        """
        Add a net or nets to the scene.
        """
        lines = [
            net.schematicNet(start, start),
            net.schematicNet(start, start),
            net.schematicNet(start, start),
        ]
        return lines

    def extendWires(self, lines: list, start: QPoint, end: QPoint):
        """
        This method is to shape the wires drawn using addWires method.
        __|^^^
        """
        try:
            firstPointX = self.snapToBase(
                (end.x() - start.x()) / 3 + start.x(), self.gridTuple[0]
            )
            firstPointY = start.y()
            firstPoint = QPoint(firstPointX, firstPointY)
            secondPoint = QPoint(firstPointX, end.y())
            [self.addItem(line) for line in lines if line.scene() is None]
            lines[0].start = start
            lines[0].end = firstPoint
            lines[1].start = firstPoint
            lines[1].end = secondPoint
            lines[2].start = secondPoint
            lines[2].end = end
        except Exception as e:
            self.logger.error(e)

    def pruneWires(self, lines, pen):
        if lines[0].start == lines[2].end:  # if the first and last points are the same
            for line in lines:
                self.removeItem(line)
                del line
            return None
        # if the line is vertical or horizontal
        elif (
            lines[0].start.x() == lines[2].end.x()
            or lines[0].start.y() == lines[2].end.y()
        ):
            newLine = net.schematicNet(lines[0].start, lines[2].end)
            self.addItem(newLine)
            undoCommand = us.addShapeUndo(self, newLine)
            self.undoStack.push(undoCommand)
            for line in lines:
                self.removeItem(line)
                del line
            return [newLine]
        else:
            for line in lines:
                if line.length == 0:
                    self.removeItem(line)
                    lines.remove(line)
                    del line
                else:
                    undoCommand = us.addShapeUndo(self, line)
                    self.undoStack.push(undoCommand)
            return lines

    def addPin(self, pos: QPoint):
        try:
            pin = shp.schematicPin(
                pos, self.pinName, self.pinDir, self.pinType, self.gridTuple
            )
            self.addItem(pin)
            undoCommand = us.addShapeUndo(self, pin)
            self.undoStack.push(undoCommand)
            return pin
        except Exception as e:
            self.logger.error(e)

    def addNote(self, pos: QPoint):
        """
        Changed the method name not to clash with qgraphicsscene addText method.
        """
        text = shp.text(
            pos,
            self.noteText,
            self.gridTuple,
            self.noteFontFamily,
            self.noteFontStyle,
            self.noteFontSize,
            self.noteAlign,
            self.noteOrient,
        )
        self.addItem(text)
        undoCommand = us.addShapeUndo(self, text)
        self.undoStack.push(undoCommand)
        return text

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        instance = self.instSymbol(pos)
        self.addItem(instance)
        self.itemCounter += 1
        undoCommand = us.addShapeUndo(self, instance)
        self.undoStack.push(undoCommand)
        self.instanceSymbolTuple = None
        return instance

    def instSymbol(self, pos: QPoint):
        itemShapes = []
        itemAttributes = {}
        try:
            with open(self.instanceSymbolTuple.viewItem.viewPath, "r") as temp:

                items = json.load(temp)
                if items[0]["cellView"] != "symbol":
                    self.logger.error("Not a symbol!")
                    return

                for item in items[1:]:
                    if item["type"] == "attr":
                        itemAttributes[item["nam"]] = item["def"]
                    else:
                        itemShapes.append(lj.createSymbolItems(item, self.gridTuple))

                symbolInstance = shp.symbolShape(
                    itemShapes, itemAttributes, self.gridTuple
                )
                symbolInstance.setPos(pos)
                symbolInstance.counter = self.itemCounter
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                symbolInstance.libraryName = (
                    self.instanceSymbolTuple.libraryItem.libraryName
                )
                symbolInstance.cellName = self.instanceSymbolTuple.cellItem.cellName
                symbolInstance.viewName = self.instanceSymbolTuple.viewItem.viewName
                for item in symbolInstance.labels.values():
                    item.labelDefs()
                return symbolInstance
        except Exception as e:
            self.logger.warning(f"instantiation error: {e}")

    def copySelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                selectedItemJson = json.dumps(item, cls=se.schematicEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                if isinstance(item, shp.symbolShape):
                    self.itemCounter += 1
                    itemCopyDict["name"] = f"I{self.itemCounter}"
                    itemCopyDict["ic"] = int(self.itemCounter)
                    itemCopyDict["ld"]["instName"][0] = f"I{self.itemCounter}"
                    shape = lj.createSchematicItems(
                        itemCopyDict, self.libraryDict, item.viewName, self.gridTuple
                    )
                    [label.labelDefs() for label in shape.labels.values()]
                elif isinstance(item, net.schematicNet):
                    shape = lj.createSchematicNets(itemCopyDict)
                elif isinstance(item, shp.schematicPin):
                    shape = lj.createSchematicPins(itemCopyDict, self.gridTuple)
                elif isinstance(item, shp.text):
                    shape = lj.createTextItem(itemCopyDict, self.gridTuple)
                if shape is not None:
                    self.addItem(shape)
                # shift position by one grid unit to right and down
                shape.setPos(
                    QPoint(
                        item.pos().x() + 4 * self.gridTuple[0],
                        item.pos().y() + 4 * self.gridTuple[1],
                    )
                )
                undoCommand = us.addShapeUndo(self, shape)
                self.undoStack.push(undoCommand)

    def saveSchematicCell(self, file: pathlib.Path):
        try:
            self.sceneR = self.sceneRect()  # get scene rect
            # items = self.items(self.sceneR)  # get items in scene rect
            # only save symbol shapes
            symbolItems = self.findSceneSymbolSet()
            netItems = self.findSceneNetsSet()
            pinItems = self.findSceneSchemPinsSet()
            textItems = self.findSceneTextSet()
            items = list(symbolItems | netItems | pinItems | textItems)
            items.insert(0, {"cellView": "schematic"})
            with open(file, "w") as f:
                json.dump(items, f, cls=se.schematicEncoder, indent=4)
            if self.parent.parent.parentView is not None:
                if type(self.parentView) == schematicEditor:
                    self.parent.parent.parentView.loadSchematic()
                elif type(self.parentView) == symbolEditor:
                    self.parent.parent.parentView.loadSymbol()
        except Exception as e:
            self.logger.error(e)

    def loadSchematicCell(self, itemsList):
        """
        load schematic from item list
        """
        for item in itemsList[1:]:
            if item is not None:
                if item["type"] == "symbolShape":
                    itemShape = lj.createSchematicItems(
                        item, self.libraryDict, item["view"], self.gridTuple
                    )
                    self.addItem(itemShape)
                    if itemShape.counter > self.itemCounter:
                        self.itemCounter = itemShape.counter
                    [labelItem.labelDefs() for labelItem in itemShape.labels.values()]
                elif item["type"] == "schematicNet":
                    netShape = lj.createSchematicNets(item)
                    self.addItem(netShape)
                elif item["type"] == "schematicPin":
                    pinShape = lj.createSchematicPins(item, self.gridTuple)
                    self.addItem(pinShape)
                elif item["type"] == "text":
                    text = lj.createTextItem(item, self.gridTuple)
                    self.addItem(text)

        # increment item counter for next symbol
        self.itemCounter += 1
        # self.addItem(shp.text(QPoint(0, 200), self.textPen, 'Revolution EDA'))
        self.update()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    if isinstance(item, shp.symbolShape):
                        dlg = pdlg.instanceProperties(self.editorWindow, item)
                        if dlg.exec() == QDialog.Accepted:
                            item.instanceName = dlg.instNameEdit.text().strip()
                            item.angle = float(dlg.angleEdit.text().strip())

                            location = QPoint(
                                float(dlg.xLocationEdit.text().strip()),
                                float(dlg.yLocationEdit.text().strip()),
                            )
                            item.setPos(
                                self.snapToGrid(location - self.origin, self.gridTuple)
                            )
                            tempDoc = QTextDocument()
                            for i in range(dlg.instanceLabelsLayout.rowCount()):
                                # first create label name document with HTML annotations
                                tempDoc.setHtml(
                                    dlg.instanceLabelsLayout.itemAtPosition(i, 0)
                                    .widget()
                                    .text()
                                )
                                # now strip html annotations
                                tempLabelName = tempDoc.toPlainText().strip()
                                # check if label name is in label dictionary of item.
                                if item.labels.get(tempLabelName):
                                    item.labels[tempLabelName].labelValue = (
                                        dlg.instanceLabelsLayout.itemAtPosition(i, 1)
                                        .widget()
                                        .text()
                                    )
                                    visible = (
                                        dlg.instanceLabelsLayout.itemAtPosition(i, 2)
                                        .widget()
                                        .currentText()
                                    )
                                    if visible == "True":
                                        item.labels[tempLabelName].labelVisible = True
                                    else:
                                        item.labels[tempLabelName].labelVisible = False
                            [
                                labelItem.labelDefs()
                                for labelItem in item.labels.values()
                            ]

                    elif isinstance(item, net.schematicNet):
                        dlg = pdlg.netProperties(self.editorWindow, item)
                        if dlg.exec() == QDialog.Accepted:
                            item.name = dlg.netNameEdit.text().strip()
                            if item.name != "":
                                item.nameSet = True

                    elif isinstance(item, shp.text):
                        dlg = pdlg.noteTextEditProperties(self.editorWindow, item)
                        if dlg.exec() == QDialog.Accepted:
                            # item.prepareGeometryChange()
                            start = item.start
                            self.removeItem(item)
                            item = shp.text(
                                start,
                                self.textPen,
                                dlg.plainTextEdit.toPlainText(),
                                self.gridTuple,
                                dlg.familyCB.currentText(),
                                dlg.fontStyleCB.currentText(),
                                dlg.fontsizeCB.currentText(),
                                dlg.textAlignmCB.currentText(),
                                dlg.textOrientCB.currentText(),
                            )
                            self.rotateAnItem(start, item, float(item.textOrient[1:]))
                            self.addItem(item)
                    elif isinstance(item, shp.schematicPin):
                        dlg = pdlg.schematicPinPropertiesDialog(self.editorWindow, item)
                        dlg.pinName.setText(item.pinName)
                        dlg.pinDir.setCurrentText(item.pinDir)
                        dlg.pinType.setCurrentText(item.pinType)
                        dlg.angleEdit.setText(str(item.angle))
                        dlg.xlocationEdit.setText(str(item.mapToScene(item.start).x()))
                        dlg.ylocationEdit.setText(str(item.mapToScene(item.start).y()))
                        if dlg.exec() == QDialog.Accepted:
                            item.pinName = dlg.pinName.text().strip()
                            item.pinDir = dlg.pinDir.currentText()
                            item.pinType = dlg.pinType.currentText()
                            itemStartPos = QPoint(
                                int(float(dlg.xlocationEdit.text().strip())),
                                int(float(dlg.ylocationEdit.text().strip())),
                            )
                            item.start = self.snapToGrid(
                                itemStartPos - self.origin, self.gridTuple
                            )
                            item.angle = float(dlg.angleEdit.text().strip())
                item.update()
        except Exception as e:
            self.logger.error(e)

    def netNameEdit(self):
        """
        Edit the name of the selected net.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    if isinstance(item, net.schematicNet):
                        dlg = pdlg.netProperties(self.editorWindow, item)
                        if dlg.exec() == QDialog.Accepted:
                            item.name = dlg.netNameEdit.text().strip()
                            if item.name != "":
                                item.nameSet = True
                            item.update()
        except Exception as e:
            self.logger.error(e)

    def hilightNets(self):
        """
        Show the connections the selected items.
        """
        try:
            self.highlightNets = bool(self.editorWindow.hilightNetAction.isChecked())
        except Exception as e:
            self.logger.error(e)

    def createSymbol(self):
        """
        Create a symbol view for a schematic.
        """
        oldSymbolItem = False

        askViewNameDlg = pdlg.symbolNameDialog(
            self.parent.parent.file.parent,
            self.parent.parent.cellName,
            self.parent.parent,
        )
        if askViewNameDlg.exec() == QDialog.Accepted:
            symbolViewName = askViewNameDlg.symbolViewsCB.currentText()
            if symbolViewName in askViewNameDlg.symbolViewNames:
                oldSymbolItem = True
            if oldSymbolItem:
                deleteSymViewDlg = fd.deleteSymbolDialog(
                    self.parent.parent.cellName, symbolViewName, self.parent.parent
                )
                if deleteSymViewDlg.exec() == QDialog.Accepted:
                    symbolViewItem = self.generateSymbol(symbolViewName)
                    self.editorWindow.appMainW.libraryBrowser.openCellView(
                        symbolViewItem,
                        self.editorWindow.cellItem,
                        self.editorWindow.libItem,
                    )
            else:
                symbolViewItem = self.generateSymbol(symbolViewName)
                self.editorWindow.appMainW.libraryBrowser.openCellView(
                    symbolViewItem,
                    self.editorWindow.cellItem,
                    self.editorWindow.libItem,
                )

    def generateSymbol(self, symbolViewName: str):
        # openPath = pathlib.Path(cellItem.data(Qt.UserRole + 2))
        libName = self.editorWindow.libName
        cellName = self.editorWindow.cellName
        libItem = libm.getLibItem(self.editorWindow.libraryView.libraryModel, libName)
        cellItem = libm.getCellItem(libItem, cellName)
        libraryView = self.editorWindow.libraryView
        schematicPins = list(self.findSceneSchemPinsSet())

        schematicPinNames = [pinItem.pinName for pinItem in schematicPins]

        inputPins = [
            pinItem.pinName
            for pinItem in schematicPins
            if pinItem.pinDir == shp.schematicPin.pinDirs[0]
        ]

        outputPins = [
            pinItem.pinName
            for pinItem in schematicPins
            if pinItem.pinDir == shp.schematicPin.pinDirs[1]
        ]

        inoutPins = [
            pinItem.pinName
            for pinItem in schematicPins
            if pinItem.pinDir == shp.schematicPin.pinDirs[2]
        ]

        dlg = pdlg.symbolCreateDialog(
            self.parent.parent, inputPins, outputPins, inoutPins
        )
        if dlg.exec() == QDialog.Accepted:
            symbolViewItem = scb.createCellView(
                self.parent.parent, symbolViewName, cellItem
            )
            libraryDict = self.parent.parent.libraryDict
            # create symbol editor window with an empty items list
            symbolWindow = symbolEditor(symbolViewItem, libraryDict, libraryView)
            try:
                leftPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.leftPinsEdit.text().split(",")
                        ],
                    )
                )
                rightPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.rightPinsEdit.text().split(",")
                        ],
                    )
                )
                topPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.topPinsEdit.text().split(",")
                        ],
                    )
                )
                bottomPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.bottomPinsEdit.text().split(",")
                        ],
                    )
                )
                stubLength = int(float(dlg.stubLengthEdit.text().strip()))
                pinDistance = int(float(dlg.pinDistanceEdit.text().strip()))
                rectXDim = (
                    max(len(topPinNames), len(bottomPinNames)) + 1
                ) * pinDistance
                rectYDim = (
                    max(len(leftPinNames), len(rightPinNames)) + 1
                ) * pinDistance
            except ValueError:
                self.logger.error("Enter valid value")

        # add window to open windows list
        libraryView.openViews[f"{libName}_{cellName}_{symbolViewName}"] = symbolWindow
        symbolScene = symbolWindow.centralW.scene
        symbolScene.rectDraw(QPoint(0, 0), QPoint(rectXDim, rectYDim))
        symbolScene.labelDraw(
            QPoint(int(0.25 * rectXDim), int(0.4 * rectYDim)),
            "[@cellName]",
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        symbolScene.labelDraw(
            QPoint(int(rectXDim), int(-0.2 * rectYDim)),
            "[@instName]",
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        leftPinLocs = [
            QPoint(-stubLength, (i + 1) * pinDistance) for i in range(len(leftPinNames))
        ]
        rightPinLocs = [
            QPoint(rectXDim + stubLength, (i + 1) * pinDistance)
            for i in range(len(rightPinNames))
        ]
        bottomPinLocs = [
            QPoint((i + 1) * pinDistance, rectYDim + stubLength)
            for i in range(len(bottomPinNames))
        ]
        topPinLocs = [
            QPoint((i + 1) * pinDistance, -stubLength) for i in range(len(topPinNames))
        ]
        for i in range(len(leftPinNames)):
            symbolScene.lineDraw(leftPinLocs[i], leftPinLocs[i] + QPoint(stubLength, 0))
            symbolScene.addItem(
                schematicPins[schematicPinNames.index(leftPinNames[i])].toSymbolPin(
                    leftPinLocs[i], symbolScene.gridTuple
                )
            )
        for i in range(len(rightPinNames)):
            symbolScene.lineDraw(
                rightPinLocs[i], rightPinLocs[i] + QPoint(-stubLength, 0)
            )
            symbolScene.addItem(
                schematicPins[schematicPinNames.index(rightPinNames[i])].toSymbolPin(
                    rightPinLocs[i], symbolScene.gridTuple
                )
            )
        for i in range(len(topPinNames)):
            symbolScene.lineDraw(topPinLocs[i], topPinLocs[i] + QPoint(0, stubLength))
            symbolScene.addItem(
                schematicPins[schematicPinNames.index(topPinNames[i])].toSymbolPin(
                    topPinLocs[i], symbolScene.gridTuple
                )
            )
        for i in range(len(bottomPinNames)):
            symbolScene.lineDraw(
                bottomPinLocs[i], bottomPinLocs[i] + QPoint(0, -stubLength)
            )
            symbolScene.addItem(
                schematicPins[schematicPinNames.index(bottomPinNames[i])].toSymbolPin(
                    bottomPinLocs[i], symbolScene.gridTuple
                )
            )  # symbol attribute generation for netlisting.
        symbolScene.attributeList = list()  # empty attribute list

        symbolScene.attributeList.append(
            se.symbolAttribute("XyceNetlistLine", "X[@instName] [@cellName] [@pinList]")
        )

        symbolWindow.checkSaveCell()
        libraryView.reworkDesignLibrariesView(self.appMainW.libraryDict)
        # symbolWindow.show()
        return symbolViewItem

    def goDownHier(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.symbolShape):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(
                        self.editorWindow.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [
                        cellItem.child(i).text()
                        for i in range(cellItem.rowCount())
                        if cellItem.child(i).text() != item.viewName
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
                            childWindow.parentView = self.editorWindow
                            childWindow.schematicToolbar.addAction(
                                childWindow.goUpAction
                            )
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    def goUpHier(self):
        if self.editorWindow.parentView is not None:
            self.editorWindow.parentView.raise_()
            self.editorWindow.close()

    def ignoreSymbol(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.symbolShape):
                    item.netlistIgnore = not item.netlistIgnore
        else:
            self.logger.warning("No symbol selected")


class layout_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.selectEdLayer = laylyr.pdkLayoutLayers[0]
        self.itemSelect = True  # flag to select item
        self.layoutShapes = ["layoutRect", "layoutCell"]
        self.drawPin = False
        self.itemSelect = True
        self.drawArc = False  # draw arc
        self.drawRect = False  # draw rect
        self.drawPath = False  # draw line
        self.addLabel = False
        self.drawCircle = False
        self.rotateItem = False

        self.layoutInstanceTuple = None
        self.addInstance = False
        self.itemCounter = 0
        self.newPath = None
        self.newPathWidth = 0.0
        self.draftLine = None
        self.pathMode = [False for _ in range(5)]
        self.m45Rotate = QTransform()
        self.m45Rotate.rotate(-45)
        self.newPin = None
        self.newPinTuple = None
        self.newLabelTuple = None
        self.newLabel = None

    @property
    def drawMode(self):
        return any((self.drawPath, self.drawRect, self.addLabel,
                    self.drawCircle, self.drawArc, self.rotateItem))

    # Order of drawing
    # 1. Rect
    # 2. Path
    # 3. Pin
    # 4. Label
    # 5. Contact
    # 6. Add instance
    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        self.mousePressLoc = mouse_event.scenePos().toPoint()
        try:
            modifiers = QGuiApplication.keyboardModifiers()
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()
            if mouse_event.button() == Qt.LeftButton:
                # if self.addLabel and self.newLabel is not None:
                #     self.newLabel.start = self.mousePressLoc
                #     self.newLabelTuple = None
                #     # self.resetSceneMode()  # reset drawing mode
                #     self.newLabel.setSelected(False)  # remove reference to item
                #     self.newLabel = None
                #     self.addLabel = False
                # elif self.addInstance:
                #     self.newInstance = self.drawInstance(self.mousePressLoc)
                #     self.newInstance.setSelected(True)
                #     self.addInstance = False
                if self.drawRect:
                    self.newRect = lshp.layoutRect(
                        self.mousePressLoc,
                        self.mousePressLoc,
                        self.selectEdLayer,
                        self.gridTuple,
                    )
                    self.addUndoStack(self.newRect)
                elif self.drawPath:
                    self.newPath = lshp.layoutPath(
                        QLineF(self.mousePressLoc, self.mousePressLoc),
                        self.selectEdLayer,
                        self.gridTuple,
                        self.newPathWidth,
                    )
                    self.newPath.mode = self.pathMode.index(True)
                    self.addUndoStack(self.newPath)

                elif self.drawPin:
                    if self.newLabel is None:
                        self.newPin = lshp.layoutPin(
                            self.mousePressLoc,
                            self.mousePressLoc,
                            *self.newPinTuple,
                            self.gridTuple,
                        )
                        self.addUndoStack(self.newPin)
                    # else:
                    #     self.newLabel = None
                        # self.editorWindow.createPinClick()

                #     else:
                #         self.newPath.draftLine = QLineF(
                #             self.newPath.draftLine.p1(), self.mousePressLoc
                #         )
                #         self.newPath = None
                # elif self.changeOrigin:  # change origin of the symbol
                #     self.origin = self.mousePressLoc
                #     self.changeOrigin = False
                # elif self.itemSelect:
                #     self.selectSceneItems(modifiers)


        except Exception as e:
            self.logger.error(f"mouse press error: {e}")
        super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        # if self.addLabel:
        #     if self.newLabel is not None: # already defined a new label
        #         self.newLabel.start = self.mouseMoveLoc
        #     # there is no new label but there is a new label tuple defined
        #     elif self.newLabelTuple is not None:
        #         self.newLabel = lshp.layoutLabel(self.mouseMoveLoc, *self.newLabelTuple,
        #                                          self.gridTuple)
        if mouse_event.buttons() == Qt.LeftButton:
        #
        #     # if self.selectedItems() is not None:
        #     #     for item in self.selectedItems():
        #     #         item.setPos(item.mapFromScene(self.mouseMoveLoc))
        #     #         self.mousePressLoc = self.mouseMoveLoc
            if self.drawRect:
                self.editorWindow.messageLine.setText(
                    "Release mouse on the bottom left point"
                )
                self.newRect.end = self.mouseMoveLoc
            elif self.drawPath:
                self.newPath.draftLine = QLineF(
                    self.newPath.draftLine.p1(), self.mouseMoveLoc
                )
            elif self.drawPin and self.newPin is not None:
                    self.newPin.end = self.mouseMoveLoc
        else:
            if self.drawPin and self.newPin is None:
                if self.newLabel is not None:
                    self.newLabel.start = self.mouseMoveLoc


        #
        #     elif self.itemSelect and modifiers == Qt.ShiftModifier:
        #         self.selectionRectItem.setRect(
        #             QRectF(self.mousePressLoc, self.mouseMoveLoc)
        #         )
        super().mouseMoveEvent(mouse_event)
        self.statusLine.showMessage(
            f"Cursor Position: {(self.mouseMoveLoc - self.origin).toTuple()}"
        )

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.button() == Qt.LeftButton:
                if self.drawRect:
                    self.newRect.setSelected(False)
                    self.newRect = None
                    self.drawRect = False
                elif self.drawPin:
                    if self.newPin is not None and self.newLabel is None: # still
                        self.newPin = None
                        self.newLabel = lshp.layoutLabel(
                            self.mouseReleaseLoc, *self.newLabelTuple, self.gridTuple
                        )
                        self.addUndoStack(self.newLabel)
                    elif self.newPin is None and self.newLabel is not None:
                        self.newLabel = None


                # elif self.itemSelect and modifiers == Qt.ShiftModifier:
                #     self.selectInRectItems(
                #         self.selectionRectItem.rect(), self.partialSelection
                #     )
                #     self.removeItem(self.selectionRectItem)
                #     self.selectionRectItem = None
        except Exception as e:
            self.logger.error(f"mouse release error: {e}")

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        try:
            instance = self.instLayout(pos)
            self.addItem(instance)
            self.itemCounter += 1
            undoCommand = us.addShapeUndo(self, instance)
            self.undoStack.push(undoCommand)
            return instance
        except Exception as e:
            self.logger.error(f"Cannot draw instance: {e}")

    def instLayout(self, pos: QPoint):
        """
        Read a layout file and create layoutShape objects from it.
        """
        match self.layoutInstanceTuple.viewItem.viewType:
            case "layout":
                with open(self.layoutInstanceTuple.viewItem.viewPath, "r") as temp:
                    try:
                        items = json.load(temp)
                        if items[0]["cellView"] != "layout":
                            self.logger.error("Not a layout cell")
                        else:
                            shapes = []
                            for item in items[1:]:
                                shapes.append(
                                    lj.createLayoutItems(
                                        item, self.libraryDict, self.gridTuple
                                    )
                                )
                            layoutInstance = lshp.layoutInstance(shapes, self.gridTuple)
                            layoutInstance.setPos(pos)
                            layoutInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            layoutInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            layoutInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            layoutInstance.counter = self.itemCounter
                            layoutInstance.instanceName = f"I{layoutInstance.counter}"
                            # For each instance assign a counter number from the scene
                            return layoutInstance
                    except json.JSONDecodeError:
                        # print("Invalid JSON file")
                        self.logger.warning("Invalid JSON File")
            case "pcell":
                with open(self.layoutInstanceTuple.viewItem.viewPath, "r") as temp:
                    try:
                        items = json.load(temp)
                        if items[0]["cellView"] != "pcell":
                            self.logger.error("Not a pcell cell")
                        else:
                            pcellInstanceStr = (
                                f"pcells."
                                f'{items[1]["reference"]}('
                                f"{self.gridTuple})"
                            )
                            pcellInstance = eval(pcellInstanceStr)
                            pcellInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            pcellInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            pcellInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            pcellInstance.counter = self.itemCounter
                            pcellInstance.instanceName = f"I{pcellInstance.counter}"
                            dlg = pdlg.pcellInstanceDialog(
                                self.editorWindow, pcellInstance
                            )
                            if dlg.exec() == QDialog.Accepted:
                                instanceValuesDict = {}
                                for key, value in dlg.lineEditDict.items():
                                    instanceValuesDict[key] = value.text()
                                pcellInstance(**instanceValuesDict)
                            self.addItem(pcellInstance)
                            return pcellInstance
                    except Exception as e:
                        self.logger.error(f"Cannot read pcell: {e}")

    def layRectDraw(self, start: QPoint, end: QPoint, inputLayer: ddef.layLayer):
        """
        Draws a rectangle on the scene
        """
        rect = lshp.layoutRect(start, end, inputLayer, self.gridTuple)
        # self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        return rect

    def addUndoStack(self, item):
        undoCommand = us.addShapeUndo(self, item)
        self.undoStack.push(undoCommand)

    # def finishItemEdit(self, item: lshp.layoutShape):
    #     try:
    #         self.resetSceneMode()  # reset drawing mode
    #         item = None # remove reference to item
    #         item.setSelected(False)
    #     except Exception as e:
    #         self.logger.error(f"{type(item)} drawing error")

    def findScenelayoutCellSet(self) -> set[lshp.layoutInstance]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, lshp.layoutInstance)}

    def saveLayoutCell(self, fileName):
        # only save the items on the top-level.
        for item in self.items():
            if not item.parentItem():
                print(type(item))

        # items = [item for item in self.items() if not item.parentItem()]
        # items.insert(0, {"cellView": "layout"})
        # with open(fileName, "w") as f:
        #     try:
        #         json.dump(items, f, cls=le.layoutEncoder, indent=4)
        #     except Exception as e:
        #         self.logger.error(e)

    def loadLayoutCell(self, itemsList: list):
        pass
        # for item in itemsList[1:]:
        #     if item["type"] in self.layoutShapes:
        #         itemShape = lj.createLayoutItems(item, self.libraryDict, self.gridTuple)
        #         self.addItem(itemShape)

    def keyPressEvent(self, key_event):
        super().keyPressEvent(key_event)
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()

    def resetSceneMode(self):
        # modeList = [False for _ in range(8)]
        # modeList[1] = True
        self.drawPin = False
        self.itemSelect = True
        self.drawArc = False  # draw arc
        self.drawRect = False  # draw rect
        self.drawPath = False  # draw line
        self.addLabel = False
        self.drawCircle = False
        self.rotateItem = False
        self.newPath = None
        self.draftLine = None
        self.changeOrigin = False
        self.editorWindow.messageLine.setText("Select Mode")

    @staticmethod
    def rotateVector(mouseLoc: QPoint, vector: layp.layoutPath, transform: QTransform):
        start = vector.start
        xmove = mouseLoc.x() - start.x()
        ymove = mouseLoc.y() - start.y()
        match (xmove >= 0, ymove >= 0):
            case (True, True):
                vector.end = QPoint(start.x(), start.y() + ymove)
            case (True, False):
                vector.end = QPoint(start.x() + xmove, start.y())
            case (False, False):
                vector.end = QPoint(start.x(), start.y() + ymove)
            case (False, True):
                vector.end = QPoint(start.x() + xmove, start.y())
        vector.setTransform(transform)


class editor_view(QGraphicsView):
    """
    The qgraphicsview for qgraphicsscene. It is used for both schematic and layout editors.
    """

    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.editor = self.parent.parent
        self.scene = scene
        self.logger = self.scene.logger
        self.majorGrid = self.editor.majorGrid
        self.gridTuple = self.editor.gridTuple
        self.gridbackg = True
        self.linebackg = False

        self.init_UI()

    def init_UI(self):
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        # self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)

        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.standardCursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.standardCursor)  # set cursor to standard arrow
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setMouseTracking(True)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Get the current center point of the view
        oldPos = self.mapToScene(self.viewport().rect().center())

        # Perform the zoom
        zoomFactor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(zoomFactor, zoomFactor)

        # Get the new center point of the view
        newPos = self.mapToScene(self.viewport().rect().center())

        # Calculate the delta and adjust the scene position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())


    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(base * int(round(number / base)))

    def snapToGrid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            self.snapToBase(point.x(), gridTuple[0]),
            self.snapToBase(point.y(), gridTuple[1]),
        )

    def drawBackground(self, painter, rect):

        rectCoord = rect.getRect()
        painter.fillRect(rect, QColor("black"))
        if self.gridbackg:
            painter.setPen(QColor("gray"))
            grid_x_start = (
                math.ceil(rectCoord[0] / self.gridTuple[0]) * self.gridTuple[0]
            )
            grid_y_start = (
                math.ceil(rectCoord[1] / self.gridTuple[1]) * self.gridTuple[1]
            )
            num_x_points = math.floor(rectCoord[2] / self.gridTuple[0])
            num_y_points = math.floor(rectCoord[3] / self.gridTuple[1])
            for i in range(int(num_x_points)):
                for j in range(int(num_y_points)):
                    x = grid_x_start + i * self.gridTuple[0]
                    y = grid_y_start + j * self.gridTuple[1]
                    painter.drawPoint(x, y)
        elif self.linebackg:
            painter.setPen(QColor("gray"))
            left = int(rect.left()) - (int(rect.left()) % self.gridTuple[0])
            top = int(rect.top()) - (int(rect.top()) % self.gridTuple[1])
            bottom = int(rect.bottom())
            right = int(rect.right())

            x_coords = range(left, right, self.gridTuple[0])
            y_coords = range(top, bottom, self.gridTuple[1])

            for x in x_coords:
                painter.drawLine(x, top, x, bottom)
            for y in y_coords:
                painter.drawLine(left, y, right, y)

        else:
            super().drawBackground(painter, rect)

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_F:
            self.fitToView()
        super().keyPressEvent(key_event)

    def fitToView(self):
        viewRect = self.scene.itemsBoundingRect().marginsAdded(QMargins(40, 40, 40, 40))
        self.fitInView(viewRect, Qt.AspectRatioMode.KeepAspectRatio)
        self.show()

    def printView(self, printer):
        """
        Print view using selected Printer.
        """
        painter = QPainter(printer)

        if self.gridbackg:
            self.gridbackg = False
        else:
            self.linebackg = False

        self.revedaPrint(painter)

        self.gridbackg = not self.gridbackg
        self.linebackg = not self.linebackg

    def revedaPrint(self, painter):
        viewport_geom = self.viewport().geometry()
        self.drawBackground(painter, viewport_geom)
        painter.drawText(viewport_geom, "Revolution EDA")
        self.render(painter)
        painter.end()


class symbol_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = None


class schematic_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = None  # initialize to an empty rectangle


class layout_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = None


class libraryBrowser(QMainWindow):
    def __init__(self, appMainW: QMainWindow) -> None:
        super().__init__()
        self.resize(300, 600)
        self.appMainW = appMainW
        self.libraryDict = self.appMainW.libraryDict
        self.cellViews = self.appMainW.cellViews
        self.setWindowTitle("Library Browser")
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        self.logger = self.appMainW.logger
        self.libFilePath = self.appMainW.libraryPathObj
        self.libBrowserCont = libraryBrowserContainer(self)
        self.setCentralWidget(self.libBrowserCont)
        self.designView = self.libBrowserCont.designView
        self.libraryModel = self.designView.libraryModel
        self.editProcess = None

    def _createMenuBar(self):
        self.browserMenubar = self.menuBar()
        self.browserMenubar.setNativeMenuBar(False)
        self.libraryMenu = self.browserMenubar.addMenu("&Library")

    def _createActions(self):
        openLibIcon = QIcon(":/icons/database--plus.png")
        self.openLibAction = QAction(openLibIcon, "Create/Open Lib...", self)
        self.openLibAction.setToolTip("Create/Open Lib...")
        self.libraryMenu.addAction(self.openLibAction)
        self.openLibAction.triggered.connect(self.openLibClick)

        libraryEditIcon = QIcon(":/icons/application-dialog.png")
        self.libraryEditorAction = QAction(libraryEditIcon, "Library Editor", self)
        self.libraryMenu.addAction(self.libraryEditorAction)
        self.libraryEditorAction.setToolTip("Open Library Editor...")
        self.libraryEditorAction.triggered.connect(self.libraryEditorClick)

        closeLibIcon = QIcon(":/icons/database-delete.png")
        self.closeLibAction = QAction(closeLibIcon, "Close Lib...", self)
        self.closeLibAction.setToolTip("Close Lib")
        self.libraryMenu.addAction(self.closeLibAction)
        self.closeLibAction.triggered.connect(self.closeLibClick)

        self.libraryMenu.addSeparator()

        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.newCellAction.setToolTip("Create New Cell")
        self.libraryMenu.addAction(self.newCellAction)
        self.newCellAction.triggered.connect(self.newCellClick)

        deleteCellIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellAction = QAction(deleteCellIcon, "Delete Cell...", self)
        self.deleteCellAction.setToolTip("Delete Cell")
        self.libraryMenu.addAction(self.deleteCellAction)
        self.deleteCellAction.triggered.connect(self.deleteCellClick)

        self.libraryMenu.addSeparator()

        newCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.newCellViewAction = QAction(
            newCellViewIcon, "Create New CellView...", self
        )
        self.newCellViewAction.setToolTip("Create New Cellview")
        self.libraryMenu.addAction(self.newCellViewAction)
        self.newCellViewAction.triggered.connect(self.newCellViewClick)

        openCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.openCellViewAction = QAction(openCellViewIcon, "Open CellView...", self)
        self.openCellViewAction.setToolTip("Open CellView")
        self.libraryMenu.addAction(self.openCellViewAction)
        self.openCellViewAction.triggered.connect(self.openCellViewClick)

        deleteCellViewIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellViewAction = QAction(
            deleteCellViewIcon, "Delete CellView...", self
        )
        self.deleteCellViewAction.setToolTip("Delete Cellview")
        self.libraryMenu.addAction(self.deleteCellViewAction)
        self.deleteCellViewAction.triggered.connect(self.deleteCellViewClick)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(toolbar)
        toolbar.addAction(self.openLibAction)
        toolbar.addAction(self.closeLibAction)
        toolbar.addSeparator()
        toolbar.addAction(self.newCellAction)
        toolbar.addAction(self.deleteCellAction)
        toolbar.addSeparator()
        toolbar.addAction(self.newCellViewAction)
        toolbar.addAction(self.openCellViewAction)
        toolbar.addAction(self.deleteCellViewAction)

    def writeLibDefFile(self, libPathDict: dict, libFilePath: pathlib.Path) -> None:

        libTempDict = dict(zip(libPathDict.keys(), map(str, libPathDict.values())))
        try:
            with libFilePath.open(mode="w") as f:
                json.dump({"libdefs": libTempDict}, f, indent=4)
            self.logger.info(f"Wrote library definition file in {libFilePath}")
        except IOError:
            self.logger.error(f"Cannot save library definitions in {libFilePath}")

    def openLibClick(self):
        """
        Open a directory and add a 'reveda.lib' file to designate it as a library.
        """
        home_dir = str(pathlib.Path.cwd())
        libDialog = QFileDialog(self, "Create/Open Library", home_dir)
        libDialog.setFileMode(QFileDialog.Directory)
        # libDialog.Option(QFileDialog.ShowDirsOnly)
        if libDialog.exec() == QDialog.Accepted:
            libPathObj = pathlib.Path(libDialog.selectedFiles()[0])
            self.libraryDict[libPathObj.stem] = libPathObj
            # create an empty file to denote it is a design library.
            libPathObj.joinpath("reveda.lib").touch(exist_ok=True)
            # self.designView.reworkDesignLibrariesView()
            self.libraryModel.populateLibrary(libPathObj)
            self.writeLibDefFile(self.libraryDict, self.libFilePath)

    def closeLibClick(self):
        libCloseDialog = fd.closeLibDialog(self.libraryDict, self)
        if libCloseDialog.exec() == QDialog.Accepted:
            libName = libCloseDialog.libNamesCB.currentText()
            libItem = libm.getLibItem(self.libraryModel, libName)
            self.libraryDict.pop(libName, None)
            self.libraryModel.rootItem.removeRow(libItem)

    def libraryEditorClick(self, s):
        """
        Open library editor dialogue.
        """
        tempDict = deepcopy(self.libraryDict)
        pathEditDlg = fd.libraryPathEditorDialog(self, tempDict)
        libDefFilePathObj = pathlib.Path.cwd().joinpath("library.json")
        self.libraryDict.clear()
        if pathEditDlg.exec() == QDialog.Accepted:
            model = pathEditDlg.pathsModel
            for row in range(model.rowCount()):
                if model.itemFromIndex(model.index(row, 1)).text().strip():
                    self.libraryDict[
                        model.itemFromIndex(model.index(row, 0)).text().strip()
                    ] = pathlib.Path(
                        model.itemFromIndex(model.index(row, 1)).text().strip()
                    )
        self.writeLibDefFile(self.libraryDict, libDefFilePathObj)
        self.appMainW.libraryDict = self.libraryDict
        self.designView.reworkDesignLibrariesView(self.appMainW.libraryDict)

    def newCellClick(self, s):
        dlg = fd.createCellDialog(self, self.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            libName = dlg.libNamesCB.currentText()
            cellName = dlg.cellCB.currentText()
            self.createNewCell(self, self.libraryModel, cellName, libName)

    def createNewCell(self, parent, libraryModel, cellName, libName):
        libItem = libm.getLibItem(self.libraryModel, libName)
        if cellName.strip() == "":
            self.logger.error("Please enter a cell name.")
        else:
            scb.createCell(parent, libraryModel, libItem, cellName)

    def deleteCellClick(self, s):
        dlg = fd.deleteCellDialog(self, self.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            libItem = libm.getLibItem(self.libraryModel, dlg.libNamesCB.currentText())
            if dlg.cellCB.currentText().strip() == "":
                self.logger.error("Please enter a cell name.")
            else:
                # cellItemsLib = {libItem.child(i).cellName: libItem.child(i) for i in
                #                 range(libItem.rowCount())}
                # cellItem = cellItemsLib.get(dlg.cellCB.currentText())
                cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
                # remove the directory
                shutil.rmtree(cellItem.data(Qt.UserRole + 2))
                cellItem.parent().removeRow(cellItem.row())

    def newCellViewClick(self, s):
        dlg = fd.newCellViewDialog(self, self.libraryModel)
        dlg.viewType.addItems(self.cellViews)
        if dlg.exec() == QDialog.Accepted:
            # cellPath = dlg.selectedLibPath.joinpath(dlg.cellCB.currentText())
            libItem = libm.getLibItem(self.libraryModel, dlg.libNamesCB.currentText())
            cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
            viewItem = scb.createCellView(
                self.appMainW, dlg.viewName.text().strip(), cellItem
            )
            self.createNewCellView(libItem, cellItem, viewItem)

    def createNewCellView(self, libItem, cellItem, viewItem):
        viewTuple = ddef.viewTuple(
            libItem.libraryName, cellItem.cellName, viewItem.viewName
        )
        match viewItem.viewType:
            case "config":
                schViewsList = [
                    cellItem.child(row).viewName
                    for row in range(cellItem.rowCount())
                    if cellItem.child(row).viewType == "schematic"
                ]

                dlg = fd.createConfigViewDialogue(self.appMainW)
                dlg.libraryNameEdit.setText(libItem.libraryName)
                dlg.cellNameEdit.setText(cellItem.cellName)
                dlg.viewNameCB.addItems(schViewsList)
                dlg.switchViews.setText(", ".join(self.appMainW.switchViewList))
                dlg.stopViews.setText(", ".join(self.appMainW.stopViewList))
                # dlg.switchViews.setText(self.)
                if dlg.exec() == QDialog.Accepted:
                    selectedSchName = dlg.viewNameCB.currentText()
                    selectedSchItem = libm.getViewItem(cellItem, selectedSchName)
                    schematicWindow = schematicEditor(
                        selectedSchItem,
                        self.libraryDict,
                        self.libBrowserCont.designView,
                    )
                    schematicWindow.loadSchematic()
                    switchViewList = [
                        viewName.strip()
                        for viewName in dlg.switchViews.text().split(",")
                    ]
                    stopViewList = [
                        viewName.strip() for viewName in dlg.stopViews.text().split(",")
                    ]
                    schematicWindow.switchViewList = switchViewList
                    schematicWindow.stopViewList = stopViewList
                    schematicWindow.configDict = dict()  # clear config dictionary

                    # clear netlisted cells list
                    newConfigDict = dict()  # create an empty newconfig dict
                    schematicWindow.createConfigView(
                        viewItem,
                        schematicWindow.configDict,
                        newConfigDict,
                        schematicWindow.processedCells,
                    )
                    configFilePathObj = viewItem.data(Qt.UserRole + 2)
                    items = list()
                    items.insert(0, {"cellView": "config"})
                    items.insert(1, {"reference": selectedSchName})
                    items.insert(2, schematicWindow.configDict)
                    with configFilePathObj.open(mode="w+") as configFile:
                        json.dump(items, configFile, indent=4)

                    configWindow = self.openConfigEditWindow(
                        schematicWindow.configDict, selectedSchItem, viewItem
                    )
                    self.appMainW.openViews[viewTuple] = configWindow
            case "schematic":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                schematicWindow = schematicEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = schematicWindow
                schematicWindow.loadSchematic()
                schematicWindow.show()
            case "symbol":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                symbolWindow = symbolEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = symbolWindow
                symbolWindow.loadSymbol()
                symbolWindow.show()
            case "veriloga":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                if self.editProcess is None:
                    self.editProcess = QProcess()
                    self.editProcess.finished.connect(self.editProcessFinished)
                    self.editProcess.start(str(self.appMainW.textEditorPath), [])
            case "layout":
                layoutWindow = layoutEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = layoutWindow
                layoutWindow.loadLayout()
                layoutWindow.show()
            case "pcell":
                dlg = ldlg.pcellSettingDialogue(self.appMainW, viewItem, "pdk.pcells")
                if dlg.exec() == QDialog.Accepted:
                    items = list()
                    items.insert(0, {"cellView": "pcell"})
                    items.insert(1, {"reference": dlg.pcellCB.currentText()})
                    with viewItem.data(Qt.UserRole + 2).open(mode="w+") as pcellFile:
                        json.dump(items, pcellFile, indent=4)

    def openConfigEditWindow(self, configDict, schViewItem, viewItem):
        schematicName = schViewItem.viewName
        libItem = schViewItem.parent().parent()
        configWindow = configViewEdit(self.appMainW, schViewItem, configDict, viewItem)
        configWindow.centralWidget.libraryNameEdit.setText(libItem.libraryName)
        cellItem = viewItem.parent()
        configWindow.centralWidget.cellNameEdit.setText(cellItem.cellName)
        schViewsList = [
            cellItem.child(row).viewName
            for row in range(cellItem.rowCount())
            if cellItem.child(row).viewType == "schematic"
        ]
        configWindow.centralWidget.viewNameCB.addItems(schViewsList)
        configWindow.centralWidget.viewNameCB.setCurrentText(schematicName)
        configWindow.centralWidget.switchViewsEdit.setText(
            ", ".join(self.appMainW.switchViewList)
        )
        configWindow.centralWidget.stopViewsEdit.setText(
            ", ".join(self.appMainW.stopViewList)
        )
        configWindow.show()
        return configWindow

    def selectCellView(self, libModel) -> scb.viewItem:
        dlg = fd.selectCellViewDialog(self, libModel)
        if dlg.exec() == QDialog.Accepted:
            libItem = libm.getLibItem(libModel, dlg.libNamesCB.currentText())
            try:
                cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
            except IndexError:
                cellItem = libItem.child(0)
            try:
                viewItem = libm.getViewItem(cellItem, dlg.viewCB.currentText())
                return viewItem
            except IndexError:
                viewItem = cellItem.child(0)
                return None

    def openCellViewClick(self):
        viewItem = self.selectCellView(self.libraryModel)
        cellItem = viewItem.parent()
        libItem = cellItem.parent()
        self.openCellView(viewItem, cellItem, libItem)

    def openCellView(self, viewItem, cellItem, libItem):
        viewName = viewItem.viewName
        cellName = cellItem.cellName
        libName = libItem.libraryName
        openCellViewTuple = ddef.viewTuple(libName, cellName, viewName)
        if openCellViewTuple in self.appMainW.openViews.keys():
            self.appMainW.openViews[openCellViewTuple].raise_()
        else:
            match viewItem.viewType:
                case "layout":
                    layoutWindow = layoutEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    layoutWindow.loadLayout()
                    layoutWindow.show()
                    self.appMainW.openViews[openCellViewTuple] = layoutWindow

                case "schematic":
                    schematicWindow = schematicEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    schematicWindow.loadSchematic()
                    schematicWindow.show()
                    self.appMainW.openViews[openCellViewTuple] = schematicWindow
                case "symbol":
                    symbolWindow = symbolEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    symbolWindow.loadSymbol()
                    symbolWindow.show()
                    self.appMainW.openViews[openCellViewTuple] = symbolWindow
                case "veriloga":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    if items[1]["filePath"]:
                        if self.editProcess is None:
                            self.editProcess = QProcess()
                            VerilogafilePathObj = (
                                viewItem.parent()
                                .data(Qt.UserRole + 2)
                                .joinpath(items[1]["filePath"])
                            )
                            self.editProcess.finished.connect(self.editProcessFinished)
                            self.editProcess.start(
                                self.appMainW.textEditorPath, [str(VerilogafilePathObj)]
                            )
                    else:
                        self.logger.warning("File path not defined.")
                case "pcell":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)

                case "config":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    viewName = items[0]["viewName"]
                    schematicName = items[1]["reference"]
                    schViewItem = libm.getViewItem(cellItem, schematicName)
                    configDict = items[2]
                    configWindow = self.openConfigEditWindow(
                        configDict, schViewItem, viewItem
                    )
                    self.appMainW.openViews[openCellViewTuple] = configWindow

        return openCellViewTuple

    def editProcessFinished(self):
        self.appMainW.importVerilogaClick()
        self.editProcess = None

    def deleteCellViewClick(self, s):
        viewItem = self.selectCellView(self.libraryModel)
        try:
            viewItem.data(Qt.UserRole + 2).unlink()  # delete the file.
            viewItem.parent().removeRow(viewItem.row())
        except OSError as e:
            self.logger.warning(f"Error:{e.strerror}")

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()  # ignore the default close event
        self.hide()  # hide the window instead


class libraryBrowserContainer(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.designView = designLibrariesView(self)
        self.layout.addWidget(self.designView)
        self.setLayout(self.layout)


class designLibrariesView(QTreeView):
    def __init__(self, parent):
        super().__init__(parent=parent)  # QTreeView
        self.parent = parent
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.viewCounter = 0
        self.libBrowsW = self.parent.parent
        self.appMainW = self.libBrowsW.appMainW
        self.libraryDict = self.appMainW.libraryDict  # type: dict
        self.cellViews = self.appMainW.cellViews  # type: list
        self.openViews = self.appMainW.openViews  # type: dict
        self.logger = self.appMainW.logger
        self.selectedItem = None
        # library model is based on qstandarditemmodel
        self.libraryModel = designLibrariesModel(self.libraryDict)
        self.setSortingEnabled(True)
        self.setUniformRowHeights(True)
        self.expandAll()
        self.setModel(self.libraryModel)

    def removeLibrary(self):
        button = QMessageBox.question(
            self,
            "Library Deletion",
            "Are you sure to delete " "this library? This action cannot be undone.",
        )
        if button == QMessageBox.Yes:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.libraryModel.removeRow(self.selectedItem.row())

    def renameLib(self):
        oldLibraryName = self.selectedItem.libraryName
        dlg = fd.renameLibDialog(self, oldLibraryName)
        if dlg.exec() == QDialog.Accepted:
            newLibraryName = dlg.newLibraryName.text().strip()
            libraryItem = libm.getLibItem(self.libraryModel, oldLibraryName)
            libraryItem.setText(newLibraryName)
            oldLibraryPath = libraryItem.data(Qt.UserRole + 2)
            newLibraryPath = oldLibraryPath.parent.joinpath(newLibraryName)
            oldLibraryPath.rename(newLibraryPath)

    def createCell(self):
        dlg = fd.createCellDialog(self, self.libraryModel)
        assert isinstance(self.selectedItem, scb.libraryItem)
        dlg.libNamesCB.setCurrentText(self.selectedItem.libraryName)
        if dlg.exec() == QDialog.Accepted:
            cellName = dlg.cellCB.currentText()
            if cellName.strip() != "":
                scb.createCell(self, self.libraryModel, self.selectedItem, cellName)
            else:
                self.logger.error("Please enter a cell name.")

    def copyCell(self):
        dlg = fd.copyCellDialog(self, self.libraryModel, self.selectedItem)

        if dlg.exec() == QDialog.Accepted:
            scb.copyCell(
                self, dlg.model, dlg.cellItem, dlg.copyName.text(), dlg.selectedLibPath
            )

    def renameCell(self):
        dlg = fd.renameCellDialog(self, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.renameCell(self, dlg.cellItem, dlg.nameEdit.text())

    def deleteCell(self):
        try:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e}")

    def createCellView(self):
        dlg = fd.createCellViewDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            viewItem = scb.createCellView(
                self.appMainW, dlg.nameEdit.text(), self.selectedItem
            )
            self.libBrowsW.createNewCellView(
                self.selectedItem.parent(), self.selectedItem, viewItem
            )

    def openView(self):
        viewItem = self.selectedItem
        cellItem = viewItem.parent()
        libItem = cellItem.parent()
        self.libBrowsW.openCellView(viewItem, cellItem, libItem)

    def copyView(self):
        dlg = fd.copyViewDialog(self, self.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            if self.selectedItem.data(Qt.UserRole + 1) == "view":
                viewPath = self.selectedItem.data(Qt.UserRole + 2)
                selectedLibItem = libm.getLibItem(
                    self.libraryModel, dlg.libNamesCB.currentText()
                )
                cellName = dlg.cellCB.currentText()
                libCellNames = [
                    selectedLibItem.child(row).cellName
                    for row in range(selectedLibItem.rowCount())
                ]
                if (
                    cellName in libCellNames
                ):  # check if there is the cell in the library
                    cellItem = libm.getCellItem(
                        selectedLibItem, dlg.cellCB.currentText()
                    )
                else:
                    cellItem = scb.createCell(
                        self.libBrowsW,
                        self.libraryModel,
                        selectedLibItem,
                        dlg.cellCB.currentText(),
                    )
                cellViewNames = [
                    cellItem.child(row).viewName for row in range(cellItem.rowCount())
                ]
                newViewName = dlg.viewName.text()
                if newViewName in cellViewNames:
                    self.logger.warning(
                        "View already exists. Delete cellview and try again."
                    )
                else:
                    newViewPath = cellItem.data(Qt.UserRole + 2).joinpath(
                        f"{newViewName}.json"
                    )
                    shutil.copy(viewPath, newViewPath)
                    cellItem.appendRow(scb.viewItem(newViewPath))

    def renameView(self):
        oldViewName = self.selectedItem.viewName
        dlg = fd.renameViewDialog(self.libBrowsW, oldViewName)
        if dlg.exec() == QDialog.Accepted:
            newName = dlg.newViewNameEdit.text()
            try:
                viewPathObj = self.selectedItem.data(Qt.UserRole + 2)
                newPathObj = self.selectedItem.data(Qt.UserRole + 2).rename(
                    viewPathObj.parent.joinpath(f"{newName}.json")
                )
                self.selectedItem.parent().appendRow(scb.viewItem(newPathObj))
                self.selectedItem.parent().removeRow(self.selectedItem.row())
            except FileExistsError:
                self.logger.error("Cellview exists.")

    def deleteView(self):
        try:
            self.selectedItem.data(Qt.UserRole + 2).unlink()
            itemRow = self.selectedItem.row()
            parent = self.selectedItem.parent()
            parent.removeRow(itemRow)
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e.strerror}")

    def reworkDesignLibrariesView(self, libraryDict: dict):
        """
        Recreate library model from libraryDict.
        """
        self.libraryModel = designLibrariesModel(libraryDict)
        self.setModel(self.libraryModel)
        self.libBrowsW.libraryModel = self.libraryModel

    # context menu
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            pass
        try:
            self.selectedItem = self.libraryModel.itemFromIndex(index)
            if self.selectedItem.data(Qt.UserRole + 1) == "library":
                menu.addAction("Rename Library", self.renameLib)
                menu.addAction("Remove Library", self.removeLibrary)
                menu.addAction("Create Cell", self.createCell)
            elif self.selectedItem.data(Qt.UserRole + 1) == "cell":
                menu.addAction(
                    QAction("Create CellView...", self, triggered=self.createCellView)
                )
                menu.addAction(QAction("Copy Cell...", self, triggered=self.copyCell))
                menu.addAction(
                    QAction("Rename Cell...", self, triggered=self.renameCell)
                )
                menu.addAction(
                    QAction("Delete Cell...", self, triggered=self.deleteCell)
                )
            elif self.selectedItem.data(Qt.UserRole + 1) == "view":
                menu.addAction(QAction("Open View", self, triggered=self.openView))
                menu.addAction(QAction("Copy View...", self, triggered=self.copyView))
                menu.addAction(
                    QAction("Rename View...", self, triggered=self.renameView)
                )
                menu.addAction(
                    QAction("Delete View...", self, triggered=self.deleteView)
                )
            menu.exec(event.globalPos())
        except UnboundLocalError:
            pass


class designLibrariesModel(QStandardItemModel):
    def __init__(self, libraryDict):
        self.libraryDict = libraryDict
        super().__init__()
        self.rootItem = self.invisibleRootItem()
        self.setHorizontalHeaderLabels(["Libraries"])
        self.initModel()

    def initModel(self):
        for designPath in self.libraryDict.values():
            self.populateLibrary(designPath)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)

    def addLibraryToModel(self, designPath):
        libraryEntry = scb.libraryItem(designPath)
        self.rootItem.appendRow(libraryEntry)
        return libraryEntry

    def addCellToModel(self, cellPath, parentItem):
        cellEntry = scb.cellItem(cellPath)
        parentItem.appendRow(cellEntry)
        return cellEntry

    def addViewToModel(self, viewPath, parentItem):
        viewEntry = scb.viewItem(viewPath)
        parentItem.appendRow(viewEntry)


class libraryPathsModel(QStandardItemModel):
    def __init__(self, libraryDict):
        super().__init__()
        self.libraryDict = libraryDict
        self.setHorizontalHeaderLabels(["Library Name", "Library Path"])
        for key, value in self.libraryDict.items():
            libName = QStandardItem(key)
            libPath = QStandardItem(str(value))
            self.appendRow(libName, libPath)
        self.appendRow(QStandardItem("Click here..."), QStandardItem(""))


class libraryPathsTableView(QTableView):
    def __init__(self, model):
        self.model = model
        self.setModel(self.model)
        self.setShowGrid(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def contextMenuEvent(self, event) -> None:
        self.menu = QMenu(self)
        removePathAction = QAction("Remove Library Path...", self.menu)
        removePathAction.triggered.connect(lambda: self.removeLibraryPath(event))
        self.menu.addAction(removePathAction)
        self.menu.popup(QCursor.pos())

    def removeLibraryPath(self, event):
        print("remove library path")


class symbolViewsModel(designLibrariesModel):
    def __init__(self, libraryDict: dict, symbolViews: list):
        self.symbolViews = symbolViews
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                    and any(x in view.name for x in self.symbolViews)
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)


class layoutViewsModel(designLibrariesModel):
    def __init__(self, libraryDict: dict, layoutViews: list):
        self.layoutViews = layoutViews
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                    and any(x in view.name for x in self.layoutViews)
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)


class xyceNetlist:
    def __init__(
        self,
        schematic: schematicEditor,
        filePathObj: pathlib.Path,
        use_config: bool = False,
    ):
        self.filePathObj = filePathObj
        self.schematic = schematic
        self._use_config = use_config
        self._scene = self.schematic.centralW.scene
        self.libraryDict = self.schematic.libraryDict
        self.libraryView = self.schematic.libraryView
        self._configDict = None
        self.libItem = libm.getLibItem(
            self.schematic.libraryView.libraryModel,
            self.schematic.libName,
        )
        self.cellItem = libm.getCellItem(self.libItem, self.schematic.cellName)

        self.switchViewList = schematic.switchViewList
        self.stopViewList = schematic.stopViewList
        self.netlistedViewsSet = set()  # keeps track of netlisted views.

    def writeNetlist(self):
        with self.filePathObj.open(mode="w") as cirFile:
            cirFile.write(
                "*".join(
                    [
                        "\n",
                        80 * "*",
                        "\n",
                        "* Revolution EDA CDL Netlist\n",
                        f"* Library: {self.schematic.libName}\n",
                        f"* Top Cell Name: {self.schematic.cellName}\n",
                        f"* View Name: {self.schematic.viewName}\n",
                        f"* Date: {datetime.datetime.now()}\n",
                        80 * "*",
                        "\n",
                        ".GLOBAL gnd!\n\n",
                    ]
                )
            )

            # now go down the rabbit hole to track all circuit elements.
            self.recursiveNetlisting(self.schematic, cirFile)

            cirFile.write(".END\n")

    @property
    def configDict(self):
        return self._configDict

    @configDict.setter
    def configDict(self, value: dict):
        assert isinstance(value, dict)
        self._configDict = value

    def recursiveNetlisting(self, schematic: schematicEditor, cirFile):
        """
        Recursively traverse all sub-circuits and netlist them.
        """
        try:
            schematicScene = schematic.centralW.scene
            schematicScene.groupAllNets()  # name all nets in the
            # schematic
            sceneSymbolSet = schematicScene.findSceneSymbolSet()
            schematicScene.generatePinNetMap(sceneSymbolSet)
            for item in sceneSymbolSet:
                if (
                    item.attr.get("XyceNetlistLine")
                    and item.attr.get("XyceNetlistPass") != "1"
                    and (not item.netlistIgnore)
                ):
                    self.netlistedViewsSet.add(
                        ddef.viewTuple(item.libraryName, item.cellName, item.viewName)
                    )
                    libItem = libm.getLibItem(
                        schematic.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewItems = [
                        cellItem.child(row) for row in range(cellItem.rowCount())
                    ]
                    viewNames = [view.viewName for view in viewItems]

                    viewDict = dict(zip(viewNames, viewItems))
                    if self._use_config:
                        netlistableViews = [self.configDict.get(item.cellName)[1]]
                    else:
                        netlistableViews = [
                            viewItemName
                            for viewItemName in self.switchViewList
                            if viewItemName in viewNames
                        ]
                    # now create the netlist line for that item.

                    self.createItemLine(cirFile, item, netlistableViews, viewDict)
                elif item.netlistIgnore:
                    cirFile.write(f"*{item.instanceName} is marked to be ignored\n")
                elif not item.attr.get("XyceNetlistPass", False):
                    cirFile.write(
                        f"*{item.instanceName} has no " f"XyceNetlistLine attribute\n"
                    )

        except Exception as e:
            self.schematic.logger.error(e)

    def createItemLine(self, cirFile, item, netlistableViews: list, viewDict: dict):
        for viewName in netlistableViews:
            if viewName in viewDict:
                viewTuple = ddef.viewTuple(item.libraryName, item.cellName, viewName)
                # print(viewTuple)
                if viewDict[viewName].viewType == "schematic":
                    cirFile.write(self.createXyceSymbolLine(item))

                    schematicObj = schematicEditor(
                        viewDict[viewName],
                        self.libraryDict,
                        self.libraryView,
                    )

                    schematicObj.loadSchematic()
                    if viewTuple not in self.netlistedViewsSet:
                        self.netlistedViewsSet.add(viewTuple)
                        # print(f'{schematicObj.cellName} {schematicObj.viewName}')
                        pinList = " ".join(item.pinNetMap.keys())
                        cirFile.write(f".SUBCKT {schematicObj.cellName} {pinList}\n")
                        self.recursiveNetlisting(schematicObj, cirFile)
                        cirFile.write(".ENDS\n")
                elif viewDict[viewName].viewType == "veriloga":
                    with viewDict[viewName].data(Qt.UserRole + 2).open(
                        mode="r"
                    ) as vaview:
                        items = json.load(vaview)
                    netlistLine = items[3]["netlistLine"]
                    netlistLine = netlistLine.replace(
                        "[@instName]", f"{item.instanceName}"
                    )
                    # TODO: fix veriloga netlisting
                    # for pinName, netName in item.pinNetMap.items():
                    #     netlistLine = netlistLine.replace(f"[|{pinName}:%]", f"{netName}")
                    pinList = " ".join(item.pinNetMap.values())
                    netlistLine = netlistLine.replace("[@pinList]", pinList)
                    for labelItem in item.labels.values():
                        if labelItem.labelDefinition in netlistLine:
                            netlistLine = netlistLine.replace(
                                labelItem.labelDefinition, labelItem.labelText
                            )
                    cirFile.write(f"{netlistLine}\n")
                    self.netlistedViewsSet.add(viewTuple)
                elif viewDict[viewName].viewType == "symbol":
                    cirFile.write(f"{self.createXyceSymbolLine(item)}")
                    self.netlistedViewsSet.add(
                        ddef.viewTuple(item.libraryName, item.cellName, item.viewName)
                    )
                break

    def createXyceSymbolLine(self, item):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            xyceNetlistFormatLine = item.attr["XyceNetlistLine"].strip()
            for labelItem in item.labels.values():
                if labelItem.labelDefinition in xyceNetlistFormatLine:
                    xyceNetlistFormatLine = xyceNetlistFormatLine.replace(
                        labelItem.labelDefinition, labelItem.labelText
                    )

            for attrb, value in item.attr.items():
                if f"[%{attrb}]" in xyceNetlistFormatLine:
                    xyceNetlistFormatLine = xyceNetlistFormatLine.replace(
                        f"[%{attrb}]", value
                    )
            pinList = " ".join(item.pinNetMap.values())
            xyceNetlistFormatLine = (
                xyceNetlistFormatLine.replace("[@pinList]", pinList) + "\n"
            )
            return xyceNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(e)
            self._scene.logger.error(
                f"Netlist line is not defined for" f" {item.instanceName}"
            )
            # if there is no NLPDeviceFormat line, create a warning line
            return f"*Netlist line is not defined for symbol of {item.instanceName}\n"


class configViewEdit(QMainWindow):
    def __init__(self, appmainW, schViewItem, configDict, viewItem):
        super().__init__(parent=appmainW)
        self.appmainW = appmainW  # app mainwindow
        self.schViewItem = schViewItem
        self.configDict = configDict
        self.viewItem = viewItem
        self.setWindowTitle("Edit Config View")
        self.setMinimumSize(500, 600)
        self._createMenuBar()
        self._createActions()
        self._addActions()
        self._createTriggers()
        self.centralWidget = configViewEditContainer(self)
        self.setCentralWidget(self.centralWidget)

    def _createMenuBar(self):
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu("&File")
        self.editMenu = self.mainMenu.addMenu("&Edit")
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _createActions(self):
        updateIcon = QIcon(":/icons/arrow-circle.png")
        self.updateAction = QAction(updateIcon, "Update", self)
        saveIcon = QIcon(":/icons/database--plus.png")
        self.saveAction = QAction(saveIcon, "Save", self)

    def _addActions(self):
        self.fileMenu.addAction(self.updateAction)
        self.fileMenu.addAction(self.saveAction)

    def _createTriggers(self):
        self.updateAction.triggered.connect(self.updateClick)
        self.saveAction.triggered.connect(self.saveClick)

    def updateClick(self):
        self.centralWidget.configViewTable.updateModel()
        self.configDict = dict()
        newConfigDict = dict()
        model = self.centralWidget.confModel
        for i in range(model.rowCount()):
            viewList = [
                item.strip()
                for item in model.itemFromIndex(model.index(i, 3)).text().split(",")
            ]
            self.configDict[model.item(i, 1).text()] = [
                model.item(i, 0).text(),
                model.item(i, 2).text(),
                viewList,
            ]
        if self.appmainW.libraryBrowser is None:
            self.appmainW.createLibraryBrowser()
        topSchematicWindow = schematicEditor(
            self.schViewItem,
            self.appmainW.libraryDict,
            self.appmainW.libraryBrowser.libBrowserCont.designView,
        )
        topSchematicWindow.loadSchematic()
        topSchematicWindow.createConfigView(
            self.viewItem,
            self.configDict,
            newConfigDict,
            topSchematicWindow.processedCells,
        )
        self.configDict = newConfigDict

        self.centralWidget.confModel = configModel(self.configDict)
        # self.centralWidget.configDictGroup.setVisible(False)
        self.centralWidget.configDictLayout.removeWidget(
            self.centralWidget.configViewTable
        )
        self.centralWidget.configViewTable = configTable(self.centralWidget.confModel)
        self.centralWidget.configDictLayout.addWidget(
            self.centralWidget.configViewTable
        )  # self.centralWidget.configDictGroup.setVisible(True)

    def saveClick(self):
        configFilePathObj = self.viewItem.data(Qt.UserRole + 2)
        items = list()
        items.insert(0, {"viewName": "config"})
        items.insert(1, {"reference": self.schViewItem.viewName})
        items.insert(2, self.configDict)
        with configFilePathObj.open(mode="w+") as configFile:
            json.dump(items, configFile, indent=4)


class configViewEditContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.mainLayout = QVBoxLayout()
        topCellGroup = QGroupBox("Top Cell")
        topCellLayout = QFormLayout()
        self.libraryNameEdit = edf.longLineEdit()
        topCellLayout.addRow(edf.boldLabel("Library:"), self.libraryNameEdit)
        self.cellNameEdit = edf.longLineEdit()
        topCellLayout.addRow(edf.boldLabel("Cell:"), self.cellNameEdit)
        self.viewNameCB = QComboBox()
        topCellLayout.addRow(edf.boldLabel("View:"), self.viewNameCB)
        topCellGroup.setLayout(topCellLayout)
        self.mainLayout.addWidget(topCellGroup)
        viewGroup = QGroupBox("Switch/Stop Views")
        viewGroupLayout = QFormLayout()
        viewGroup.setLayout(viewGroupLayout)
        self.switchViewsEdit = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel("View List:"), self.switchViewsEdit)
        self.stopViewsEdit = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel("Stop List:"), self.stopViewsEdit)
        self.mainLayout.addWidget(viewGroup)
        self.configDictGroup = QGroupBox("Cell View Configuration")
        self.confModel = configModel(self.parent.configDict)
        self.configDictLayout = QVBoxLayout()
        self.configViewTable = configTable(self.confModel)
        self.configDictLayout.addWidget(self.configViewTable)
        self.configDictGroup.setLayout(self.configDictLayout)
        self.mainLayout.addWidget(self.configDictGroup)
        self.setLayout(self.mainLayout)


class configModel(QStandardItemModel):
    def __init__(self, configDict: dict):
        row = len(configDict.keys())
        column = 4
        super().__init__(row, column)
        self.setHorizontalHeaderLabels(
            ["Library", "Cell Name", "View Found", "View To " "Use"]
        )
        for i, (k, v) in enumerate(configDict.items()):
            item = QStandardItem(v[0])
            self.setItem(i, 0, item)
            item = QStandardItem(k)
            self.setItem(i, 1, item)
            item = QStandardItem(v[1])
            self.setItem(i, 2, item)
            item = QStandardItem(", ".join(v[2]))
            self.setItem(i, 3, item)


class configTable(QTableView):
    def __init__(self, model: configModel):
        super().__init__()
        self.model = model
        self.setModel(self.model)
        self.combos = list()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setEditTriggers(QTableView.NoEditTriggers)
        for row in range(self.model.rowCount()):
            self.combos.append(QComboBox())
            items = [
                item.strip()
                for item in self.model.itemFromIndex(self.model.index(row, 3))
                .text()
                .split(",")
            ]
            self.combos[-1].addItems(items)
            self.combos[-1].setCurrentText(
                self.model.itemFromIndex(self.model.index(row, 2)).text()
            )
            self.setIndexWidget(self.model.index(row, 3), self.combos[-1])

    def updateModel(self):
        for row in range(self.model.rowCount()):
            item = QStandardItem(self.combos[row].currentText())
            self.model.setItem(row, 2, item)


class startThread(QRunnable):
    __slots__ = ("fn",)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self) -> None:
        try:
            self.fn
        except Exception as e:
            print(e)
