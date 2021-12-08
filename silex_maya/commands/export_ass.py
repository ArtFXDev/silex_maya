from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.dialogs import Dialogs
from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import logging

class ExportAss(CommandBase):
    """
    Export selection as ass
    """

    cam_list = cmds.listCameras()
    cam_list.append('No camera')

    parameters = {
        "file_dir": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        },
        "camera": {
            "label": "Export camera",
            "type": SelectParameterMeta(*cam_list),
            "tooltip": "Name the render camera"
        },
        "selection": {
            "label": "Export selection",
            "type": bool,
        },
        "compression": {
            "label": "Compression (gzip)",
            "type": bool,
        },
        "bounding_box": {
            "label": "Export Bounding Box",
            "type": bool,
            "value": True,
        },
        "binary_encoding": {
            "label": "Use Binary Encoding",
            "type": bool,
            "value": True,
        },

        "options": {
            "label": "Options",
            "type": bool,
            "value": True,
        },
        "lights": {
            "label": "Lights",
            "type": bool,
            "value": True,
        },
        "shapes": {
            "label": "shapes",
            "type": bool,
            "value": True,
        },
        "shaders": {
            "label": "Shaders",
            "type": bool,
            "value": True,
        },
        "override": {
            "label": "Override Nodes",
            "type": bool,
            "value": True,
        },
        "diver": {
            "label": "Divers",
            "type": bool,
            "value": True,
        },
        "filters": {
            "label": "Filters",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.logger
    ):

        def export_ass(path: str, cam: str, sel: str, Llinks: bool, Slinks: bool, Bbox: bool, binary: str, mask: int) -> None:

            p = pathlib.Path(path)
            cmds.workspace(fileRule=['ASS', p.parents[0]])

            cmds.arnoldExportAss(
                f=path,
                cam=cam,
                s=sel,
                lightLinks=Llinks,
                shadowLinks=Slinks,
                boundingBox=Bbox,
                asciiAss=bool(1-binary),
                mask=mask,
            )

        def compute_mask() -> int:
            options: bool = parameters.get('options')
            camera: bool = bool(parameters.get('camera') != 'No camera')
            light: bool = parameters.get('lights')
            shape: bool = parameters.get('shapes')
            shader: bool = parameters.get('shaders')
            override: bool = parameters.get('override')
            diver: bool = parameters.get('diver')
            filters: bool = parameters.get('filters')

            return 1*options + 2*camera + 4*light + 8*shape + \
                16*shader + 32*override + 64*diver + 128*filters

        directory: str = str(parameters.get("file_dir"))
        file_name: str = str(parameters.get("file_name"))
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path: str = f"{directory}{os.path.sep}{file_name}.ass"
        sel: str = parameters.get('selection')
        Llinks: bool = parameters.get('light')
        Slinks: bool = parameters.get('light')
        Bbox: bool = parameters.get('bounding_box')
        cam: str = parameters.get('camera')
        binary: bool = parameters.get('binary_encoding')
        mask: int = compute_mask()

        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)

        selection = await Utils.wrapped_execute(action_query, cmds.ls, sl=True)
        selection = selection.result()
        if selected and not len(selection):
            raise Exception('No selection detected')

        await Utils.wrapped_execute(action_query, lambda: export_ass(export_path, cam, sel, Llinks, Slinks, Bbox, binary, mask))

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to ASS")
        return export_path
