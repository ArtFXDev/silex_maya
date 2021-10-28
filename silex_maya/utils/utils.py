import maya.utils as utils
from typing import Callable
from silex_client.utils.log import logger
from concurrent import futures
import typing

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery  # todo


class Utils:
    @staticmethod
    async def wrapped_execute(action_query, maya_function: Callable, *args, **kwargs):

        future = action_query.event_loop.loop.create_future()

        def wrapped_function():
            result = maya_function(*args, **kwargs)
            future.set_result(result)

        utils.executeDeferred(wrapped_function)

        def callback(task_result: futures.Future):
            if task_result.cancelled():
                return

            exception = task_result.exception()
            if exception:
                logger.error("Exception raised %s", exception)

        future.add_done_callback(callback)
        return future

    @staticmethod
    async def log(self, action_query, info):
        await self.wrapped_execute(action_query, lambda: print(info))
