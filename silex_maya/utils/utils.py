import asyncio
import maya.utils as utils
from typing import Callable
from silex_client.utils.log import logger
from silex_client.core.context import Context
from concurrent import futures


class Utils:
    @staticmethod
    async def wrapped_execute(action_query, maya_function: Callable, *args, **kwargs):

        future = action_query.event_loop.loop.create_future()

        def wrapped_function():
            async def set_future_result(result):
                future.set_result(result)

            async def set_future_exception(exception):
                future.set_exception(exception)

            try:
                result = maya_function(*args, **kwargs)
                Context.get().event_loop.register_task(set_future_result(result))
            except Exception as ex:
                Context.get().event_loop.register_task(set_future_exception(ex))

        # This maya function execute the given function in the main thread
        utils.executeDeferred(wrapped_function)

        def callback(task_result: futures.Future):
            if task_result.cancelled():
                return

            exception = task_result.exception()
            if exception:
                logger.error("Exception raised in wrapped execute call: %s", exception)
                raise Exception(
                    f"Exception raised in wrapped execute call: {exception}"
                )

        future.add_done_callback(callback)
        await asyncio.wait_for(future, None)
        return future
