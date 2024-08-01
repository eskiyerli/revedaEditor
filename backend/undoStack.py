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


from PySide6.QtCore import QPoint
from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from typing import List, Tuple

class undoStack(QUndoStack):
    def __init__(self):
        super().__init__()

    def removeLastCommand(self):
        # Remove the last command without undoing it
        if self.canUndo():
            self.setIndex(self.index() - 1)


class addShapeUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shape: QGraphicsItem):
        super().__init__()
        self._scene = scene
        self._shape = shape
        self.setText("Draw Shape")

    def undo(self):
        self._scene.removeItem(self._shape)

    def redo(self):
        self._scene.addItem(self._shape)


class addShapesUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shapes: List[QGraphicsItem]):
        super().__init__()
        self._scene = scene
        self._shapes = shapes
        self.setText("Add Shapes")

    def undo(self):
        [self._scene.removeItem(item) for item in self._shapes]

    def redo(self):
        [self._scene.addItem(item) for item in self._shapes]

class addDeleteShapesUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, newShapes: List[QGraphicsItem], oldShapes:
    List[QGraphicsItem]):
        super().__init__()
        self._scene = scene
        self._newShapes = newShapes
        self._oldShapes = oldShapes
        self.setText("Add/Delete Shapes")

    def undo(self):
        [self._scene.removeItem(item) for item in self._newShapes]
        [self._scene.addItem(item) for item in self._oldShapes]

    def redo(self):
        [self._scene.addItem(item) for item in self._newShapes]
        [self._scene.removeItem(item) for item in self._oldShapes]


class loadShapesUndo(addShapesUndo):
    """
    A hack to load the file but disallow the undo
    """

    def __init__(self, scene: QGraphicsScene, shapes: list[QGraphicsItem]):
        super().__init__(scene, shapes)

    def undo(self):
        pass


class deleteShapeUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shape: QGraphicsItem):
        super().__init__()
        self._scene = scene
        self._shape = shape
        self.setText("Delete Shape")

    def undo(self):
        self._scene.addItem(self._shape)

    def redo(self):
        self._scene.removeItem(self._shape)

class deleteShapesUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shapes: list[QGraphicsItem]):
        super().__init__()
        self._scene = scene
        self._shapes = shapes
        self.setText("Delete Shapes")

    def undo(self):
        [self._scene.addItem(item) for item in self._shapes]

    def redo(self):
        [self._scene.removeItem(item) for item in self._shapes]

class addDeleteShapeUndo(QUndoCommand):
    def __init__(
        self, scene: QGraphicsScene, addShape: QGraphicsItem, deleteShape: QGraphicsItem
    ):
        super().__init__()
        self._scene = scene
        self._addshape = addShape
        self._deleteShape = deleteShape
        self.setText("Add/Delete Shape")

    def undo(self):
        self._scene.removeItem(self._addshape)
        self._scene.addItem(self._deleteShape)

    def redo(self):
        self._scene.addItem(self._addshape)
        self._scene.removeItem(self._deleteShape)

class addDeleteNetUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, addNet: QGraphicsItem, deleteNet: QGraphicsItem):
        super().__init__()
        self._scene = scene
        self._addNet = addNet
        self._deleteNet = deleteNet
        self.setText("Add/Delete Net")

    def undo(self):
        self._scene.removeItem(self._addNet)
        self._scene.addItem(self._deleteNet)
        self._scene.findConnectedNetSet(self._deleteNet)

    def redo(self):
        self._scene.addItem(self._addNet)
        self._scene.removeItem(self._deleteNet)
        self._scene.findConnectedNetSet(self._addNet)

class updateSymUndo(QUndoCommand):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__()
        self._item = item
        self._oldItemList = oldItemList
        self._newItemList = newItemList

    def undo(self):
        pass

    def redo(self):
        pass


class moveShapeUndo(QUndoCommand):
    def __init__(
        self,
        scene,
        item: QGraphicsItem,
        attribute: str,
        oldPosition: QPoint,
        newPosition: QPoint,
    ):
        self._scene = scene
        self._item = item
        self._attribute = attribute
        self._oldPosition = oldPosition
        self._newPosition = newPosition

    def undo(self):
        setattr(self._item, self._attribute, self._oldPosition)

    def redo(self):
        setattr(self._item, self._attribute, self._newPosition)


class undoRotateShape(QUndoCommand):
    def __init__(self, scene, shape, angle, parent=None):
        super().__init__()
        self._scene = scene
        self._shape = shape
        self._angle = angle
        self.setText("Undo Shape rotation")

    def undo(self) -> None:
        self._shape.setRotation(self._angle - 90)

    def redo(self) -> None:
        # self.angle += 90
        self._shape.setRotation(self._angle)


class undoMoveShapesCommand(QUndoCommand):
    def __init__(self, shapes: list[QGraphicsItem], shapesOffsetList: list[int], startPos, endPos):
        super().__init__()
        self._shapes = shapes
        self._shapesOffsetList = shapesOffsetList
        self._startPos = startPos
        self._endPos = endPos


    def undo(self):
        for index, item in enumerate(self._shapes):
            item.setPos(self._startPos + self._shapesOffsetList[index])

    def redo(self):
        for index, item in enumerate(self._shapes):
            item.setPos(self._endPos + self._shapesOffsetList[index])

class undoMoveByCommand(QUndoCommand):
    def __init__(self, scene, items: List, dx: float, dy: float, description: str = "Move Items"):
        super().__init__(description)
        self.scene = scene
        self.items = items
        self.dx = dx
        self.dy = dy
        self.oldPositions: List[Tuple[QPoint, QPoint]] = []

    def redo(self):
        for item in self.items:
            oldPos = item.pos()
            newPos = oldPos + QPoint(self.dx, self.dy)
            self.oldPositions.append((item, oldPos))
            item.setPos(newPos)

    def undo(self):
        for item, oldPos in self.oldPositions:
            item.setPos(oldPos)