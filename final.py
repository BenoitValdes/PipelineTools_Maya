import maya.cmds as cmds
import os
import re
import shutil

def final():
    versionList = []
    currentScene = unicode(cmds.file(q=True, sn=True))
    if currentScene:
        sceneName = currentScene.split("/")[-1]
        currentScene = "/".join(currentScene.split("/")[0:-1])
        if currentScene.endswith('Edit'):          
            src = currentScene+'/'+sceneName		
            dst = currentScene[:-5]+'/'+re.sub('_v[0-9]+','',sceneName)
            
            for files in os.listdir(currentScene):
               files = str(files)
               for files in files.split('.')[:-1]:
                   version = files.split('_')[-1]
                   versionList.append(version[1:])
            
            version = int(sorted(versionList, reverse=True)[0])+1
            if version < 10:        
                version = '0'+str(version)
                
            dialog = cmds.confirmDialog( title='Confirm', message='Do you want increment in version '+str(version), button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            if dialog == "No" :
                shutil.copy(src,dst)
            else:
                newFile = currentScene+'/'+re.sub('_v[0-9]+','_v'+str(version),sceneName)
                cmds.file( rename=newFile )
                cmds.file( save=True, type='mayaAscii' )                
                shutil.copy(newFile,dst)
    
        else:
            print 'Dude your are not in the pipeline'
    
    else:
        print 'Dude your are not in the pipeline'
    