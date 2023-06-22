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
from PySide6.QtCore import (Qt, QDir)
from PySide6.QtGui import (QStandardItemModel, QStandardItem)
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QVBoxLayout, QRadioButton, QButtonGroup,
                               QPushButton, QGroupBox, QTableView, QMenu,
                               QCheckBox)

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
        pcellCB = QComboBox()
        pcellCB.addItems(pcells)
        formLayout.addRow(edf.boldLabel("PCell:"), pcellCB)
        self.mainLayout.addWidget(groupBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)


    @staticmethod
    def getClasses(module_name):
        module = importlib.import_module(module_name)
        classes = []
        for name, obj in inspect.getmembers(module):
            print(name)
            if inspect.isclass(obj):
                classes.append(name)
        return classes