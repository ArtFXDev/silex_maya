from __future__ import annotations
import typing
from typing import Any, Dict

import pathlib
from silex_client.action.command_base import CommandBase
from silex_maya.commands.open import Open
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import (
    TextParameterMeta,
    RadioSelectParameterMeta,
)
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class OpenConform(Open):
    """
    Open the given scene file
    """

    parameters = {
        "conform_path": {
            "label": "filename",
            "type": pathlib.Path,
            "value": None,
        }
    }

    async def _prompt_override(
        self, file_path: pathlib.Path, action_query: ActionQuery
    ) -> str:
        """
        Helper to prompt the user for a new conform type and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("info"),
            name="info",
            label="Info",
            value=f"The path:\n{file_path}\nAlready exists",
        )
        new_parameter = ParameterBuffer(
            type=RadioSelectParameterMeta(
                "Override", "Keep existing", "Always override", "Always keep existing"
            ),
            name="existing_file",
            label="Existing file",
        )
        # Prompt the user to get the new path
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "existing_file": new_parameter,
            },
        )
        return response["existing_file"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        conform_path: pathlib.Path = parameters["conform_path"]

        if conform_path.exists():
            response = action_query.store.get("maya_conform_override")
            if response is None:
                response = await self._prompt_override(conform_path, action_query)
            if response in ["Always override", "Always keep existing"]:
                action_query.store["maya_conform_override"] = response
            if response in ["Keep existing", "Always keep existing"]:
                logger.error("AAAAAAAAAAAAAA")
                parameters["file_path"] = conform_path

        logger.error(parameters)
        return super().__call__(parameters, action_query, logger)
