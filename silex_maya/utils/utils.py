import asyncio
import maya.utils as utils
from typing import Callable
from silex_client.utils.log import logger
from concurrent import futures


class Utils:
    @staticmethod
    async def wrapped_execute(action_query, maya_function: Callable, *args, **kwargs):

        future = action_query.event_loop.loop.create_future()

        def wrapped_function():
            result = maya_function(*args, **kwargs)
            future.set_result(result)
            # TODO: Figure out why when we remove this log, the future takes ages to get set
            logger.debug("Wrapped function executed %s", maya_function)

        utils.executeDeferred(wrapped_function)

        def callback(task_result: futures.Future):
            if task_result.cancelled():
                return

            exception = task_result.exception()
            if exception:
                logger.error("Exception raised %s", exception)

        future.add_done_callback(callback)
        await asyncio.wait_for(future, None)
        return future
