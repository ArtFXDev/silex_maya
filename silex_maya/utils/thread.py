from typing import Callable

from maya import utils
from silex_client.utils.thread import ExecutionInThread


class MayaExecutionInMainThread(ExecutionInThread):
    @staticmethod
    def execute_wrapped_function(wrapped_function: Callable):
        utils.executeDeferred(wrapped_function)


execute_in_main_thread = MayaExecutionInMainThread()
