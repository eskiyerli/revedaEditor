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
import revedaEditor.gui.editFunctions as edf
import pdk.pcells as pcl
import inspect
import importlib
import revedaEditor.gui.lsw as lsw
import pdk.layoutLayers as laylyr
import revedaEditor.common.layoutShapes as lshp
from PySide6.QtGui import (QStandardItemModel, QStandardItem)
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QVBoxLayout, QRadioButton, QButtonGroup,
                               QPushButton, QGroupBox, QTableView, QMenu,
                               QCheckBox)


class pcellInstanceDialog(QDialog):
    def __init__(self, parent, item:lshp.pcell):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("PCell Instance Options")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vLayout = QVBoxLayout()
        instanceParamsGroup = QGroupBox("Instance Parameters")
        instanceParamsLayout = QFormLayout()
        instanceParamsGroup.setLayout(instanceParamsLayout)
        if item.__class__.__bases__[0] == shp.pcell:
            self.pcellLibName = edf.shortLineEdit()
            self.pcellLibName.setReadOnly(True)
            self.pcellLibName.setText(item.libraryName)
            instanceParamsLayout.addRow("PCell Library:", self.pcellLibName)
            self.pcellCellName = edf.shortLineEdit()
            self.pcellCellName.setReadOnly(True)
            self.pcellCellName.setText(item.cellName)
            instanceParamsLayout.addRow("PCell Cell:", self.pcellCellName)
            self.pcellName = edf.shortLineEdit()
            self.pcellName.setReadOnly(True)
            self.pcellName.setText(item.viewName)
            instanceParamsLayout.addRow("PCell Name:", self.pcellName)
            initArgs = inspect.signature(item.__class__.__init__).parameters
            argsUsed = [param for param in initArgs if (param != 'self' and
                                                          param != 'gridTuple')]
            argDict = {arg: getattr(item, arg) for arg in argsUsed}
            self.lineEditDict = {key:edf.shortLineEdit(value) for key, value in argDict.items()}
            for key, value in self.lineEditDict.items():
                instanceParamsLayout.addRow(key, value)
        vLayout.addWidget(instanceParamsGroup)

        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)
        self.show()

class pcellSettingDialogue(QDialog):
    def __init__(self,parent,viewItem: QStandardItem, module: str):
        super().__init__(parent)
        # self.logger = parent.logger
        self.viewItem = viewItem
        self.module = module
        self.setWindowTitle('PCell Settings')
        self.setMinimumSize(600,300)
        self.mainLayout = QVBoxLayout()
        groupBox = QGroupBox()
        formLayout = QFormLayout()
        groupBox.setLayout(formLayout)
        pcells = self.getClasses(self.module)
        self.pcellCB = QComboBox()
        self.pcellCB.addItems(pcells)
        formLayout.addRow(edf.boldLabel("PCell:"), self.pcellCB)
        self.mainLayout.addWidget(groupBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


    @staticmethod
    def getClasses(module_name):
        module = importlib.import_module(module_name)
        classes = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                classes.append(name)
        return classes

class pathSettingsDialogue(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Create Path')
        self.setMinimumSize(400,200)
        mainLayout = QVBoxLayout()
        pathOrientBox = QGroupBox('Path Orientation')
        horizontalLayout = QHBoxLayout(pathOrientBox)
        pathOrientBox.setLayout(horizontalLayout)
        pathOrientGroup = QButtonGroup()

        self.manhattanButton = QRadioButton('Manhattan')
        pathOrientGroup.addButton(self.manhattanButton)
        horizontalLayout.addWidget(self.manhattanButton)
        self.diagonalButton = QRadioButton('Diagonal')
        pathOrientGroup.addButton(self.diagonalButton)
        horizontalLayout.addWidget(self.diagonalButton)
        self.anyButton = QRadioButton('Any')
        pathOrientGroup.addButton(self.anyButton)
        horizontalLayout.addWidget(self.anyButton)
        self.horizontalButton = QRadioButton('Horizontal')
        pathOrientGroup.addButton(self.horizontalButton)
        horizontalLayout.addWidget(self.horizontalButton)
        self.verticalButton = QRadioButton('Vertical')
        pathOrientGroup.addButton(self.verticalButton)
        horizontalLayout.addWidget(self.verticalButton)
        self.manhattanButton.setChecked(True)
        pathOrientGroup.setExclusive(True)
        mainLayout.addWidget(pathOrientBox)
        groupBox = QGroupBox()
        formLayout = QFormLayout()
        groupBox.setLayout(formLayout)
        self.pathWidth = edf.shortLineEdit()
        formLayout.addRow(edf.boldLabel("Path Width:"), self.pathWidth)
        self.pathName = edf.shortLineEdit()
        formLayout.addRow(edf.boldLabel("Path Name:"), self.pathName)
        mainLayout.addWidget(groupBox)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()

