from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.core.context import Context
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils
import gazu.files
import gazu.task
import traceback


class Compute_output_path(CommandBase):
    """
    return output file path
    """

    parameters = {
        "publish_type": {
            "label": "Select a publish type",
            "type": SelectParameterMeta("maa", "obj", "abc", "fbx", "usd", "ass", "vrscene"),
            "value": None,
            "tooltip": "Select a publish type in the list",
        },
        "file_namme": {
            "label": "File name",
            "type": str,
        },
    }

    # required_metadata = ['task_id', 'task_type_id']

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        async def get_ids() -> str:

            try:
                task_type: str = Context.get().metadata['task_type']
                task_type_id: str = gazu.task.get_task_type_by_name(
                    task_type).get('id', None)
            except:
                await Utils.wrapped_execute(action_query, lambda: traceback.print_exc())
                return -1, None

            return task_type_id

        #    frames_nb = parameters.get('frames_nb')

        task_type_id: str = await get_ids()

        task_type_id: str = action_query.context_metadata.get("task_id", None)
        if task_type_id is None:
            await Utils.wrapped_execute(action_query, lambda: print(" ERROR : Invalid task_type_id !"))
            return -1, None

        output_type_id: str = await gazu.files.get_output_type_by_short_name(
            parameters.get('publish_type'))
        name: str = parameters.get('file_name')

        await gazu.files.build_entity_output_file_path(
            entity=task_type_id,
            output_type=output_type_id,
            task_type=task_type_id,
            name=name,
            mode="output",
            #    nb_elements=frames_nb
        )
