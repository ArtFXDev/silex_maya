import maya.cmds as cmds
from silex_client.resolve.config import Config

def create_shelf():
    shelf_id = "silex_shelf"

    if cmds.shelfLayout(shelf_id, ex=1):
        if cmds.shelfLayout(shelf_id, q=1, ca=1):
            for each in cmds.shelfLayout(shelf_id, q=1, ca=1):
                cmds.deleteUI(each)
        cmds.deleteUI(shelf_id)

    cmds.shelfLayout(shelf_id, p="ShelfLayout")
    cmds.setParent(shelf_id)

    import_statement = "from silex_client.action.action_query import ActionQuery\n"
    actions = {
        item["name"]: f"{import_statement}ActionQuery('{item['name']}').execute()"
        for item in Config().actions
    }

    for action in actions:
        cmds.setParent(shelf_id)
        cmds.shelfButton(
            width=37,
            height=37,
            image="commandButton.png",
            l=action,
            imageOverlayLabel=action,
            command=actions[action],
            olb=(0, 0, 0, 0),
            olc=(0.9, 0.9, 0.9),
        )
