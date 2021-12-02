from silex_client.core.context import Context
from silex_client.resolve.config import Config
import maya
import create_shelf, custom_save



Context.get().start_services()
maya.utils.executeDeferred(create_shelf.create_shelf)
maya.utils.executeDeferred(custom_save.custom_save)

