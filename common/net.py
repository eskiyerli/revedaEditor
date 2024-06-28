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

import math
from enum import Enum
from typing import List, Set, Tuple, Union

# net class definition.
from PySide6.QtCore import (
    QPoint,
    Qt,
    QLineF,
    QRectF,
    QPointF,
    QRect,
)
from PySide6.QtGui import (
    QPen, QPainter,
    QStaticText,
    QPainterPath,
    QFont,
)
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
)

import pdk.schLayers as schlyr


# class netNameStrengthEnum(Enum):
#     NONAME = 1
#     INHERIT = 2
#     SET = 3


# class pointSelfIndex(NamedTuple):
#     point: QPoint
#     selfIndex: int
#
#
#



class NetMode(Enum):
    ORTHOGONAL = 0
    DIAGONAL = 1
    FREE = 2


class netNameStrengthEnum(Enum):
    NONAME = 0
    WEAK = 1
    INHERIT = 2
    SET = 3


class schematicNet(QGraphicsItem):
    SNAP_DISTANCE = 2
    NAME_FONT_SIZE = 8

    def __init__(self, start: QPointF, end: QPointF, mode: NetMode = NetMode.ORTHOGONAL):
        super().__init__()
        self.netNameStrengthEnum = None
        self._setupFlags()
        self._initializeAttributes(start, end, mode)

    def _setupFlags(self):
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def _initializeAttributes(self, start: QPointF, end: QPointF, mode: NetMode):
        self._mode = mode
        self._name = ""
        self._nameConflict = False
        self._nameStrength = netNameStrengthEnum.NONAME
        self._highlighted = False
        self._flightLinesSet: Set['schematicNet'] = set()
        self._connectedNetsSet: Set['schematicNet'] = set()
        self._netSnapLines: dict = {}
        self._stretch = False
        self._stretchSide = ""
        self._setupNameAttributes()
        self._setupDraftLine(start, end)

    def _setupNameAttributes(self):
        self._nameFont = QFont()
        self._nameFont.setPointSize(self.NAME_FONT_SIZE)
        self._nameItem = QStaticText(self._name)

    def _setupDraftLine(self, start: QPointF, end: QPointF):
        self._draftLine = QLineF(start, end)
        self._transformOriginPoint = self._draftLine.p1()
        self._angle = self._calculateAngle()
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._transformOriginPoint)
        self._updateRectangles()
        self.setRotation(-self._angle)

    def _calculateAngle(self) -> float:
        baseAngle = self._draftLine.angle()
        if self._mode == NetMode.ORTHOGONAL:
            return 90 * math.floor(
                ((baseAngle + 45) % 360) / 90
            )
        elif self._mode == NetMode.DIAGONAL:
            return 45 * math.floor(
                ((baseAngle + 22.5) % 360) / 45
            )
        return baseAngle

    def _updateRectangles(self):
        self._shapeRect = QRectF(self._draftLine.p1(), self._draftLine.p2()).adjusted(-2, -2, 2,
                                                                                      2)
        self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)

    @property
    def draftLine(self) -> QLineF:
        return self._draftLine

    @draftLine.setter
    def draftLine(self, line: QLineF):
        self.prepareGeometryChange()
        self._draftLine = line
        self._transformOriginPoint = line.p1()
        self._angle = self._calculateAngle()
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._transformOriginPoint)
        self._updateRectangles()
        self.setRotation(-self._angle)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self._shapeRect)
        return path

    def boundingRect(self) -> QRectF:
        return self._boundingRect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setFont(self._nameFont)
        pen = self._getPen()
        painter.setPen(pen)
        painter.drawLine(self._draftLine)

        if self._nameStrength == netNameStrengthEnum.SET:
            self._drawName(painter)

    def _getPen(self):
        if self.isSelected():
            return schlyr.selectedWirePen
        elif self._stretch:
            return schlyr.stretchWirePen
        elif self._highlighted:
            return schlyr.hilightPen
        elif self._nameConflict:
            return schlyr.errorWirePen
        else:
            return schlyr.wirePen

    def _drawName(self, painter: QPainter):
        painter.save()
        painter.translate(self._draftLine.center())
        painter.rotate(self._angle)
        painter.drawStaticText(0, 0, self._nameItem)
        painter.restore()

    def __repr__(self):
        return f"SchematicNet({self.sceneEndPoints})"

    def itemChange(self, change, value):
        if self.scene() and change == QGraphicsItem.ItemSelectedHasChanged:
            self.scene().selectedNet = self if value else None
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        super().mousePressEvent(event)
        if self._stretch:
            self._handleStretch(event)

    def _handleStretch(self, event: QGraphicsSceneMouseEvent):
        eventPos = event.pos().toPoint()
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        if (
                eventPos - self._draftLine.p1().toPoint()).manhattanLength() <= self.scene().snapDistance:
            self.setCursor(Qt.SizeHorCursor)
            self._stretchSide = "p1"
        elif (
                eventPos - self._draftLine.p2().toPoint()).manhattanLength() <= self.scene().snapDistance:
            self.setCursor(Qt.SizeHorCursor)
            self._stretchSide = "p2"
        self.scene().stretchNet(self, self._stretchSide)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverEnterEvent(event)
        if self.scene().highlightNets:
            self._highlighted = True
            self._connectedNetsSet = self.scene().findConnectedNetSet(self)
            self._highlightConnectedNets()
            self._createFlightLines()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        if self._highlighted:
            self._highlighted = False
            self._removeFlightLines()
            self._unhighlightConnectedNets()

    def _highlightConnectedNets(self):
        for netItem in self._connectedNetsSet:
            netItem.highlight()

    def _createFlightLines(self):
        for netItem in self._connectedNetsSet:
            flightLine = netFlightLine(
                self.mapToScene(self._draftLine.center()),
                netItem.mapToScene(netItem.draftLine.center()),
            )
            self._flightLinesSet.add(flightLine)
            self.scene().addItem(flightLine)

    def _removeFlightLines(self):
        for flightLine in self._flightLinesSet:
            self.scene().removeItem(flightLine)
        self._flightLinesSet.clear()

    def _unhighlightConnectedNets(self):
        for netItem in self._connectedNetsSet:
            netItem.unhighlight()

    def isParallel(self, otherNet: 'schematicNet') -> bool:
        return abs((self.angle - otherNet.angle) % 180) < 1

    def isOrthogonal(self, otherNet: 'schematicNet') -> bool:
        return abs((self.angle - otherNet.angle - 90) % 180) < 1

    def findOverlapNets(self) -> Set['schematicNet']:
        if not self.scene():
            return set()
        return {netItem for netItem in self.collidingItems() if
                isinstance(netItem, schematicNet)} - {self}

    def mergeNets(self) -> Tuple['schematicNet', 'schematicNet']:
        otherNets = self.findOverlapNets()
        if not otherNets:
            return self, self

        parallelNets = [netItem for netItem in otherNets if self.isParallel(netItem)]
        if not parallelNets:
            return self, self

        initialRect = self.sceneShapeRect
        for netItem in parallelNets:
            self.inherit(netItem)
            if self.nameConflict:
                break
            initialRect = initialRect.united(netItem.sceneShapeRect)
            if self.scene():
                self.scene().removeItem(netItem)

        if not self.nameConflict:
            newNetPoints = initialRect.adjusted(2, 2, -2, -2)
            x1, y1, x2, y2 = newNetPoints.getCoords()
            newNet = schematicNet(
                self.snapToGrid(QPoint(x1, y1)), self.snapToGrid(QPoint(x2, y2))
            )
            newNet.inherit(self)
            return self, newNet

        return self, self

    def snapToGrid(self, point: Union[QPoint, QPointF]) -> Union[QPoint, QPointF]:
        if self.scene():
            return self.scene().snapToGrid(point, self.scene().snapTuple)
        return point

    def inherit(self, otherNet: 'schematicNet'):
        if self.nameStrength == netNameStrengthEnum.SET:
            if otherNet.nameStrength == netNameStrengthEnum.SET and self.name != otherNet.name:
                self.nameConflict = True
                otherNet.nameConflict = True
        elif otherNet.nameStrength.value > netNameStrengthEnum.WEAK.value:
            self.name = otherNet.name
            self.nameStrength = netNameStrengthEnum.INHERIT

    def inheritGuideLine(self, otherNet: 'guideLine'):
        self.name = otherNet.name
        self.nameStrength = otherNet.nameStrength

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        if name:
            self.prepareGeometryChange()
            self._name = name
            self._nameItem = QStaticText(self._name)

    @property
    def nameStrength(self) -> netNameStrengthEnum:
        return self._nameStrength

    @nameStrength.setter
    def nameStrength(self, value: netNameStrengthEnum):
        assert isinstance(value, netNameStrengthEnum)
        self._nameStrength = value

    @property
    def nameConflict(self) -> bool:
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        self._nameConflict = value

    @property
    def endPoints(self) -> List[QPoint]:
        return [self._draftLine.p1().toPoint(), self._draftLine.p2().toPoint()]

    @property
    def sceneEndPoints(self) -> List[QPoint]:
        return [
            self.mapToScene(self._draftLine.p1()).toPoint(),
            self.mapToScene(self._draftLine.p2()).toPoint(),
        ]

    def highlight(self):
        self._highlighted = True
        self.update()

    def unhighlight(self):
        self._highlighted = False
        self.update()

    @property
    def highlighted(self) -> bool:
        return self._highlighted

    @highlighted.setter
    def highlighted(self, value: bool):
        self._highlighted = value

    @property
    def sceneShapeRect(self) -> QRect:
        return self.mapRectToScene(self._shapeRect).normalized().toRect()

    @property
    def stretch(self) -> bool:
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value

    @property
    def stretchSide(self) -> str:
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float):
        self._angle = value

#
# class schematicNet(QGraphicsItem):
#     _netSnapLines: dict
#     __slots__ = (
#         "_mode",
#         "_name",
#         "_nameConflict",
#         "_netNameStrength",
#         "_highlighted",
#         "_flightLinesSet",
#         "_connectedNetsSet",
#         "_netIndexTupleSet",
#         "_scene",
#         "_netSnapLines",
#         "_stretch",
#         "_stretchSide",
#         "_nameFont",
#         "_nameItem",
#         "_draftLine",
#         "_shapeRect",
#         "_boundingRect",
#         "_angle",
#         "_transformOriginPoint",
#     )
#
#     def __init__(self, start: QPoint, end: QPoint, mode: int = 0):
#         super().__init__()
#         self.setFlag(QGraphicsItem.ItemIsMovable, True)
#         self.setFlag(QGraphicsItem.ItemIsSelectable, True)
#         self.setFlag(QGraphicsItem.ItemIsFocusable, True)
#         # self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
#         self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
#         self.setAcceptHoverEvents(True)
#         self._mode = 0
#         self._name: str = ""
#         self._nameConflict: bool = False
#         self._nameAdded: bool = False
#         self._nameSet: bool = False
#         self._nameStrength: netNameStrengthEnum = netNameStrengthEnum.NONAME
#         self._highlighted: bool = False
#         self._flightLinesSet: set[schematicNet] = set()
#         self._connectedNetsSet: set[schematicNet] = set()
#         self._netSnapLines: dict = {}
#         self._stretch: bool = False
#         self._stretchSide: str = ""
#         self._nameFont = QFont()
#         self._nameFont.setPointSize(8)
#         self._nameItem = QStaticText(self._name)
#         self._draftLine = QLineF(start, end)
#         self._transformOriginPoint = self._draftLine.p1()
#         self._angle = None
#         match self._mode:
#             case 0:
#                 self._angle = 90 * math.floor(
#                     ((self._draftLine.angle() + 45) % 360) / 90
#                 )
#             case 1:
#                 self._angle = 45 * math.floor(
#                     ((self._draftLine.angle() + 22.5) % 360) / 45
#                 )
#             case 2:
#                 self._angle = self._draftLine.angle()
#         self._draftLine.setAngle(0)
#         self.setTransformOriginPoint(self._transformOriginPoint)
#         self._shapeRect = QRectF(self._draftLine.p1(), self._draftLine.p2()).adjusted(
#             -2, -2, 2, 2
#         )
#         self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
#         self.setRotation(-self._angle)
#
#     @property
#     def draftLine(self):
#         return self._draftLine
#
#     @draftLine.setter
#     def draftLine(self, line: QLineF):
#         self.prepareGeometryChange()
#         self._draftLine = line
#         self._transformOriginPoint = line.p1()
#         match self._mode:
#             case 0:
#                 self._angle = 90 * math.floor(
#                     ((self._draftLine.angle() + 45) % 360) / 90
#                 )
#             case 1:
#                 self._angle = 45 * math.floor(
#                     ((self._draftLine.angle() + 22.5) % 360) / 45
#                 )
#             case 2:
#                 self._angle = self._draftLine.angle()
#         self._draftLine.setAngle(0)
#         self.setTransformOriginPoint(self._transformOriginPoint)
#
#         self._shapeRect = (
#             QRectF(self._draftLine.p1(), self._draftLine.p2())
#             .normalized()
#             .adjusted(-2, -2, 2, 2)
#         )
#         self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
#         self.setRotation(-self._angle)
#
#     def shape(self) -> QPainterPath:
#         path = QPainterPath()
#         path.addRect(self._shapeRect)
#         return path
#
#     def boundingRect(self):
#         return self._boundingRect
#
#     def paint(self, painter, option, widget=...):
#         painter.setFont(self._nameFont)
#         if self.isSelected():
#             pen = schlyr.selectedWirePen
#         elif self._stretch:
#             pen = schlyr.stretchWirePen
#         elif self._highlighted:
#             pen = schlyr.hilightPen
#         elif self._nameConflict:
#             pen = schlyr.errorWirePen
#         else:
#             pen = schlyr.wirePen
#
#         painter.setPen(pen)
#         painter.drawLine(self._draftLine)
#         # painter.drawEllipse(self._draftLine.p1(), 2, 2)
#         if self._nameStrength.value == 3:
#             painter.save()
#             painter.translate(
#                 self._draftLine.center().x(), self._draftLine.center().y()
#             )
#             painter.rotate(self._angle)
#             painter.drawStaticText(0, 0, self._nameItem)
#             painter.restore()
#
#     def __repr__(self):
#         return f"schematicNet({self.sceneEndPoints})"
#
#     def itemChange(self, change, value):
#         if self.scene():
#             if change == QGraphicsItem.ItemSelectedHasChanged:
#                 if value:
#                     self.scene().selectedNet= self
#                 else:
#                     self.scene().selectedNet = None
#         return super().itemChange(change, value)
#
#     def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
#         super().mousePressEvent(event)
#         if self._stretch:
#             eventPos = event.pos().toPoint()
#             self.setFlag(QGraphicsItem.ItemIsMovable, False)
#             if (
#                 eventPos - self._draftLine.p1().toPoint()
#             ).manhattanLength() <= self.scene().snapDistance:
#                 self.setCursor(Qt.SizeHorCursor)
#                 self._stretchSide = "p1"
#             elif (
#                 eventPos - self._draftLine.p2().toPoint()
#             ).manhattanLength() <= self.scene().snapDistance:
#                 self.setCursor(Qt.SizeHorCursor)
#                 self._stretchSide = "p2"
#             self.scene().stretchNet(self, self._stretchSide)
#
#     def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
#         """
#         Override the hoverEnterEvent method of QGraphicsItem.
#
#         Args:
#             event (QGraphicsSceneHoverEvent): The hover event.
#
#         Returns:
#             None
#         """
#         super().hoverEnterEvent(event)
#         # Check if highlightNets flag is set in the scene
#         if self.scene().highlightNets:
#             self._highlighted = True
#             self._connectedNetsSet = self.scene().findConnectedNetSet(self)
#
#             # Highlight the connected netItems
#             for netItem in self._connectedNetsSet:
#                 netItem.highlight()
#
#             # Create flight lines and add them to the scene
#             for netItem in self._connectedNetsSet:
#                 flightLine = netFlightLine(
#                     self.mapToScene(self._draftLine.center()),
#                     netItem.mapToScene(netItem.draftLine.center()),
#                 )
#                 self._flightLinesSet.add(flightLine)
#                 self.scene().addItem(flightLine)
#
#     def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
#         super().hoverLeaveEvent(event)
#         if self._highlighted:
#             self._highlighted = False
#             self._clearFlightLines()
#             self._unhighlightConnectedNets()
#
#     def _clearFlightLines(self) -> None:
#         for flight_line in self._flightLinesSet:
#             self.scene().removeItem(flight_line)
#         self._flightLinesSet.clear()
#
#     def _unhighlightConnectedNets(self) -> None:
#         for net_item in self._connectedNetsSet:
#             net_item.unhighlight()
#
#     def isParallel(self, otherNet: "schematicNet") -> bool:
#         return abs((self.angle - otherNet.angle) % 180) < 1
#
#     def isOrthogonal(self, otherNet: "schematicNet") -> bool:
#         return abs((self.angle - otherNet.angle - 90) % 180) < 1
#
#     def notParallel(self, otherNet: "schematicNet") -> bool:
#         return not self.isParallel(otherNet)
#
#     def findOverlapNets(self) -> set["schematicNet"]:
#         """
#         Find all netItems in the scene that overlap with self.sceneShapeRect.
#
#         Returns:
#             set: A set of netItems that overlap with self.sceneShapeRect.
#         """
#         overlapNets = set()
#         if self.scene():
#             # overlapNets = {
#             #     netItem
#             #     for netItem in self.scene().items(self.sceneShapeRect)
#             #     if isinstance(netItem, schematicNet)
#             # }
#             overlapNets = {netItem for netItem in self.collidingItems() if isinstance(netItem, schematicNet)}
#             return overlapNets - {self}
#
#     def mergeNets(self) -> tuple["schematicNet", "schematicNet"]:
#         """
#         Merges overlapping nets and returns the merged net.
#
#         Returns:
#             Optional[schematicNet]: The merged net if there are overlapping nets, otherwise returns self.
#         """
#         # Find other nets that overlap with self
#         otherNets = self.findOverlapNets()
#         # If there are other nets
#         if otherNets:
#             # Filter the other nets to find the parallel ones
#             parallelNets = [
#                 netItem for netItem in otherNets if self.isParallel(netItem)
#             ]
#
#             # If there are parallel nets
#             if parallelNets:
#                 # Create an initialRect variable and set it to self's sceneShapeRect
#                 initialRect = self.sceneShapeRect
#
#                 # Iterate over the parallel nets
#                 for netItem in parallelNets:
#                     # Update the initialRect by uniting it with each parallel net's
#                     # sceneShapeRect
#                     self.inherit(netItem)
#                     if not self.nameConflict:
#                         initialRect = initialRect.united(netItem.sceneShapeRect)
#                         if self.scene():
#                             self.scene().removeItem(netItem)
#                     else:
#                         break  # break out of the for loop
#                 if not self.nameConflict:
#                     # Adjust the initialRect by 2 pixels on each side
#                     newNetPoints = initialRect.adjusted(2, 2, -2, -2)
#
#                     # Get the coordinates of the adjusted rectangle
#                     x1, y1, x2, y2 = newNetPoints.getCoords()
#
#                     # Create a new schematicNet with the snapped coordinates
#                     newNet = schematicNet(
#                         self.snapToGrid(QPoint(x1, y1)), self.snapToGrid(QPoint(x2, y2))
#                     )
#                     newNet.inherit(self)
#                     return self, newNet  # original net, new net
#                 else:
#                     return self, self
#
#         # If there are no other nets or no parallel nets, return self
#         return self, self
#
#     def snapToGrid(self, point: Union[QPoint, QPointF]) -> QPoint:
#         if self.scene():
#             return self.scene().snapToGrid(point, self.scene().snapTuple)
#         else:
#             return point
#
#     def inherit(self, otherNet: Type["schematicNet"]):
#         """
#         Inherit the name of the other net if self name strength is less than SET.
#         """
#         assert isinstance(otherNet, schematicNet)
#         if self.nameStrength.value == 3:
#             if otherNet.nameStrength.value == 3 and self.name != otherNet.name:
#                 self.nameConflict = True
#                 otherNet.nameConflict = True
#         elif otherNet.nameStrength.value > 1:  # INHERIT or SET
#             self.name = otherNet.name
#             self.nameStrength = netNameStrengthEnum.INHERIT
#
#     def inheritGuideLine(self, otherNet: Type["guideLine"]):
#         self.name = otherNet.name
#         self.nameStrength = otherNet.nameStrength
#
#     @property
#     def name(self):
#         return self._name
#
#     @name.setter
#     def name(self, name):
#         if name != "":  # net name should not be an empty string
#             self.prepareGeometryChange()
#             self._name = name
#             self._nameItem = QStaticText(self._name)
#
#     @property
#     def nameStrength(self) -> netNameStrengthEnum:
#         return self._nameStrength
#
#     @nameStrength.setter
#     def nameStrength(self, value: netNameStrengthEnum):
#         assert isinstance(value, netNameStrengthEnum)
#         self._nameStrength = value
#
#     @property
#     def nameConflict(self) -> bool:
#         """
#         If two different names are attempted to be set for the net.
#         """
#         return self._nameConflict
#
#     @nameConflict.setter
#     def nameConflict(self, value: bool):
#         assert isinstance(value, bool)
#         self._nameConflict = value
#
#     @property
#     def endPoints(self):
#         return [self._draftLine.p1().toPoint(), self._draftLine.p2().toPoint()]
#
#     @property
#     def sceneEndPoints(self):
#         return [
#             self.mapToScene(self._draftLine.p1()).toPoint(),
#             self.mapToScene(self._draftLine.p2()).toPoint(),
#         ]
#
#     def highlight(self):
#         self._highlighted = True
#         self.update()
#
#     def unhighlight(self):
#         self._highlighted = False
#         self.update()
#
#     @property
#     def highlighted(self):
#         return self._highlighted
#
#     @highlighted.setter
#     def highlighted(self, value: bool):
#         self._highlighted = value
#
#     @property
#     def sceneShapeRect(self) -> QRectF:
#         return self.mapRectToScene(self._shapeRect).normalized().toRect()
#
#     @property
#     def stretch(self) -> bool:
#         return self._stretch
#
#     @stretch.setter
#     def stretch(self, value: bool):
#         self._stretch = value
#
#     @property
#     def stretchSide(self) -> int:
#         """
#         The end where the net is stretched.
#         """
#         return self._stretchSide
#
#     @stretchSide.setter
#     def stretchSide(self, value: str):
#         self.prepareGeometryChange()
#         self._stretchSide = value
#
#     @property
#     def angle(self) -> float:
#         return self._angle
#
#     @angle.setter
#     def angle(self, value: float):
#         self._angle = value
#
#     @property
#     def stretch(self) -> bool:
#         return self._stretch
#
#     @stretch.setter
#     def stretch(self, value: bool):
#         self._stretch = value
#

class netFlightLine(QGraphicsPathItem):
    wireHighlightPen = QPen(
        schlyr.wireHilightLayer.pcolor,
        schlyr.wireHilightLayer.pwidth,
        schlyr.wireHilightLayer.pstyle,
    )

    def __init__(self, start: QPoint, end: QPoint):
        self._start = start
        self._end = end
        super().__init__()

    def __repr__(self):
        return f"netFlightLine({self.mapToScene(self._start)},{self.mapToScene(self._end)})"

    def paint(self, painter, option, widget) -> None:
        painter.setPen(netFlightLine.wireHighlightPen)
        line = QLineF(self._start, self._end)
        perpendicularLine = QLineF(
            line.center(), line.center() + QPointF(-line.dy(), line.dx())
        )
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
        self.pen().setCosmetic(True)
        self._name: str = ""
        self._nameStrength: netNameStrengthEnum = netNameStrengthEnum.NONAME

    @property
    def sceneEndPoints(self) -> list[QPoint]:
        """
        Returns a list of the end points of the net in scene coordinates.

        Returns:
            list[QPoint]: A list of the end points of the net in scene coordinates.
        """
        return [
            self.mapToScene(self.line().p1()).toPoint(),
            self.mapToScene(self.line().p2()).toPoint(),
        ]

    def __repr__(self):
        return f"guideLine({self.mapToScene(self.line().p1()), self.mapToScene(self.line().p2())}"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != "":  # net name should not be an empty string
            self._name = name

    @property
    def nameStrength(self) -> netNameStrengthEnum:
        return self._nameStrength

    @nameStrength.setter
    def nameStrength(self, value: netNameStrengthEnum):
        assert isinstance(value, netNameStrengthEnum)
        self._nameStrength = value

    def inherit(self, otherNet: schematicNet):
        """
        This method is used to carry the name information of the original net
        to stretch net.
        """
        assert isinstance(otherNet, schematicNet)
        self.name = otherNet.name
        self.nameStrength = otherNet.nameStrength
