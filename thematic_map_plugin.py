from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject
import os.path

from .thematic_map_dialog import ThematicMapDialog


class ThematicMapPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr('&Thematic Map')
        
    def tr(self, message):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate('ThematicMapPlugin', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icons', 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr('Create Thematic Map'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip=self.tr('Generate thematic/choropleth map'),
            whats_this=self.tr('Create a thematic map using graduated colors based on numeric field values')
        )
        
    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if len(QgsProject.instance().mapLayers()) == 0:
            self.iface.messageBar().pushWarning(
                "Warning", 
                "No layers loaded! Please load a vector layer first."
            )
            return
            
        dlg = ThematicMapDialog(self.iface)
        dlg.exec_()