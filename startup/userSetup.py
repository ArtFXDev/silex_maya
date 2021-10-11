from silex_client.core.context import Context
from maya import cmds

Context.get().event_loop.start()
Context.get().ws_connection.start()

def create_shelf():
    shelf_id = "silex_shelf"

    if cmds.shelfLayout(shelf_id, ex=1):
        cmds.deleteUI(shelf_id)

    cmds.shelfLayout(shelf_id, p="ShelfLayout")
    cmds.setParent(shelf_id)


    actions = { item["name"]: f"Context.get().get_action('{item['name']}').execute()" for item in Context.get().config.actions }

    for action in actions:
        cmds.setParent(shelf_id)
        cmds.shelfButton(width=37, height=37, image="commandButton.png", l=action, imageOverlayLabel=action , command=actions[action], olb=(0, 0, 0, 0), olc=(.9, .9, .9))

maya.utils.executeDeferred(create_shelf)