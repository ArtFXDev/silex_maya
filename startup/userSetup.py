from silex_client.core.context import Context
from maya import cmds

Context.get().event_loop.start()
Context.get().ws_connection.start()
