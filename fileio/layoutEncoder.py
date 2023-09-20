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
import json
import inspect
import pdk.layoutLayers as laylyr
import revedaEditor.common.layoutShapes as lshp


class layoutEncoder(json.JSONEncoder):
    def default(self, item):
        match type(item):
            case lshp.layoutInstance:
                itemDict = {"type": "layoutInstance", "lib": item.libraryName, "cell":
                            item.cellName,
                            "view": item.viewName, "nam": item.instanceName,
                            "ic": item.counter,
                            "loc": (item.scenePos() - item.scene().origin).toTuple(),
                            "ang": item.angle, }
            case lshp.layoutRect:
                itemDict = {"type": "layoutRect", "rect": item.rect.getCoords(),
                            "loc": (item.scenePos() - item.scene().origin).toTuple(),
                            "ang": item.angle,
                            "lnum": laylyr.pdkDrawingLayers.index(item.layer)}
            case lshp.layoutPath:
                itemDict = {"type": "layoutPath"}
            case default: # now check super class types:
                match item.__class__.__bases__[0]:
                    case lshp.pcell:
                        init_args = inspect.signature(item.__class__.__init__).parameters
                        args_used = [param for param in init_args if (param != 'self' and
                                                                    param != 'gridTuple')]

                        argDict = {arg: getattr(item, arg) for arg in args_used}
                        # print(argDict)
                        itemDict = {"type": "pcell", "lib": item.libraryName, "cell": item.cellName,
                                    "view": item.viewName, "nam": item.instanceName, "ic": item.counter,
                                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                                    "ang": item.angle, "params": argDict}


        return itemDict



