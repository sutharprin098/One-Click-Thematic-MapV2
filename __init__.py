def classFactory(iface):
    from .thematic_map_plugin import ThematicMapPlugin
    return ThematicMapPlugin(iface)