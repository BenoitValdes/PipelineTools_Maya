import maya.cmds as cmds
import os
import re

def increment():
    versionList = []
    currentScene = unicode(cmds.file(q=True, sn=True))
    if currentScene:
        sceneName = currentScene.split("/")[-1]
        currentScene = "/".join(currentScene.split("/")[0:-1])
        if currentScene.endswith('Edit'):
            for files in os.listdir(currentScene):
               files = str(files)
               for files in files.split('.')[:-1]:
                   version = files.split('_')[-1]
                   versionList.append(version[1:]) 
            
            version = int(sorted(versionList, reverse=True)[0])+1
            if version < 10:        
                version = '0'+str(version)
            
            newFile = currentScene+'/'+re.sub('_v[0-9]+','_v'+str(version),sceneName)
            cmds.file( rename=newFile )
            cmds.file( save=True, type='mayaAscii' )
            
        elif 'Edit' in os.listdir(currentScene):
            for files in os.listdir(currentScene+'/Edit'):
               files = str(files)
               for files in files.split('.')[:-1]:
                   version = files.split('_')[-1]
                   versionList.append(version[1:]) 
            
            version = int(sorted(versionList, reverse=True)[0])+1
            if version < 10:       
                version = '0'+str(version)
            newFile = currentScene+'/Edit'+'/'+re.sub('.ma','_v'+str(version)+'.ma',sceneName)
            cmds.file( rename=newFile )
            cmds.file( save=True, type='mayaAscii' )
        else:
            print 'Dude you are not in the pipeline'
    
    else:
        print 'Dude you are not in the pipeline'