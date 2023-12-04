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

# net class definition.
from PySide6.QtCore import (QPoint, Qt, QLineF, QRectF, QPointF, )
from PySide6.QtGui import (QPen, QStaticText, QPainterPath, QFont, )
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem, QGraphicsPathItem,
                               QGraphicsEllipseItem, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent, )
import pdk.schLayers as schlyr
import math
import itertools as itt
from typing import (Union, Optional, )


class crossingDot(QGraphicsEllipseItem):
    def __init__(self, point: QPoint, radius: int):
        self.radius = radius
        self.point = point
        super().__init__(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius)
        self.setPen(schlyr.wirePen)
        self.setBrush(schlyr.wireBrush)
        self._name = None

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(schlyr.selectedWirePen)
            painter.setBrush(schlyr.selectedWireBrush)
        else:
            painter.setPen(schlyr.wirePen)
            painter.setBrush(schlyr.wireBrush)
        painter.drawEllipse(self.point, self.radius, self.radius)


class schematicNet(QGraphicsItem):
    def __init__(self, start: QPoint, end: QPoint, mode: int = 0):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        # self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self._mode = 0
        self._name: str = ""
        self._nameConflict: bool = False
        self._nameAdded: bool = False
        self._nameSet: bool = False
        self._highlighted: bool = False
        self._flightLinesSet: set[schematicNet] = set()
        self._connectedNetsSet: set[schematicNet] = set()
        self._wiredEnds: set[int] = set()
        self._snapGuideLines: dict[int, guideLine] = dict()
        self._stretch: bool = False
        self._nameFont = QFont()
        self._nameFont.setPointSize(8)
        self._nameItem = QStaticText(self._name)
        self._draftLine = QLineF(start, end)
        self._guideLine: Optional[guideLine] = None
        match self._mode:
            case 0:
                self._angle = 90 * math.floor(((self._draftLine.angle() + 45) % 360) / 90)
            case 1:
                self._angle = 45 * math.floor(((self._draftLine.angle() + 22.5) % 360) / 45)
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._draftLine.p1())
        if self.scene():
            self._draftLine.setP2(
                self.scene().snapToGrid(self._draftLine.p2(), self.scene().snapTuple))
        self._shapeRect = QRectF(self._draftLine.p1(), self._draftLine.p2()).adjusted(-2,
                                                                                      -2, 2, 2)
        self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
        self.setRotation(-self._angle)

    @property
    def draftLine(self):
        return self._draftLine

    @draftLine.setter
    def draftLine(self, line: QLineF):
        self.prepareGeometryChange()
        self._draftLine = line
        match self._mode:
            case 0:
                self._angle = 90 * math.floor(((self._draftLine.angle() + 45) % 360) / 90)
            case 1:
                self._angle = 45 * math.floor(((self._draftLine.angle() + 22.5) % 360) / 45)
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._draftLine.p1())
        if self.scene():
            self._draftLine.setP2(
                self.scene().snapToGrid(self._draftLine.p2(), self.scene().snapTuple))
        self._shapeRect = QRectF(self._draftLine.p1(),
                                 self._draftLine.p2()).normalized().adjusted(-2, -2, 2, 2)
        self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
        self.setRotation(-self._angle)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self._shapeRect)
        return path

    def boundingRect(self):
        return self._boundingRect

    def paint(self, painter, option, widget=...):

        painter.setFont(self._nameFont)
        if self.isSelected():
            pen = schlyr.selectedWirePen
            if self._stretch:
                pen = schlyr.stretchWirePen
        elif self._highlighted:
            pen = schlyr.hilightPen
        else:
            pen = schlyr.wirePen
        painter.setPen(pen)

        painter.drawLine(self._draftLine)
        # painter.drawRect(self.innerRect)
        painter.save()
        painter.translate(self._draftLine.center().x(), self._draftLine.center().y())
        painter.rotate(self._angle)
        painter.drawStaticText(0, 0, self._nameItem)
        painter.restore()


    def sceneEvent(self, event):
        """
        Handle events related to the scene.

        Args:
            event: The event to handle.

        Returns:
            True if the event was handled successfully, False otherwise.
        """
        # Check if the current scene has the drawWire edit mode enabled
        if self.scene() and self.scene().editModes.drawWire:
            return False
        else:
            # Call the parent class's sceneEvent method to handle the event
            super().sceneEvent(event)
        return True

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.clearDots()
        self.mergeNets()
        self.splitNets()
        self.createDots()
        self.findConnectedEndPoints()
        if self._wiredEnds:
            for netEndIndex in self._wiredEnds:
                if self._snapGuideLines.get(netEndIndex) is None:
                    sceneEndPoint = self.sceneEndPoints[netEndIndex]
                    self._snapGuideLines[netEndIndex] = guideLine(sceneEndPoint,
                                                                  sceneEndPoint)
        if self._stretch:
            eventPos = event.scenePos().toPoint()
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            if (eventPos - self.mapToScene(
                    self._draftLine.p1()).toPoint()).manhattanLength() <= self.scene().snapDistance:
                self.setCursor(Qt.SizeHorCursor)
                self._guideLine = guideLine(self.mapToScene(self._draftLine.p1()), eventPos)
            elif (eventPos - self.mapToScene(
                    self._draftLine.p2()).toPoint()).manhattanLength() <= self.scene().snapDistance:
                self.setCursor(Qt.SizeHorCursor)
                self._guideLine = guideLine(self.mapToScene(self._draftLine.p2()), eventPos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._snapGuideLines:
            for netEndIndex, guideLine in self._snapGuideLines.items():
                if guideLine.scene() is None:
                    self.scene().addItem(guideLine)
                guideLine.setLine(QLineF(guideLine.line().p1(), guideLine.mapFromScene(
                    self.sceneEndPoints[netEndIndex])))

        elif self.stretch:
            eventPos = event.scenePos().toPoint()
            if self._guideLine is not None:
                if self._guideLine.scene() is None:
                    self.scene().addItem(self._guideLine)
                self._guideLine.setLine(QLineF(self._guideLine.line().p1(),
                                               self._guideLine.mapFromScene(eventPos)))

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        self.clearDots()
        self.mergeNets()
        self.splitNets()
        self.createDots()
        if self._snapGuideLines and self.scene():
            for guideLine in self._snapGuideLines.values():
                self.scene().addStretchWires(*guideLine.sceneEndPoints)
                self.scene().removeItem(guideLine)
            self._snapGuideLines = dict()
            self._wiredEnds = set()
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            if self._guideLine and self.scene():
                lines = self.scene().addStretchWires(*self._guideLine.sceneEndPoints)
                self.scene().removeItem(self._guideLine)
            for line in lines:
                line.mergeNets()
            self._guideLine = None
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        Override the hoverEnterEvent method of QGraphicsItem.

        Args:
            event (QGraphicsSceneHoverEvent): The hover event.

        Returns:
            None
        """
        super().hoverEnterEvent(event)

        # Check if highlightNets flag is set in the scene
        if self.scene().highlightNets:
            # Create a set of connected netItems based on certain conditions
            self._connectedNetsSet = {netItem for netItem in self.scene().items() if (
                    isinstance(netItem, schematicNet) and (
                    self.nameSet or self.nameAdded) and netItem.name == self.name)}

            # Highlight the connected netItems
            for netItem in self._connectedNetsSet:
                netItem.highlight()

            # Create flight lines and add them to the scene
            for netItem in self._connectedNetsSet:
                flightLine = netFlightLine(self.mapToScene(self._draftLine.center()),
                                           netItem.mapToScene(netItem.draftLine.center()), )
                self._flightLinesSet.add(flightLine)
                self.scene().addItem(flightLine)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        if self._highlighted:
            for flightLine in self._flightLinesSet:
                self.scene().removeItem(flightLine)
            self._flightLinesSet = set()
        [netItem.unhighlight() for netItem in self._connectedNetsSet]

    def isParallel(self, otherNet: "schematicNet") -> bool:
        return abs((self.angle - otherNet.angle) % 180) < 1

    def isOrthogonal(self, otherNet: "schematicNet") -> bool:
        return abs((self.angle - otherNet.angle - 90) % 180) < 1

    def notParallel(self, otherNet: "schematicNet") -> bool:
        return not self.isParallel(otherNet)

    def containsDot(self, dot: crossingDot) -> bool:
        if self.sceneShapeRect.contains(self.mapFromScene(dot.point)):
            return True
        return False

    def findOverlapNets(self):
        """
        Find all netItems in the scene that overlap with self.sceneShapeRect.

        Returns:
            set: A set of netItems that overlap with self.sceneShapeRect.
        """
        if self.scene():
            overlapNets = {netItem for netItem in self.scene().items(self.sceneShapeRect) if
                           isinstance(netItem, schematicNet) and netItem is not self}
        else:
            overlapNets = set()
        return overlapNets

    def splitNets(self):
        otherNets = self.findOverlapNets()
        if otherNets:
            orthoNets = list(filter(self.isOrthogonal, otherNets))
            if orthoNets:
                # if self is dividing another net
                self.createSplitNets(orthoNets)

                # if another net is dividing self.
                for orthoNet in orthoNets:
                    orthoNet.createSplitNets([self])

    def createSplitNets(self, orthoNets: list):
        for orthoNet, end in itt.product(orthoNets, self.sceneEndPoints):
            if orthoNet.sceneInnerRect.contains(end):
                newNet1 = schematicNet(end, orthoNet.mapToScene(orthoNet.draftLine.p2()))
                self.scene().addItem(newNet1)
                newNet2 = schematicNet(orthoNet.mapToScene(orthoNet.draftLine.p1()), end)
                self.scene().addItem(newNet2)
                self.scene().removeItem(orthoNet)
                if self._nameSet:
                    newNet1.name, newNet2.name = self._name, self._name
                    newNet1.nameSet, newNet2.nameSet = self._nameSet, self._nameSet
                if self._nameAdded:
                    newNet1.name, newNet2.name = self._name, self._name
                    newNet1.nameAdded, newNet2.nameAdded = self._nameAdded, self._nameAdded

    def mergeNets(self):
        otherNets = self.findOverlapNets()
        if otherNets:
            parallelNets = list(filter(self.isParallel, otherNets))
            if parallelNets:
                initialRect = self.sceneShapeRect
                for netItem in parallelNets:
                    initialRect = initialRect.united(netItem.sceneShapeRect)
                    netItem.scene().removeItem(netItem)
                newNetPoints = initialRect.adjusted(2, 2, -2, -2)
                x1, y1, x2, y2 = newNetPoints.getCoords()
                newNet = schematicNet(self.snapToGrid(QPoint(x1, y1)),
                                      self.snapToGrid(QPoint(x2, y2)))
                if self._nameSet:
                    newNet.name = self._name
                    newNet.nameSet = self._nameSet
                if self._nameAdded:
                    newNet.name = self._name
                    newNet.nameAdded = self._nameAdded
                self.scene().addItem(newNet)
                self.scene().removeItem(self)
                newNet.mergeNets()

    def clearDots(self):
        [self.scene().removeItem(item) for item in self.scene().items(self.sceneShapeRect)
         if isinstance(item, crossingDot)]

    def createDots(self):
        otherNets = self.findOverlapNets()
        netCombinations = set(itt.combinations(otherNets, 2))
        for netCombination in netCombinations:
            net2, net3 = netCombination
            if net2 and net3:
                for netEnd1, netEnd2, netEnd3 in itt.product(self.sceneEndPoints,
                                                             net2.sceneEndPoints, net3.sceneEndPoints):
                    if netEnd1 == netEnd2 and netEnd2 == netEnd3:
                        newDot = crossingDot(netEnd1, 5)
                        self.scene().addItem(newDot)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != "":  # net name should not be an empty string
            self.prepareGeometryChange()
            self._name = name
            self._nameItem = QStaticText(self._name)

    @property
    def nameSet(self) -> bool:
        """
        Check if the name of the net is explicitly set.

        Returns:
            bool: The value of the 'nameSet' attribute.
        """
        return self._nameSet

    @nameSet.setter
    def nameSet(self, value: bool):
        """
        If the name of the net is explicitly set, set this attribute to True.

        Args:
            value (bool): The value to set for the 'nameSet' attribute.

        Raises:
            AssertionError: If the input value is not a boolean.
        """
        assert isinstance(value, bool)
        self._nameSet = value

    @property
    def nameAdded(self) -> bool:
        """
        Name added is true if net name is set due to a connected net or pin.
        """
        return self._nameAdded

    @nameAdded.setter
    def nameAdded(self, value: bool):
        assert isinstance(value, bool)
        self._nameAdded = value

    @property
    def nameConflict(self) -> bool:
        """
        If two different names are attempted to be set for the net.
        """
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        assert isinstance(value, bool)
        self._nameConflict = value

    @property
    def sceneEndPoints(self):
        return [self.mapToScene(self._draftLine.p1()).toPoint(),
                self.mapToScene(self._draftLine.p2()).toPoint(), ]

    def highlight(self):
        self._highlighted = True
        self.update()

    def unhighlight(self):
        self._highlighted = False
        self.update()

    @property
    def highlighted(self):
        return self._highlighted

    @highlighted.setter
    def highlighted(self, value: bool):
        self._highlighted = value

    @property
    def sceneShapeRect(self) -> QRectF:
        return self.mapRectToScene(self._shapeRect).normalized().toRect()

    @property
    def stretch(self) -> bool:
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value

    @property
    def stretchSide(self):
        '''
        The end where the net is stretched.
        '''
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    @property
    def angle(self):
        return self._angle

    @property
    def innerRect(self) -> QRectF:
        return (
            QRectF(self._draftLine.p1(), self._draftLine.p2()).normalized().adjusted(2, 2,
                                                                                     -2,
                                                                                     -2))

    @property
    def sceneInnerRect(self) -> QRectF:
        return self.mapRectToScene(self.innerRect)

    def findConnectedEndPoints(self):
        self._wiredEnds = set()  # empty wired ends set
        otherNets = self.findOverlapNets()
        for otherNet in otherNets:
            for selfEnd, otherEnd in itt.product(self.sceneEndPoints,
                                                 otherNet.sceneEndPoints):
                # not a very elegant solution to mistakes in net end points.
                if (selfEnd - otherEnd).manhattanLength() <= 1:
                    self._wiredEnds.add(self.sceneEndPoints.index(selfEnd))

    def snapToGrid(self, point: Union[QPoint, QPointF]) -> QPoint:
        if self.scene():
            return self.scene().snapToGrid(point, self.scene().snapTuple)
        else:
            return point


class netFlightLine(QGraphicsPathItem):
    wireHighlightPen = QPen(schlyr.wireHilightLayer.pcolor, schlyr.wireHilightLayer.pwidth,
                            schlyr.wireHilightLayer.pstyle, )

    def __init__(self, start: QPoint, end: QPoint):
        self._start = start
        self._end = end
        super().__init__()

    def paint(self, painter, option, widget) -> None:
        painter.setPen(netFlightLine.wireHighlightPen)
        line = QLineF(self._start, self._end)
        perpendicularLine = QLineF(line.center(),
                                   line.center() + QPointF(-line.dy(), line.dx()))
        perpendicularLine.setLength(100)

        path = QPainterPath()
        path.moveTo(self._start)
        path.quadTo(perpendicularLine.p2(), self._end)
        painter.drawPath(path)


class guideLine(QGraphicsLineItem):
    def __init__(self, start: QPoint, end: QPoint):
        self._start = start
        self._end = end
        super().__init__(QLineF(self._start, self._end))
        self.setPen(schlyr.guideLinePen)

    @property
    def sceneEndPoints(self) -> list[QPoint]:
        return [self.mapToScene(self.line().p1()).toPoint(),
                self.mapToScene(self.line().p2()).toPoint()]
