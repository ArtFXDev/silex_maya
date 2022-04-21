from __future__ import annotations

import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import MultipleSelectParameterMeta
from silex_maya.utils import thread as thread_maya

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging
import re
import os
import pathlib

import fileseq
from maya import cmds, mel
from maya.app.renderSetup.model import renderSetup


class ExportAss(CommandBase):
    """
    Export to ass
    """

    parameters = {
        "directory": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
            "hide": True,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
            "hide": True,
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "render_layers": {
            "label": "Select render layers",
            "type": MultipleSelectParameterMeta(),
            "value": ["masterLayer"],
        },
    }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Add render layers to parameters
        if "render_layers" in parameters:

            render_layers: List[Any] = await thread_maya.execute_in_main_thread(
                cmds.ls, typ="renderLayer"
            )

            # Delete default renderlayers to replace them with mmasterLayer (necessaray for swiching viewport when exporting)
            del render_layers[0]

            for index, layer in enumerate(render_layers):
                render_layers[index] = layer.replace("rs_", "")

            selection_list: List[str] = ["masterLayer", 'assets'] + [
                layer for layer in render_layers
            ]

            self.command_buffer.parameters[
                "render_layers"
            ].type = MultipleSelectParameterMeta(*selection_list)

    def _get_masterlayer(self):
        # Switch masterlayer to visible
        mel.eval(
            "$tmp = $gMainProgressBar; timeField -edit -value `currentTime -query` TimeSlider|MainTimeSliderLayout|formLayout8|timeField1; renderLayerDisplayName defaultRenderLayer;"
        )

        # Return visible layer
        return renderSetup.instance().getVisibleRenderLayer()

    def _export_sequence(
        self,
        directory: pathlib.Path,
        logger,
        file_name: pathlib.Path,
        frame_range: fileseq.FrameSet,
        selected_render_layers: List[str],
    ):
        """Export ass for each frame and each render layers"""

        frames_list = list(frame_range)

        # Each render layer is exported to a different directory
        output_path = directory / "<RenderLayer>" / f"{file_name}_<RenderLayer>"

        # Get all render layer in maya
        render_layers: List[Any] = renderSetup.instance().getRenderLayers()
        render_layers_dict: Dict[str, Any] = dict(
            zip([layer.name() for layer in render_layers], render_layers)
        )

        # Get master layer if it has been selected in the parameters
        if "masterLayer" in selected_render_layers:
            render_layers_dict.update(
                {"masterLayer": self._get_masterlayer()}
            )

        # Get master layer if assets has been selected in the parameters (asset is a masterlayer)
        if "assets" in selected_render_layers:
            render_layers_dict.update(
                {"assets": self._get_masterlayer()}
            )

        # Each layer is exported seperatly
        for layer_name in selected_render_layers:
            layer: Any = render_layers_dict[layer_name]
            logger.error(layer)

            sequence = []

            # We export a ass file for every frame in the range
            for frame in frames_list:

                export_args = {'asciiAss':1, 'sf':frame, 'ef':frame, 'f':output_path}
                
                # Specific export for assets
                if layer_name == 'assets':
                    output_path = directory / "assets" / f"{file_name}"
                    export_args.update({'f': output_path, "camera":'topShape'})

                    # If only one frame is exported, assets does not need increment
                    if len(frames_list) == 1:
                        del export_args['sf']
                        del export_args['ef']
                        
                # Export the active (visible) layer in the context
                logger.error(renderSetup.instance().switchToLayer(layer))
                renderSetup.instance().switchToLayer(layer)
                cmds.arnoldExportAss(**export_args)

                # Get exported sequence
                ass_files = os.listdir(directory / layer_name)
                sequence = [directory / layer_name / f for f in ass_files]

            # Fix bad incrementation '_0001.ass' -> '.0001.ass'
            regex = r"^.+(\_(\d+)\.)ass$"
            if re.match(regex, str(sequence[0])):
                for ass in sequence:
                    match = re.match(regex, str(ass))
                    new_ass = str(ass).replace(f'{match.group(1)}ass', f'.{match.group(2)}.ass')
                    os.rename(ass , new_ass)


    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        file_name: pathlib.Path = parameters["file_name"]
        directory: pathlib.Path = parameters[
            "directory"
        ]  # The directory parameter is temp directory

        selected_render_layers: List[str] = parameters["render_layers"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]

        # Export to a ass sequence for each frame (in an awsome, brand new temporary directory)
        await thread_maya.execute_in_main_thread(
            self._export_sequence,
            directory,
            logger,
            file_name,
            frame_range,
            selected_render_layers,
        )

        return directory
