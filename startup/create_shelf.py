from collections import defaultdict

import maya.cmds as cmds
from silex_client.resolve.config import Config


def create_shelf():
    shelf_id = "Silex"

    if cmds.shelfLayout(shelf_id, ex=1):
        if cmds.shelfLayout(shelf_id, q=1, ca=1):
            for each in cmds.shelfLayout(shelf_id, q=1, ca=1):
                cmds.deleteUI(each)
        cmds.deleteUI(shelf_id)

    cmds.shelfLayout(shelf_id, p="ShelfLayout")

    # Construct menu items commands
    import_statement = "from silex_client.action.action_query import ActionQuery\n"

    # Organize shelf items by category
    by_shelf = defaultdict(list)

    # Get the resolved action configs
    for action in Config.get().actions:
        resolved_action = Config.get().resolve_action(action["name"])

        if resolved_action is not None:
            shelf = resolved_action[action["name"]].get("shelf")
            by_shelf[shelf if shelf is not None else "other"].append(
                {
                    "name": action["name"],
                    "action": resolved_action,
                    "script": f"{import_statement}ActionQuery('{action['name']}').execute()",
                }
            )

    cmds.setParent(shelf_id)

    for index, shelf in enumerate(by_shelf):
        for action in by_shelf[shelf]:
            action_name, action, script = action.values()
            action = action[action_name]

            cmds.shelfButton(
                width=37,
                height=37,
                image=action.get("thumbnail", ""),
                l=action_name,
                imageOverlayLabel=action_name,
                command=script,
                olb=(0, 0, 0, 0),
                olc=(0.9, 0.9, 0.9),
            )

        # Add a separator between categories
        if index != len(by_shelf) - 1:
            cmds.separator(width=12, height=35, style="shelf", hr=False)
