from __future__ import annotations
import os
import pathlib
import typing
from typing import Any, Dict, List

import gazu.task
import logging

from silex_client.action.command_base import CommandBase, CommandParameters
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class UploadPreview(CommandBase):
    """
    Upload the given preview to kitsu as a comment
    """

    parameters: CommandParameters = {
        "preview_path": {"label": "Preview path", "type": pathlib.Path, "value": None},
    }

    required_metadata: List[str] = ["task_id"]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
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

        # add comment with preview
        comment = await gazu.task.add_comment(task, task_status)

        # add preview
        preview_file = await gazu.task.add_preview(
        task,
        comment,
        parameters["preview_path"]
        )
        import time
        time.sleep(10)
        # set preview
        logger.error(preview_file)
        import gazu.client as raw
        await raw.put(f"actions/preview-files/{preview_file['id']}/set-main-preview",{})

        # await gazu.task.set_main_preview(preview_file['id'])

