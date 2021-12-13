import maya.cmds as cmds
import maya.mel as mel

def custom_save():
    save_cmd='python("from silex_client.action.action_query import ActionQuery;ActionQuery(\'save\').execute()")'
    increment_and_save_cmd='python("from silex_client.action.action_query import ActionQuery;ActionQuery(\'increment_and_save\').execute()")'
    # hijack save button
    cmds.iconTextButton(u"saveSceneButton", edit=True, command=save_cmd, sourceType="mel")
    # hijack save menu item
    mel.eval("buildFileMenu();") # new in Maya 2009, we have to explicitly create the file menu before modifying it
    cmds.setParent(u"mainFileMenu", menu=True)
    cmds.menuItem(u"saveItem", edit=True, label="Save Scene", command=save_cmd)
    # hijack CTRL-S named command
    cmds.nameCommand(u"NameComSave_File", annotation="silex save", command=save_cmd )
    # cmds.hotkey( k='s', ctl=True, name='NameComSave_File' )


    # # hijack alt+s command
    # cmds.nameCommand( 'silexIncrementAndSave', annotation='silex increment and save', command=increment_and_save_cmd)
    # cmds.hotkey( 's', query=True, alt=True, ctl=True, name='silexIncrementAndSave')
    # #incrementAndSaveScene



