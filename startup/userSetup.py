import maya
from create_shelf import create_shelf
from custom_save import custom_save
from load_plugins import load_plugins
from silex_client.core.context import Context

Context.get().start_services()
maya.utils.executeDeferred(create_shelf)
maya.utils.executeDeferred(custom_save)
maya.utils.executeDeferred(load_plugins)
