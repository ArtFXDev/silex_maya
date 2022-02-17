from typing import Callable

from maya import utils, cmds

from silex_client.utils.thread import ExecutionInThread
from silex_client.core.context import Context


class MayaExecutionInMainThread(ExecutionInThread):
    @staticmethod
    def execute_wrapped_function(wrapped_function: Callable):
        # ExecuteDeferred cannot be called in mayapy
        if cmds.about(batch=True):
            Context.get().event_queue.put(wrapped_function)
        else:
            utils.executeDeferred(wrapped_function)


execute_in_main_thread = MayaExecutionInMainThread()
