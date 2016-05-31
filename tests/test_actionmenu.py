import sys
import pyblish.api

from Qt import QtWidgets

from pyblish_lite import view, app


class ContextAction(pyblish.api.Action):
    label = "Context action"
    icon = u"\uf126"

    def process(self, context):
        self.log.info("I have access to the context")

qapp = QtWidgets.QApplication(sys.argv)

with app.stylesheet() as css:
    qapp.setStyleSheet(css)

actions = view.ActionMenu(actions=[
    ContextAction,
    pyblish.api.Category("My Category")
])

actions.exec_()
