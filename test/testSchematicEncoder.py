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

import unittest
import revedaEditor.common.net as net
import revedaEditor.common.shape as shp
class TestDefault(unittest.TestCase):

    def test_symbolShape(self):
        # Testing for symbolShape object
        item = shp.schematicSymbol()
        itemDict = self.default(item)
        self.assertEqual(itemDict["type"], "symbolShape")

    def test_schematicNet(self):
        # Testing for schematicNet object
        item = net.schematicNet()
        itemDict = self.default(item)
        self.assertEqual(itemDict["type"], "schematicNet")

    def test_schematicPin(self):
        # Testing for schematicPin object
        item = shp.schematicPin()
        itemDict = self.default(item)
        self.assertEqual(itemDict["type"], "schematicPin")

    def test_text(self):
        # Testing for text object
        item = shp.text()
        itemDict = self.default(item)
        self.assertEqual(itemDict["type"], "text")

if __name__ == '__main__':
    unittest.main()