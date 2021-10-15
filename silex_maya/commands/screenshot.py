from __future__ import annotations
import typing
from typing import Any, Dict, List

import gazu.task

from silex_client.action.command_base import CommandBase, CommandParameters
from silex_client.utils.log import logger
from silex_maya.utils.utils import Utils
from silex_maya.utils.preview import create_thumbnail

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Screenshot(CommandBase):
    """
    Take a screenshot and upload it
    """

    parameters: CommandParameters = {
        "description": {"label": "Description", "type": str, "value": None},
        "status": {"label": "Task Status", "type": str, "value": "wfa"},
    }

    required_metadata: List[str] = ["task_id"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Take a thumbnail of the current viewport
        thumbnail_future = await Utils.wrapped_execute(action_query, create_thumbnail)
        thumbnail = await thumbnail_future

        # Get current task
        task = await gazu.task.get_task(action_query.context_metadata["task_id"])

        # Check the given task status
        task_statuses = await gazu.task.all_task_statuses()
        task_status = await gazu.task.get_task_status(task["task_status"]["id"])
        if parameters["status"] in task_statuses:
            task_status = gazu.task.get_task_status_by_short_name(parameters["status"])
        else:
            logger.warning(
                "Could not set the given task status: The given task status is invalid"
            )

        await gazu.task.add_comment(
            task,
            task_status,
            parameters["description"],
            attachments=[thumbnail],
        )
