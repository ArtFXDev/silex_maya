from __future__ import annotations
import os
import typing
from typing import Any, Dict, List

import gazu.task

from silex_client.action.command_base import CommandBase, CommandParameters
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class UploadPreview(CommandBase):
    """
    Upload the
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
        if not isinstance(upstream, str) or not os.path.isfile(upstream):
            logger.error("The upstream file path %s is incorrect", upstream)
            raise Exception(f"The upstream file path {upstream} is incorrect")

        # Get current task
        task = await gazu.task.get_task(action_query.context_metadata["task_id"])

        # Check the given task status
        task_statuses = await gazu.task.all_task_statuses()
        task_status = await gazu.task.get_task_status(task["task_status"]["id"])
        if parameters["status"] in [
            task_status["short_name"] for task_status in task_statuses
        ]:
            task_status = await gazu.task.get_task_status_by_short_name(
                parameters["status"]
            )
        else:
            logger.warning(
                "Could not set the given task status: The given task status %s is invalid",
                parameters["status"],
            )

        await gazu.task.add_comment(
            task,
            task_status,
            parameters["description"],
            attachments=[upstream],
        )
