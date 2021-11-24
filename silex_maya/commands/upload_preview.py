from __future__ import annotations
import os
import pathlib
import typing
from typing import Any, Dict, List

import gazu.task
import logging

from silex_client.action.command_base import CommandBase, CommandParameters
from silex_client.utils.log import logger
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class UploadPreview(CommandBase):
    """
    Upload the given preview to kitsu as a comment
    """

    parameters: CommandParameters = {
        "preview_path": {"label": "Preview path", "type": str, "value": None},
        "description": {"label": "Description", "type": str, "value": None},
        "status": {
            "label": "Task Status",
            "type": SelectParameterMeta("wfa", "done", "wip", "retake"),
            "value": None,
        },
    }

    required_metadata: List[str] = ["task_id"]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.logger
    ):
        if not os.path.isfile(parameters["preview_path"]):
            logger.error(
                "The preview file path %s is incorrect", parameters["preview_path"]
            )
            raise Exception(
                "The preview file path {} is incorrect".format(
                    parameters["preview_path"]
                )
            )

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
            attachments=[parameters["preview_path"]],
        )
