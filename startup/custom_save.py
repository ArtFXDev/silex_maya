import maya.cmds as cmds
import maya.mel as mel

def custom_save():
    save_cmd='python("from silex_client.action.action_query import ActionQuery;ActionQuery(\'save\').execute()")'
    # Hijack save button
    cmds.iconTextButton(u"saveSceneButton", edit=True, command=save_cmd, sourceType="mel")
    # Hijack save menu item
    mel.eval("buildFileMenu();") # new in Maya 2009, we have to explicitly create the file menu before modifying it
    cmds.setParent(u"mainFileMenu", menu=True)
    cmds.menuItem(u"saveItem", edit=True, label="Save Scene", command=save_cmd)
    # Create ctrl-s save command
    cmds.nameCommand(u"NameComSave_File", annotation="silex save", command=save_cmd)

    def reset_save():
        cmds.nameCommand("NameComSave_File", annotation="silex save", command='file -save')
    cmds.scriptJob(event=["quitApplication", reset_save])
