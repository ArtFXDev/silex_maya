import maya.cmds as cmds
import maya.mel as mel

def custom_save():
    # no install if in batch mode
    cmd='python("from silex_client.action.action_query import ActionQuery;ActionQuery(\'save\').execute()")'
    # hijack save button
    cmds.iconTextButton(u"saveSceneButton", edit=True, command=cmd, sourceType="mel")
    # hijack save menu item
    mel.eval("buildFileMenu();") # new in Maya 2009, we have to explicitly create the file menu before modifying it
    cmds.setParent(u"mainFileMenu", menu=True)
    cmds.menuItem(u"saveItem", edit=True, label="Save Scene", command=cmd)
    # hijack CTRL-S named command
    cmds.nameCommand(u"NameComSave_File", annotation="Your Custom Save", command=cmd )



