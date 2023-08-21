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
import importlib
import inspect

from PySide6.QtGui import (QStandardItem, QFontDatabase)
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit,
                               QVBoxLayout, QRadioButton, QButtonGroup,
                               QGroupBox)
import revedaEditor.common.layoutShapes as lshp
import revedaEditor.gui.editFunctions as edf


class pcellInstanceDialog(QDialog):
    def __init__(self, parent, item: lshp.pcell):
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
            self.lineEditDict = {key: edf.shortLineEdit(value) for key, value in
                                 argDict.items()}
            for key, value in self.lineEditDict.items():
                instanceParamsLayout.addRow(key, value)
        vLayout.addWidget(instanceParamsGroup)

        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)
        self.show()


class pcellSettingDialogue(QDialog):
    def __init__(self, parent, viewItem: QStandardItem, module: str):
        super().__init__(parent)
        # self.logger = parent.logger
        self.viewItem = viewItem
        self.module = module
        self.setWindowTitle('PCell Settings')
        self.setMinimumSize(600, 300)
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
        self.setMinimumSize(400, 200)
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


class createLayoutPinDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Layout Pin")
        self.setMinimumWidth(300)
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [family for family in fontFamilies if
                         QFontDatabase.isFixedPitch(family)]
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.pinPropGroupBox = QGroupBox('Pin Properties')
        fLayout = QFormLayout()
        self.pinPropGroupBox.setLayout(fLayout)
        self.pinName = QLineEdit()
        self.pinName.setPlaceholderText("Pin Name")
        self.pinName.setToolTip("Enter pin name")
        fLayout.addRow(edf.boldLabel("Pin Name"), self.pinName)
        self.pinDir = QComboBox()
        self.pinDir.addItems(lshp.layoutPin.pinDirs)
        self.pinDir.setToolTip("Select pin direction")
        fLayout.addRow(edf.boldLabel("Pin Direction"), self.pinDir)
        self.pinType = QComboBox()
        self.pinType.addItems(lshp.layoutPin.pinTypes)
        self.pinType.setToolTip("Select pin type")
        fLayout.addRow(edf.boldLabel("Pin Type"), self.pinType)
        self.mainLayout.addWidget(self.pinPropGroupBox)
        self.layerSelectGroupBox = QGroupBox('Select layers')
        layerFormLayout = QFormLayout()
        self.layerSelectGroupBox.setLayout(layerFormLayout)
        self.pinLayerCB = QComboBox()
        layerFormLayout.addRow(edf.boldLabel('Pin Layer:'), self.pinLayerCB)
        self.labelLayerCB = QComboBox()
        layerFormLayout.addRow(edf.boldLabel('Label Layer:'), self.labelLayerCB)
        self.mainLayout.addWidget(self.layerSelectGroupBox)
        labelPropBox = QGroupBox('Label Properties')
        labelPropLayout = QFormLayout()
        labelPropBox.setLayout(labelPropLayout)
        self.familyCB = QComboBox()
        self.familyCB.addItems(fixedFamilies)
        self.familyCB.currentTextChanged.connect(self.familyFontStyles)
        labelPropLayout.addRow(edf.boldLabel('Font Name'),self.familyCB)
        self.fontStyleCB = QComboBox()
        self.fontStyles = QFontDatabase.styles(fixedFamilies[0])
        self.fontStyleCB.addItems(self.fontStyles)
        self.fontStyleCB.currentTextChanged.connect(self.styleFontSizes)
        labelPropLayout.addRow(edf.boldLabel('Font Style'), self.fontStyleCB)
        self.labelHeightCB = QComboBox()
        self.fontSizes = [str(size) for size in QFontDatabase.pointSizes(fixedFamilies[0],
                                                          self.fontStyles[0])]
        self.labelHeightCB.addItems(self.fontSizes)
        labelPropLayout.addRow(edf.boldLabel('Label Height'),self.labelHeightCB)
        self.labelAlignCB = QComboBox()
        self.labelAlignCB.addItems(lshp.layoutLabel.labelAlignments)
        labelPropLayout.addRow(QLabel("Label Alignment"), self.labelAlignCB)
        self.labelOrientCB = QComboBox()
        self.labelOrientCB.addItems(lshp.layoutLabel.labelOrients)
        labelPropLayout.addRow(QLabel("Label Orientation"), self.labelOrientCB)
        self.mainLayout.addWidget(labelPropBox)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

    def familyFontStyles(self,s):
        self.fontStyleCB.clear()
        self.fontStyles = QFontDatabase.styles(self.familyCB.currentText())
        self.fontStyleCB.addItems(self.fontStyles)

    def styleFontSizes(self,s):
        self.labelHeightCB.clear()
        selectedFamily = self.familyCB.currentText()
        selectedStyle = self.fontStyleCB.currentText()
        self.fontSizes = [str(size) for size in QFontDatabase.pointSizes(
            selectedFamily, selectedStyle)]
        self.labelHeightCB.addItems(self.fontSizes)

class createLayoutLabelDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Layout Label")
        self.setMinimumWidth(300)
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [family for family in fontFamilies if
                         QFontDatabase.isFixedPitch(family)]
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        labelPropBox = QGroupBox('Label Properties')
        labelPropLayout = QFormLayout()
        labelPropBox.setLayout(labelPropLayout)
        self.labelName = QLineEdit()
        self.labelName.setPlaceholderText("Label Name")
        self.labelName.setToolTip("Enter label name")
        labelPropLayout.addRow(edf.boldLabel("Label Name"), self.labelName)
        self.labelLayerCB = QComboBox()
        labelPropLayout.addRow(edf.boldLabel('Label Layer:'), self.labelLayerCB)
        self.familyCB = QComboBox()
        self.familyCB.addItems(fixedFamilies)
        self.familyCB.currentTextChanged.connect(self.familyFontStyles)
        labelPropLayout.addRow(edf.boldLabel('Font Name'),self.familyCB)
        self.fontStyleCB = QComboBox()
        self.fontStyles = QFontDatabase.styles(fixedFamilies[0])
        self.fontStyleCB.addItems(self.fontStyles)
        self.fontStyleCB.currentTextChanged.connect(self.styleFontSizes)
        labelPropLayout.addRow(edf.boldLabel('Font Style'), self.fontStyleCB)
        self.labelHeightCB = QComboBox()
        self.fontSizes = [str(size) for size in QFontDatabase.pointSizes(fixedFamilies[0],
                                                          self.fontStyles[0])]
        self.labelHeightCB.addItems(self.fontSizes)
        labelPropLayout.addRow(edf.boldLabel('Label Height'),self.labelHeightCB)
        self.labelAlignCB = QComboBox()
        self.labelAlignCB.addItems(lshp.layoutLabel.labelAlignments)
        labelPropLayout.addRow(QLabel("Label Alignment"), self.labelAlignCB)
        self.labelOrientCB = QComboBox()
        self.labelOrientCB.addItems(lshp.layoutLabel.labelOrients)
        labelPropLayout.addRow(QLabel("Label Orientation"), self.labelOrientCB)
        self.mainLayout.addWidget(labelPropBox)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

    def familyFontStyles(self,s):
        self.fontStyleCB.clear()
        self.fontStyles = QFontDatabase.styles(self.familyCB.currentText())
        self.fontStyleCB.addItems(self.fontStyles)

    def styleFontSizes(self,s):
        self.labelHeightCB.clear()
        selectedFamily = self.familyCB.currentText()
        selectedStyle = self.fontStyleCB.currentText()
        self.fontSizes = [str(size) for size in QFontDatabase.pointSizes(
            selectedFamily, selectedStyle)]
        self.labelHeightCB.addItems(self.fontSizes)
