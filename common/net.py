
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
from PySide6.QtCore import (QPoint, Qt, QLineF, QRectF, QPointF, QRect)
from PySide6.QtGui import (QPen, QStaticText,)
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem,
                               QGraphicsEllipseItem, QGraphicsRectItem,
                               QGraphicsSceneMouseEvent)
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
        # self._createdNets = dict()
        self._endPoints = [self._start, self._end]
        self._dots = set()
        self._dotPoints = set()
        self._touchingNets = set()
        self._endsNetsTupleList = list()
        self._newWires = list()

    def __repr__(self):
        return f"schematicNet(start={self.mapToScene(self._start)}, " \
               f"end={self.mapToScene(self._end)}"


    def paint(self, painter, option, widget) -> None:

        painter.setPen(self._pen)
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        if self.name is not None:
            # textLoc = self.line().p1()
            if self._nameConflict:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            if self._horizontal:
                # if there is name conflict, draw the line and name in red.
                textLoc = QPoint(0.5*(self.line().p1().x()+self.line().p2().x()),self.line(
                ).p1().y())
            elif not self._horizontal:
                textLoc = QPoint(self.line().p1().x(),0.5*(self.line().p1().y()+self.line(
                ).p2().y()))
            painter.drawStaticText(textLoc, QStaticText(self.name))

        painter.drawLine(self.line())


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
        return self.line().p1()
        # return self._start

    @start.setter
    def start(self, start: QPoint):

        self._start = start
        # self.line().setP1(start)
        self.setLine(QLineF(self._start, self._end))

    @property
    def end(self):
        return self.line().p2()
        # return self._end

    @end.setter
    def end(self, end: QPoint):
        self._end = end
        # self.line().setP2(end)
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
        if name != "": # net name should not be an empty string
            self._name = name
            self.nameSet = True

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

    @property
    def endPoints(self):
        return self._endPoints

    @endPoints.setter
    def endPoints(self, endPoints: list):
        assert isinstance(endPoints, list)
        self._start = endPoints[0]
        self._end = endPoints[1]
        self.setLine(QLineF(self._start, self._end))
        self._endPoints = endPoints


    def whichEnd(self,endPoint: QPoint):
        if endPoint == self.start.toPoint():
            return 'start'
        elif endPoint == self.end.toPoint():
            return 'end'
        else:
            return None

    @property
    def horizontal(self):
        if self.line().dy() == 0:
            self._horizontal = True
        elif self.line().dx() == 0:
            self._horizontal = False
        else:
            self._horizontal = False
        return self._horizontal

    @property
    def dots(self):
        return self._dots

    @property
    def dotPoints(self):
        return self._dotPoints

    def findDotPoints(self):
        '''
        Find all the dot points on the net.
        '''

        try:
            sceneNetsSet = self.scene().findSceneNetsSet()
            horizontalNetsInView = {item for item in sceneNetsSet if
                                    item.horizontal}

            verticalNetsInView = {item for item in sceneNetsSet if
                                    not item.horizontal}
            sceneSelfP1 = self.mapToScene(self.line().p1())
            sceneSelfP2 = self.mapToScene(self.line().p2())

            [self.scene().removeItem(dot) for dot in self._dots]
            self._dots.clear()
            self._dotPoints.clear()
            self._touchingNets.clear()

            if self.horizontal:
                for netItem in verticalNetsInView:
                    sceneNetItemP1 = netItem.mapToScene(netItem.line().p1())
                    sceneNetItemP2 = netItem.mapToScene(netItem.line().p2())

                    self.horEndAtVert(sceneNetItemP1, sceneNetItemP2,
                                      sceneSelfP1, sceneSelfP2, netItem)
                    self.vertEndAtHor(sceneSelfP1,sceneSelfP2, sceneNetItemP1,
                                      sceneNetItemP2, netItem)


            elif not self.horizontal:
                for netItem in horizontalNetsInView:
                    sceneNetItemP1 = netItem.mapToScene(netItem.line().p1())
                    sceneNetItemP2 = netItem.mapToScene(netItem.line().p2())
                    self.vertEndAtHor(sceneNetItemP1, sceneNetItemP2,
                                      sceneSelfP1, sceneSelfP2,netItem)
                    self.horEndAtVert(sceneSelfP1, sceneSelfP2, sceneNetItemP1,
                                      sceneNetItemP2,netItem)

            [self._dots.add(crossingDot(dotPoint,3,self.scene().wirePen)) for dotPoint in
             self._dotPoints]
            [self.scene().addItem(dot) for dot in self._dots]

        except Exception as e:
            print(f'add dot error: {e}')

    def vertEndAtHor(self, horNetSceneP1, horNetSceneP2, vertNetSceneP1,
                     vertNetSceneP2,netItem):
        '''
        Calculate point where vertical net ends at horizontal net
        '''
        if min(horNetSceneP1.x(), horNetSceneP2.x()) < vertNetSceneP1.x() < max(
                horNetSceneP1.x(), horNetSceneP2.x()):
            if vertNetSceneP1.y() == horNetSceneP1.y():
                self._dotPoints.add(vertNetSceneP1.toPoint())
                self._touchingNets.add(netItem)
                # netItem.dotPoints.add(vertNetSceneP1.toPoint())
            elif vertNetSceneP2.y() == horNetSceneP1.y():
                self._dotPoints.add(vertNetSceneP2.toPoint())
                # netItem.dotPoints.add(vertNetSceneP2.toPoint())
                self._touchingNets.add(netItem)

    def horEndAtVert(self, vertNetSceneP1, vertNetSceneP2, horNetSceneP1,
                     horNetSceneP2,netItem):

        '''
        Calculate point where horizontal net ends at vertical net
        '''
        if min(vertNetSceneP1.y(), vertNetSceneP2.y()) < horNetSceneP1.y() < max(
                vertNetSceneP1.y(), vertNetSceneP2.y()):
            if horNetSceneP1.x() == vertNetSceneP1.x():
                self._dotPoints.add(horNetSceneP1.toPoint())
                self._touchingNets.add(netItem)
                # netItem.dotPoints.add(horNetSceneP1.toPoint())
            elif horNetSceneP2.x() == vertNetSceneP1.x():
                self._dotPoints.add(horNetSceneP2.toPoint())
                self._touchingNets.add(netItem)
                # netItem.dotPoints.add(horNetSceneP2.toPoint())

    def splitNets(self):
        '''
        If a net ends on another net of different orientation (horizontal vs vertical)
        divide that net in to two. Does not work well.
        '''
        try:
            horizontalNetsInView = {item for item in self.scene().parent.view.viewNetItemsSet if
                                    item.horizontal}

            verticalNetsInView = {item for item in self.scene().parent.view.viewNetItemsSet if
                                    not item.horizontal }
            sceneSelfP1 = self.mapToScene(self.line().p1())
            sceneSelfP2 = self.mapToScene(self.line().p2())
            if self.horizontal:
                for netItem in verticalNetsInView:
                    sceneNetItemP1 = netItem.mapToScene(netItem.line().p1())
                    sceneNetItemP2 = netItem.mapToScene(netItem.line().p2())
                    if min(sceneNetItemP1.y(),sceneNetItemP2.y()) < sceneSelfP1.y()< max(
                            sceneNetItemP1.y(),sceneNetItemP2.y()):
                        if sceneSelfP1.x() == sceneNetItemP1.x():

                            netItem.setLine(QLineF(sceneSelfP1,sceneNetItemP1))
                            newNetItem = schematicNet(sceneSelfP1,sceneNetItemP2,
                                                      self.scene().wirePen)
                            self.scene().addItem(newNetItem)
                            return self.line().p1()
                        elif sceneSelfP2.x() == sceneNetItemP1.x():

                            netItem.setLine(QLineF(sceneSelfP2,sceneNetItemP1))
                            newNetItem = schematicNet(sceneSelfP2, sceneNetItemP2,
                                                      self.scene().wirePen)
                            self.scene().addItem(newNetItem)
                            return self.line().p2()
            elif not self.horizontal:
                for netItem in horizontalNetsInView:
                    sceneNetItemP1 = netItem.mapToScene(netItem.line().p1())
                    sceneNetItemP2 = netItem.mapToScene(netItem.line().p2())
                    if min(sceneNetItemP1.x(), sceneNetItemP2.x()) < sceneSelfP1.x()< max(
                            sceneNetItemP1.x(), sceneNetItemP2.x()):
                        if sceneSelfP1.y() == sceneNetItemP1.y():

                            netItem.setLine(QLineF(sceneSelfP1,sceneNetItemP1))
                            newNetItem = schematicNet(sceneSelfP1,sceneNetItemP2,
                                                      self.scene().wirePen)
                            self.scene().addItem(newNetItem)
                            return self.line().p1()
                        elif sceneSelfP2.y() == sceneNetItemP1.y():

                            netItem.setLine(QLineF(sceneSelfP2,sceneNetItemP1))
                            newNetItem = schematicNet(sceneSelfP2, sceneNetItemP2,
                                                      self.scene().wirePen)
                            self.scene().addItem(newNetItem)
                            return self.line().p2()
        except Exception as e:
            print(f'split nets Error: {e}')


    def mergeNets(self,) -> None:
        # check any overlapping nets in the view
        # editing is done in the view and thus there is no need to check all nets in the scene
        try:
            netsInView = {item for item in self.scene().parent.view.items() if
                          isinstance(item,schematicNet) and item is not self}
            horizontalNetsInView = {item for item in netsInView if
                                    item.horizontal}

            verticalNetsInView = {item for item in netsInView if
                                    not item.horizontal}

            dBNetRect = self.sceneBoundingRect()
            if self.horizontal and horizontalNetsInView is not None:
                for netItem in horizontalNetsInView :
                    netItemBRect = netItem.sceneBoundingRect()
                    if dBNetRect.intersects(netItemBRect):
                        newXstart = max([self.start.x(), self.end.x(),
                                         netItem.start.x(),
                                        netItem.end.x()])
                        newXend = min([self.start.x(), self.end.x(),
                                     netItem.start.x(),
                                        netItem.end.x()])
                        self.start = QPoint(newXstart, self.start.y())
                        self.end = QPoint(newXend, self.end.y())
                        self.scene().removeItem(netItem)  # remove the old net from the scene
                        del netItem
                        self.scene().schematicWindow.messageLine.setText("Merged Nets")
            elif not self.horizontal and verticalNetsInView is not None:
                for netItem in verticalNetsInView - {self, }:
                    netItemBRect = netItem.sceneBoundingRect()
                    if dBNetRect.intersects(netItemBRect):
                        newYstart = max([self.start.y(), self.end.y(),
                                       netItem.start.y(),
                                        netItem.end.y()])
                        newYend = min([self.start.y(), self.end.y(),
                                     netItem.start.y(),
                                        netItem.end.y()])
                        self.start = QPoint(self.start.x(), newYstart)
                        self.end = QPoint(self.end.x(), newYend)
                        self.scene().removeItem(netItem)  # remove the old net from the scene
                        del netItem
                        self.scene().schematicWindow.messageLine.setText("Merged Nets")
        except Exception as e:
            self.scene().logger.error(f'Error in net.mergeNets: {e}')

    def findConnections(self):
        self._endsNetsTupleList = list()
        sceneNetItems = {item for item in self.scene().items() if
                         isinstance(item,schematicNet) and item is not self}
        for netItem in sceneNetItems:
            for endPoint in netItem.endPoints:
                for selfEndPoint in self.endPoints:
                    if (netItem.mapToScene(endPoint).toPoint() ==
                            self.mapToScene(selfEndPoint).toPoint()):
                        self._endsNetsTupleList.append(ddef.netEndTuple(self,
                        self.mapToScene(selfEndPoint),netItem,
                        netItem.mapToScene(endPoint)))


    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        super().mousePressEvent(event)

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            gridTuple = self.scene().gridTuple
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / gridTuple[0]) * gridTuple[0])
            newPos.setY(round(newPos.y() / gridTuple[1]) * gridTuple[1])


            for netItem in self._touchingNets:
                netItem.findDotPoints()

            self.mergeNets()
            self.findDotPoints()
            self.splitNets()

            # Keep the item inside the view rect.
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

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:



        for netItem in self._touchingNets:
            netItem.findDotPoints()
        self.findDotPoints()
        self.mergeNets()
        self.splitNets()
        super().mouseReleaseEvent(event)

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

class snapPointRect(QGraphicsRectItem):
    def __init__(self, centre:QPoint, width:int, pen: QPen):
        self._centre = centre
        self._width = width
        self._pen = pen
        snapRect = QRectF(QPointF(centre.x()-width*0.5, centre.y()-0.5*width), QPointF(
            centre.x()+width*0.5,centre.y()+width*0.5))

        super().__init__(snapRect)
        self.setRotation(90)

    def paint(self,painter,option,widget) -> None:
        painter.setPen(self._pen)
        painter.drawRect(self.rect)
