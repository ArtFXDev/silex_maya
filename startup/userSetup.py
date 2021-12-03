from silex_client.core.context import Context
import maya

from custom_save import custom_save
from create_shelf import create_shelf


Context.get().start_services()
maya.utils.executeDeferred(create_shelf)
maya.utils.executeDeferred(custom_save)

