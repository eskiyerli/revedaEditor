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
# import math

# shape class definition for symbol editor.
# base class for all shapes: rectangle, circle, line
from PySide6.QtCore import (QPoint, QRect, QRectF, Qt, QLine, QPointF, QLineF, )
from PySide6.QtGui import (QPen, QBrush, QColor, QTransform, QPixmap, QBitmap, QFontMetrics,
                           QFont, QTextOption)
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent, QGraphicsLineItem)

import pdk.symLayers as symlyr
import revedaEditor.backend.dataDefinitions as ddef


class layoutShape(QGraphicsItem):

    def __init__(self, gridTuple: tuple[int, int]) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        self._gridTuple = gridTuple
        self._angle = 0  # rotation angle
        self._stretch: bool = False
        self._pen = symlyr.defaultPen

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / self._gridTuple[0]) * self._gridTuple[0])
            newPos.setY(round(newPos.y() / self._gridTuple[1]) * self._gridTuple[1])

            if not sceneRect.contains(newPos):
                # Keep the item inside the scene rect.
                if newPos.x() > sceneRect.right():
                    sceneRect.setRight(newPos.x())
                    viewRect.setRight(newPos.x())
                elif newPos.x() < sceneRect.left():
                    sceneRect.setLeft(newPos.x())
                    viewRect.setLeft(newPos.x())
                if newPos.y() > sceneRect.bottom():
                    sceneRect.setBottom(newPos.y())
                    viewRect.setBottom(newPos.y())
                elif newPos.y() < sceneRect.top():
                    sceneRect.setTop(newPos.y())
                    viewRect.setTop(newPos.y())
            return newPos
        return super().itemChange(change, value)

    @property
    def pen(self):
        return self._pen

    @property
    def brush(self):
        return self._brush

    @brush.setter
    def brush(self, value: QBrush):
        if isinstance(value, QBrush):
            self._brush = value

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.prepareGeometryChange()
        self.setRotation(value)  # self.update(self.boundingRect())

    @property
    def gridTuple(self):
        return self._gridTuple

    @gridTuple.setter
    def gridTuple(self, value: int):
        self._gridTuple = value

    @property
    def stretch(self):
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.scene().changeOrigin:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        else:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def sceneEvent(self, event):
        """
        Do not propagate event if shape needs to keep still.
        """
        if self.scene() and (self.scene().changeOrigin or self.scene().drawMode):
            return False
        else:
            super().sceneEvent(event)
            return True

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)  # self.setSelected(False)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        self.setOpacity(0.75)
        self.setFocus()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        self.setCursor(Qt.CrossCursor)
        self.setOpacity(1)
        self.clearFocus()

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())

    @staticmethod
    def snapToBase(number, base):
        """
        Restrict a number to the multiples of base
        """
        return base * int(round(number / base))

    def snapToGrid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(gridTuple[0] * int(round(point.x() / gridTuple[0])),
                      gridTuple[1] * int(round(point.y() / gridTuple[1])), )


class layRect(layoutShape):
    sides = ["Left", "Right", "Top", "Bottom"]

    def __init__(self, start: QPoint, end: QPoint, inpEdLayer: ddef.layLayer,
                 gridTuple: tuple[int, int]):
        self._rect = QRectF(start, end).normalized()
        self._start = self._rect.topLeft()
        self._end = self._rect.bottomRight()
        self._stretchSide = None
        self._inpEdLayer = inpEdLayer
        self._pen = QPen(self._inpEdLayer.pcolor, self._inpEdLayer.pwidth,
                         self._inpEdLayer.pstyle)
        bitmap = QBitmap.fromImage(QPixmap(self._inpEdLayer.btexture).scaled(10, 10).toImage())
        self._brush = QBrush(self._inpEdLayer.bcolor, bitmap)
        self._selectedPen = QPen(QColor('yellow'), self._inpEdLayer.pwidth, Qt.DashLine)

        self._selectedBrush = QBrush(QColor('yellow'),bitmap)
        self._stretchPen = QPen(QColor('red'), self._inpEdLayer.pwidth, Qt.SolidLine)

        self._gridTuple = gridTuple
        super().__init__(self._gridTuple)

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self._selectedPen)
            painter.setBrush(self._selectedBrush)
            if self.stretch:
                painter.setPen(self._stretchPen)
                if self._stretchSide == layRect.sides[0]:
                    painter.drawLine(self.rect.topLeft(), self.rect.bottomLeft())
                elif self._stretchSide == layRect.sides[1]:
                    painter.drawLine(self.rect.topRight(), self.rect.bottomRight())
                elif self._stretchSide == layRect.sides[2]:
                    painter.drawLine(self.rect.topLeft(), self.rect.topRight())
                elif self._stretchSide == layRect.sides[3]:
                    painter.drawLine(self.rect.bottomLeft(), self.rect.bottomRight())
        else:
            painter.setPen(self._pen)
            painter.setBrush(self._brush)
        painter.drawRect(self._rect)

    def boundingRect(self):
        return self._rect.normalized().adjusted(-2, -2, 2, 2)

    @property
    def layer(self):
        return self._inpEdLayer

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect: QRect):
        self.prepareGeometryChange()
        self._rect = rect

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start: QPoint):
        self.prepareGeometryChange()
        self._rect = QRectF(start, self.end).normalized()
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self.prepareGeometryChange()
        self._rect = QRectF(self.start, end).normalized()
        self._end = end

    @property
    def centre(self):
        return QPoint(int(self._rect.x() + self._rect.width() / 2),
                      int(self._rect.y() + self._rect.height() / 2), )

    @property
    def height(self):
        return self.rect.height()

    @height.setter
    def height(self, height: int):
        self.prepareGeometryChange()
        self._rect.setHeight(height)

    @property
    def width(self):
        return self.rect.width()

    @width.setter
    def width(self, width):
        self.prepareGeometryChange()
        self.rect.setWidth(width)

    @property
    def left(self):
        return self.rect.left()

    @left.setter
    def left(self, left: int):
        self.rect.setLeft(left)

    @property
    def right(self):
        return self.rect.right()

    @right.setter
    def right(self, right: int):
        self.prepareGeometryChange()
        self.rect.setRight(right)

    @property
    def top(self):
        return self.rect.top()

    @top.setter
    def top(self, top: int):
        self.prepareGeometryChange()
        self.rect.setTop(top)

    @property
    def bottom(self):
        return self.rect.bottom()

    @bottom.setter
    def bottom(self, bottom: int):
        self.prepareGeometryChange()
        self.rect.setBottom(bottom)

    @property
    def origin(self):
        return self.rect.bottomLeft()

    @property
    def stretchSide(self):
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = event.pos().toPoint()
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            if eventPos.x() == self.snapToBase(self._rect.left(), self.gridTuple[0]):
                if self._rect.top() <= eventPos.y() <= self._rect.bottom():
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = layRect.sides[0]
            elif eventPos.x() == self.snapToBase(self._rect.right(), self.gridTuple[0]):
                if self._rect.top() <= eventPos.y() <= self._rect.bottom():
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = layRect.sides[1]
            elif eventPos.y() == self.snapToBase(self._rect.top(), self.gridTuple[1]):
                if self._rect.left() <= eventPos.x() <= self._rect.right():
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = layRect.sides[2]
            elif eventPos.y() == self.snapToBase(self._rect.bottom(), self.gridTuple[1]):
                if self._rect.left() <= eventPos.x() <= self._rect.right():
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = layRect.sides[3]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self.stretch:
            self.prepareGeometryChange()
            if self.stretchSide == layRect.sides[0]:
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setLeft(eventPos.x())
            elif self.stretchSide == layRect.sides[1]:
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setRight(eventPos.x() - int(self._pen.width() / 2))
            elif self.stretchSide == layRect.sides[2]:
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setTop(eventPos.y())
            elif self.stretchSide == layRect.sides[3]:
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setBottom(eventPos.y() - int(self._pen.width() / 2))
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            self.setCursor(Qt.ArrowCursor)


class layoutInstance(layoutShape):
    def __init__(self, shapes: list, gridTuple: tuple[int, int]):
        super().__init__(gridTuple)
        assert shapes is not None  # must not be an empty list
        self._shapes = shapes  # list of shapes in the symbol
        self._draft = False
        self._libraryName = ""
        self._cellName = ""
        self._viewName = ""
        self._instanceName = ""
        self._drawings = list()
        self._counter = 0
        for item in self._shapes:
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            item.setParentItem(self)
            self._drawings.append(item)
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)
        self._borderRect = self._drawings[0].sceneBoundingRect()
        if self._drawings[1:]:
            for drawing in self._drawings[1:]:
                self._borderRect = self._borderRect.united(drawing.sceneBoundingRect())

    def __str__(self):
        return (f"type(self)({self.cellName}, scene position= {self.scenePos()} )")

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

    @property
    def libraryName(self):
        return self._libraryName

    @libraryName.setter
    def libraryName(self, value):
        self._libraryName = value

    @property
    def cellName(self):
        return self._cellName

    @cellName.setter
    def cellName(self, value: str):
        self._cellName = value

    @property
    def viewName(self):
        return self._viewName

    @viewName.setter
    def viewName(self, value: str):
        self._viewName = value

    @property
    def counter(self):
        return self._counter

    @counter.setter
    def counter(self, value: int):
        assert isinstance(value, int)
        self._counter = value

    @property
    def instanceName(self):
        return self._instanceName

    @instanceName.setter
    def instanceName(self, value: str):
        assert isinstance(value, str)
        self._instanceName = value

    @property
    def shapes(self):
        return self._shapes

    @shapes.setter
    def shapes(self, value: list):
        self._shapes = value
        for shape in self._shapes:
            shape.setParentItem(self)

    def addShape(self, shape: QGraphicsItem):
        self._drawings.append(shape)
        shape.setParentItem(self)


class layoutCell(layoutInstance):
    def __init__(self, shapes: list, gridTuple):
        super().__init__(shapes, gridTuple)


class pcell(layoutInstance):
    def __init__(self, shapes: list, gridTuple: tuple[int, int]):
        super().__init__(shapes, gridTuple)


class layoutPath(layoutShape):
    def __init__(self, draftLine: QLineF, inpEdLayer: ddef.edLayer,
                 gridTuple: tuple[int, int], width: float = 1.0, startExtend: int = 0,
                 endExtend: int = 0, mode:int =0):
        super().__init__(gridTuple)
        self._draftLine = draftLine
        self._startExtend = startExtend
        self._endExtend = endExtend
        self._width = width
        self._gridTuple = gridTuple
        self._inpEdLayer = inpEdLayer
        self._mode = mode
        self._rect = QRectF(0, 0, 0, 0)
        self._rectCorners()
        self._pen = QPen(self._inpEdLayer.pcolor, self._inpEdLayer.pwidth,
                         self._inpEdLayer.pstyle)
        bitmap = QBitmap.fromImage(QPixmap(self._inpEdLayer.btexture).scaled(10, 10).toImage())
        self._brush = QBrush(self._inpEdLayer.bcolor, bitmap)
        self._selectedPen = QPen(QColor('yellow'), self._inpEdLayer.pwidth, Qt.DashLine)
        self._selectedBrush = QBrush(QColor('yellow'),bitmap)
        self._stretchPen = QPen(QColor('red'), self._inpEdLayer.pwidth, Qt.SolidLine)
        self._stretchBrush = QBrush(QColor('red'), bitmap)
        self.p45Transform = QTransform().rotate(-45, Qt.Axis.ZAxis)

    def _rectCorners(self):
        angle = self._draftLine.angle()
        match self._mode:
            case 0: # manhattan
                self.createManhattanPath(angle)
            case 1: # diagonal
                self.createDiagonalPath(angle)
            case 2:
                self.createAnyAnglePath(angle)
            case 3:
                self.createHorizontalPath(angle)
            case 4:
                self.createVerticalPath(angle)

    def createManhattanPath(self, angle):
        if 0 <= angle <= 45 or 360 > angle > 315:
            self._draftLine.setAngle(0)
        elif 45 < angle <= 135:
            self._draftLine.setAngle(90)
        elif 135 < angle <= 225:
            self._draftLine.setAngle(180)
        elif 225 < angle <= 315:
            self._draftLine.setAngle(270)
        self._rect = self.extractRect()

    def createDiagonalPath(self, angle):
        if 0 <= angle <= 22.5 or 360 > angle > 337.5:
            self._draftLine.setAngle(0)
            self._rect = self.extractRect()
        elif 22.5 < angle <= 67.5:
            self._draftLine.setAngle(0)
            self._rect = self.extractRect()
            self.setRotation(-45)
        elif 67.5 < angle <= 112.5:
            self._draftLine.setAngle(90)
            self._rect = self.extractRect()
        elif 112.5 < angle <= 157.5:
            self._draftLine.setAngle(90)
            self._rect = self.extractRect()
            self.setRotation(-45)
        elif 157.5 < angle <= 202.5:
            self._draftLine.setAngle(180)
            self._rect = self.extractRect()
        elif 202.5 < angle <= 247.5:
            self._draftLine.setAngle(180)
            self._rect = self.extractRect()
            self.setRotation(-45)
        elif 247.5 < angle <= 292.5:
            self._draftLine.setAngle(270)
            self._rect = self.extractRect()
        elif 292.5 < angle <= 337.5:
            self._draftLine.setAngle(270)
            self._rect = self.extractRect()
            self.setRotation(-45)

    def createAnyAnglePath(self, angle):
        self._draftLine.setAngle(0)
        self._rect = self.extractRect()
        self.setTransformOriginPoint(self.draftLine.p1())
        self.setRotation(-angle)

    def createHorizontalPath(self, angle):
        if 0 <= angle <= 90 or 360 > angle > 270:
            self._draftLine.setAngle(0)
        elif 90 < angle <= 270:
            self._draftLine.setAngle(180)
        self._rect = self.extractRect()

    def createVerticalPath(self, angle):
        if 0 <= angle < 180:
            self._draftLine.setAngle(90)
        elif 180 <=  angle < 360:
            self._draftLine.setAngle(270)
        self._rect = self.extractRect()

    def extractRect(self):
        direction = self._draftLine.p2() - self._draftLine.p1()
        if direction == QPoint(0, 0):  # when the mouse pressed first time
            rect = QRectF(self._draftLine.p1(), self._draftLine.p2()).adjusted(-2, -2, 2,
                                                                                2).normalized()
        else:
            direction /= direction.manhattanLength()
            perpendicular = QPointF(-direction.y(), direction.x())
            point1 = (self._draftLine.p1() + perpendicular * self._width * 0.5 - direction *
                    self._startExtend).toPoint()
            point2 = (self._draftLine.p2() - perpendicular * self._width * 0.5 + direction *
                    self._endExtend).toPoint()
            rect = QRectF(point1, point2).normalized()
        return rect


    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self._selectedPen)
            painter.setBrush(self._selectedBrush)
        else:
            painter.setPen(self._pen)
            painter.setBrush(self._brush)
        painter.drawLine(self._draftLine)
        painter.drawRect(self._rect)

    def boundingRect(self) -> QRectF:
        return self._rect.adjusted(-2, 2, 2, 2)

    @property
    def draftLine(self):
        return self._draftLine

    @draftLine.setter
    def draftLine(self, line: QLineF):
        self.prepareGeometryChange()
        self._draftLine = line
        self._rectCorners()


    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width: float):
        self._width = width
        self.prepareGeometryChange()
        self._rectCorners()

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value: int):
        print('mode is set to', value)
        self._mode = value

    @property
    def stretchSide(self):
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = event.pos().toPoint()
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            if eventPos == self._line.p1():
                self._stretchSide = 'p1'
                self.setCursor(Qt.SizeHorCursor)
            elif eventPos == self._line.p2():
                self._stretchSide = 'p2'
                self.setCursor(Qt.SizeHorCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self.stretch:
            self.prepareGeometryChange()
            if self._stretchSide == 'p1':
                if self._angle == 0 or self._angle == 180:
                    self._line.setP1(QPoint(eventPos.x(), self._line.p1().y()))
                elif self._angle == 90 or self._angle == 270:
                    self._line.setP1(QPoint(self._line.p1().x(), eventPos.y()))
            elif self._stretchSide == 'p2':
                if self._angle == 0 or self._angle == 180:
                    self._line.setP1(QPoint(eventPos.x(), self._line.p2().y()))
                elif self._angle == 90 or self._angle == 270:
                    self._line.setP1(QPoint(self._line.p2().x(), eventPos.y()))
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            self.setCursor(Qt.ArrowCursor)

class layoutPin(layoutShape):
    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]
    def __init__(self, rect: QRect, pinName: str, pinDir: str, pinType: str,
                 pinLayer: ddef.layLayer, gridTuple: tuple[
        int, int]):
        super().__init__(gridTuple)
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType
        self._pinLayer = pinLayer
        self._connected = False  # True if the pin is connected to a net.
        self._rect = rect

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(self._rect)

    def boundingRect(self):
        return self._rect.adjusted(-2, 2, 2, 2)

    @property
    def pinName(self):
        return self._pinName

    @pinName.setter
    def pinName(self, value):
        self._pinName = value

    @property
    def pinDir(self):
        return self._pinDir

    @pinDir.setter
    def pinDir(self, value):
        self._pinDir = value

    @property
    def pinType(self):
        return self._pinType

    @pinType.setter
    def pinType(self, value):
        self._pinType = value

    @property
    def pinLayer(self):
        return self._pinLayer

    @pinLayer.setter
    def pinLayer(self, value):
        self._pinLayer = value

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, value: QRect):
        self.prepareGeometryChange()
        self._rect = value

class label(layoutShape):

    labelAlignments = ["Left", "Center", "Right"]
    labelOrients = ["R0", "R90", "R180", "R270", "MX", "MX90", "MY", "MY90"]

    def __init__(self,start: QPoint, labelText: str, fontFamily: str, fontStyle: str,
                 labelHeight: str, labelAlign: str, labelOrient: str, gridTuple: tuple[int,
            int]):
        super().__init__(gridTuple)
        self._start = start
        self._labelText = labelText
        self._fontFamily = fontFamily
        self._fontStyle = fontStyle
        self._labelHeight = labelHeight
        self._labelAlign = labelAlign
        self._labelOrient = labelOrient
        self._labelFont = QFont(fontFamily)
        self._labelFont.setStyleName(fontStyle)
        self._labelFont.setPointSize(int(float(self._labelHeight)))
        self._labelFont.setKerning(True)
        self.setOpacity(1)
        self._fm = QFontMetrics(self._labelFont)
        self._textOptions = QTextOption()
        if self._labelAlign == label.labelAlignments[0]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self._labelAlign == label.labelAlignments[1]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self._labelAlign == label.labelAlignments[2]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignRight)

        if self._labelOrient == label.labelOrients[0]:
            self.setRotation(0)
        elif self._labelOrient == label.labelOrients[1]:
            self.setRotation(90)
        elif self._labelOrient == label.labelOrients[2]:
            self.setRotation(180)
        elif self._labelOrient == label.labelOrients[3]:
            self.setRotation(270)

        self._rect = self._fm.boundingRect( self._labelText, self._textOptions)

    def boundingRect(self):
        return self._rect.adjusted(-2, 2, 2, 2)

    def flip(self, direction: str):
        currentTransform = self.transform()
        newTransform = QTransform()
        if direction == 'x':
            currentTransform = newTransform.scale(-1,1)*currentTransform
        elif direction == 'y':
            currentTransform = newTransform.scale(1,-1)*currentTransform
        self.setTransform(currentTransform)
