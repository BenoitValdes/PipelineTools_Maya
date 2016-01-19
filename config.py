''' CONFIGURATION '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
import maya.cmds as cmds
path1 = r'D:\Projects'									#The main project path
path2 = False											#If you have another project directory you can enable PATH2 in adding the path of the directory
projectPath = path1										#By default the project path is the path1	
templatePath = r'D:\Code\PipelineTools\Templates'
mayaTemplate = 'MayaTemplate_2016.ma'
workspaceTemplate = 'workspace.mel'
imgFilePrefix = '\\Render\\<Scene>\\<RenderLayer>\\<RenderLayer>_<Scene>'
path1Label = 'Local: '										#This label will be put before the project name in the project list for the LOCAL files ex: 'Local: Project01' or 'P:/Project01'
path2Label = 'Server: '									#This label will be put before the project name in the project list for the SERVER files ex: 'Server: Project01' or '\\Project01'
defaultLib = 'LIB'											#The default name of the LIB filder
defaultFilm = 'FILM'										#The default name of the FILM filder
defaultPrint = 'PRINT'										#The default name of the PRINT filder
labelLib = 'Library'
labelFilm = 'Film'
labelPrint = 'Print'
tab = '	             '
libFamilyList = ['Characters','Props','Sets','Vehicles']	#Content for the Library family list
libDeptList = ['Modeling','Setup','Shading','Fur','VFX']			#Content for the Library dept list
filmDeptList = ['Anim','Layout','Lighting','VFX']			#Content for the Film family list
printDeptList = ['Layout','Lighting','VFX']					#Content for the Film family list