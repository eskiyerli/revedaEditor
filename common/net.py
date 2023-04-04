
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
from PySide6.QtCore import (QPoint, Qt, QLineF, QRect)
from PySide6.QtGui import (QPen, QStaticText, )
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem,
                               QGraphicsEllipseItem, QGraphicsSceneMouseEvent)
# import revedaEditor.common.pens as pens
import revedaEditor.backend.dataDefinitions as ddef


class schematicNet(QGraphicsLineItem):
    '''
    Base schematic net class.
    '''
    uses = ["SIGNAL", "ANALOG", "CLOCK", "GROUND", "POWER", ]


    def __init__(self, start: QPoint, end: QPoint, pen: QPen):
        assert isinstance(pen, QPen)
        self._pen = pen
        self._name = None
        self._horizontal = True
        self._start = start
        self._end = end
        self._nameSet = False  # if a name has been set
        self._nameConflict = False  # if a name conflict has been detected
        self._connections = dict()  # dictionary of connections
        super().__init__(QLineF(self._start, self._end))
        self.setPen(self._pen)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self._createdNets = dict()



    def __repr__(self):
        return f"schematicNet(start={self.mapToScene(self._start)}, " \
               f"end={self.mapToScene(self._end)}"


    def paint(self, painter, option, widget) -> None:

        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
        else:
            painter.setPen(self._pen)
        painter.drawLine(self._start, self._end)
        if self.name is not None:
            painter.drawStaticText(self._start, QStaticText(self.name))
            # if there is name conflict, draw the line and name in red.
            if self._nameConflict:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.drawStaticText(self._start, QStaticText(self.name))
                painter.drawLine(self._start, self._end)

    def sceneEvent(self, event):
        try:
            if self.scene().drawWire:
                return False
            else:
                super().sceneEvent(event)
                return True
        except AttributeError:
            return False

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start: QPoint):
        self._start = start
        self.setLine(QLineF(self._start, self._end))

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self._end = end
        self.setLine(QLineF(self._start, self._end))

    @property
    def pen(self):
        return self._pen

    @pen.setter
    def pen(self, pen: QPen):
        self._pen = pen

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        # self._nameSet = True

    @property
    def horizontal(self):
        return self._horizontal


    @property
    def nameSet(self) -> bool:
        return self._nameSet

    @nameSet.setter
    def nameSet(self, value: bool):
        assert isinstance(value,bool)
        self._nameSet = value

    @property
    def nameConflict(self) -> bool:
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        assert isinstance(value,bool)
        self._nameConflict = value

    @property
    def length(self):
        return self.line().length()

    def otherEnd(self, end: QPoint):
        if end == self._start:
            return self._end
        elif end == self._end:
            return self._start
        else:
            return None

    @property
    def horizontal(self):
        if self._end.y() == self._start.y():
            self._horizontal = True
        elif self._end.x() == self._start.x():
            self._horizontal = False
        else:
            self._horizontal = True
        return self._horizontal


    def mergeNets(self,) -> None:
        # check any overlapping nets in the view
        # editing is done in the view and thus there is no need to check all nets in the scene
        try:
            horizontalNetsInView = {item for item in self.scene().parent.view.viewNetItemsSet if
                                    item.horizontal}

            verticalNetsInView = {item for item in self.scene().parent.view.viewNetItemsSet if
                                    not item.horizontal}
            # pinsInView = {item for item in self.scene().parent.view.items(viewRect) if (
            #     isinstance(item, shp.pin))
            dBNetRect = self.sceneBoundingRect()
            if len(horizontalNetsInView) > 1 and self.horizontal:
                for netItem in horizontalNetsInView - {self, }:
                    netItemBRect = netItem.sceneBoundingRect()
                    if dBNetRect.intersects(netItemBRect):
                        # print(f'net item start: {netItem.start}, end: {netItem.end}')
                        # print(f'self start: {self.start}, end: {self.end}')
                        newXstart = min([self.start.x(), self.end.x(), netItem.start.x(),
                                        netItem.end.x()])
                        newXend = max([self.start.x(), self.end.x(), netItem.start.x(),
                                        netItem.end.x()])
                        self.start = QPoint(newXstart, self.start.y())
                        self.end = QPoint(newXend, self.end.y())
                        self.scene().removeItem(netItem)  # remove the old net from the scene
                        del netItem
                        self.scene().schematicWindow.messageLine.setText("Merged Nets")
            elif len(verticalNetsInView) > 1 and not self.horizontal:
                for netItem in verticalNetsInView - {self, }:
                    netItemBRect = netItem.sceneBoundingRect()
                    if dBNetRect.intersects(netItemBRect):
                        newYstart = min([self.start.y(), self.end.y(), netItem.start.y(),
                                        netItem.end.y()])
                        newYend = max([self.start.y(), self.end.y(), netItem.start.y(),
                                        netItem.end.y()])
                        self.start = QPoint(self.start.x(), newYstart)
                        self.end = QPoint(self.end.x(), newYend)
                        self.scene().removeItem(netItem)  # remove the old net from the scene
                        del netItem
                        self.scene().schematicWindow.messageLine.setText("Merged Nets")
        except Exception as e:
            print(e)

    def findConnections(self):
        sceneNetItems = {item for item in self.scene().items() if isinstance(item,
                                                                             schematicNet)}
        sceneNetItems -= {self}  # remove self from the set
        startStartSet = set()  # set of nets whose start point is connected to self.start
        startEndSet = set()  # set of nets whose end point is connected to self.start
        endStartSet = set()  # set of nets whose start point is connected to self.end
        endEndSet = set()
        for netItem in sceneNetItems:
            if self.start == self.mapFromItem(netItem,netItem.start).toPoint():
                startStartSet.add(netItem)
            elif self.end == self.mapFromItem(netItem,netItem.start).toPoint():
                endStartSet.add(netItem)
            elif self.start == self.mapFromItem(netItem,netItem.end).toPoint():
                startEndSet.add(netItem)
            elif self.end == self.mapFromItem(netItem,netItem.end).toPoint():
                endEndSet.add(netItem)

        self._connections["startStart"] = startStartSet
        self._connections["startEnd"] = startEndSet
        self._connections["endStart"] = endStartSet
        self._connections["endEnd"] = endEndSet

    @property
    def connections(self):
        self.findConnections()
        return self._connections

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            print('net mouse press event')
            self.setSelected(True)
            self.mergeNets()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        # for netItem in self._connections["startStart"]:
        #     start = netItem.mapFromItem(self, self.start)
        #     end = netItem.end
        # for netItem in self._connections["startEnd"]:
        #     end = netItem.mapFromItem(self, self.start)
        #     start = netItem.start
        # for netItem in self._connections["endStart"]:
        #     start = netItem.mapFromItem(self, self.end)
        #     end = netItem.end
        # for netItem in self._connections["endEnd"]:
        #     start = netItem.start
        #     netItem.end = netItem.mapFromItem(self, self.end)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # self.mergeNets()
        for value in self._createdNets.values():
            self.scene().pruneWires(value.newNets, self.scene().wirePen)
        self._createdNets = dict()

        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            gridTuple = self.scene().gridTuple
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / gridTuple[0]) * gridTuple[0])
            newPos.setY(round(newPos.y() / gridTuple[1]) * gridTuple[1])

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
        elif change == QGraphicsItem.ItemSelectedHasChanged and self.scene():
            if value:
                self.findConnections()
                if self._connections["startStart"]:
                    for netItem in self._connections["startStart"]:
                        self._createdNets[netItem] = ddef.netsEndTuple(
                            self.scene().addWires( netItem.mapToScene(
                                netItem.start), self.scene().wirePen),
                            'startStart')
                if self._connections["startEnd"]:
                    for netItem in self._connections["startEnd"]:
                        self._createdNets[netItem] = ddef.netsEndTuple(
                            self.scene().addWires(netItem.mapToScene(
                                netItem.end), self.scene().wirePen), 'startEnd')
                if self._connections["endStart"]:
                    for netItem in self._connections["endStart"]:
                        self._createdNets[netItem] = ddef.netsEndTuple(self.scene(
                        ).addWires(netItem.mapToScene(netItem.start),
                                   self.scene().wirePen), 'endStart')
                if self._connections["endEnd"]:
                    for netItem in self._connections["endEnd"]:
                        self._createdNets[netItem] = ddef.netsEndTuple(self.scene(
                        ).addWires(netItem.mapToScene(netItem.end), self.scene(
                        ).wirePen),  'endEnd')
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            if self._createdNets:
                for netItem, tupleItem in self._createdNets.items():
                    if tupleItem.selfEnd == 'startStart':
                        self.scene().extendWires(self._createdNets[
                                                     netItem].newNets, netItem.start,
                                                 self.mapToScene(self.start))
                    elif tupleItem.selfEnd == 'startEnd':
                        self.scene().extendWires(self._createdNets[
                                                     netItem].newNets, netItem.end,
                                                 self.mapToScene(self.start))
                    elif tupleItem.selfEnd == 'endStart':
                        self.scene().extendWires(self._createdNets[
                                                     netItem].newNets, netItem.start,
                                                 self.mapToScene(self.end))
                    elif tupleItem.selfEnd == 'endEnd':
                        self.scene().extendWires(self._createdNets[
                                                     netItem].newNets,netItem.end,
                                                 self.mapToScene(self.end))

        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())


class crossingDot(QGraphicsEllipseItem):
    def __init__(self, point: QPoint, radius: int, pen: QPen):
        self.radius = radius
        self._pen = pen
        self.point = point
        super().__init__(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius)
        self.setPen(pen)
        self.setBrush(pen.color())

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
            painter.setBrush(Qt.white)
        else:
            painter.setPen(self._pen)
            painter.setBrush(self._pen.color())
        painter.drawEllipse(self.point, self.radius, self.radius)
