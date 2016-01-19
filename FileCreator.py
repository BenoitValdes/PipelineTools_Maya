# 
# Author: Fredrik Averpil, fredrik.averpil@gmail.com, http://fredrikaverpil.tumblr.com
# 

# -*- coding: utf8 -*-

''' Imports regardless of Qt type '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
import os, sys
import xml.etree.ElementTree as xml
from cStringIO import StringIO
import shutil
from config import *


''' CONFIGURATION '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''

# General
QtType = 'PySide'										# Edit this to switch between PySide and PyQt
sys.dont_write_bytecode = True									# Do not generate .pyc files
uiFile = os.path.join(os.path.dirname(__file__), 'UI/FileCreator.ui')				# The .ui file to load
windowTitle = 'File Creator'									# The visible title of the window
windowObject = 'fileCreator'									# The name of the window object

# Standalone settings
darkorange = False										# Use the 'darkorange' stylesheet

# Maya settings
launchAsDockedWindow = False									# False = opens as free floating window, True = docks window to Maya UI

# Nuke settings
launchAsPanel = False										# False = opens as regular window, True = opens as panel
parentToNukeMainWindow = True									# True = makes window stay on top of Nuke

# Site-packages location:
site_packages_Win = ''										# Location of site-packages containing PySide and pysideuic and/or PyQt and SIP
site_packages_Linux = ''									# Location of site-packages containing PySide and pysideuic and/or PyQt and SIP
site_packages_OSX = ''										# Location of site-packages containing PySide and pysideuic and/or PyQt and SIP
#site_packages_Win = 'C:/Python26/Lib/site-packages'						# Example: Windows 7
#site_packages_Linux = '/usr/lib/python2.6/site-packages'					# Example: Linux CentOS 6.4
#site_packages_OSX = '/Library/Python/2.7/site-packages'					# Example: Mac OS X 10.8 Mountain Lion


''' Run mode '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
runMode = 'standalone'
try:
	import maya.cmds as cmds
	import maya.OpenMayaUI as omui
	import shiboken
	runMode = 'maya'
except:
	pass
try:
	import nuke
	from nukescripts import panels
	runMode = 'nuke'	
except:
	pass


''' PySide or PyQt '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
if (site_packages_Win != '') and ('win' in sys.platform): sys.path.append( site_packages_Win )
if (site_packages_Linux != '') and ('linux' in sys.platform): sys.path.append( site_packages_Linux )
if (site_packages_OSX != '') and ('darwin' in sys.platform): sys.path.append( site_packages_OSX )

if QtType == 'PySide':
	from PySide import QtCore, QtGui, QtUiTools
	import pysideuic	
elif QtType == 'PyQt':
	from PyQt4 import QtCore, QtGui, uic
	import sip
print 'This app is now using ' + QtType




''' Auto-setup classes and functions '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''


class PyQtFixer(QtGui.QMainWindow):
	def __init__(self, parent=None):
		"""Super, loadUi, signal connections"""
		super(PyQtFixer, self).__init__(parent)
		print 'Making a detour (hack), necessary for when using PyQt'


def loadUiType(uiFile):
	"""
	Pyside lacks the "loadUiType" command, so we have to convert the ui file to py code in-memory first
	and then execute it in a special frame to retrieve the form_class.
	"""
	parsed = xml.parse(uiFile)
	widget_class = parsed.find('widget').get('class')
	form_class = parsed.find('class').text

	with open(uiFile, 'r') as f:
		o = StringIO()
		frame = {}

		if QtType == 'PySide':
			pysideuic.compileUi(f, o, indent=0)
			pyc = compile(o.getvalue(), '<string>', 'exec')
			exec pyc in frame

			#Fetch the base_class and form class based on their type in the xml from designer
			form_class = frame['Ui_%s'%form_class]
			base_class = eval('QtGui.%s'%widget_class)
		elif QtType == 'PyQt':
			form_class = PyQtFixer
			base_class = QtGui.QMainWindow
	return form_class, base_class
form, base = loadUiType(uiFile)



def wrapinstance(ptr, base=None):
	"""
	Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)
	:param ptr: Pointer to QObject in memory
	:type ptr: long or Swig instance
	:param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
	:type base: QtGui.QWidget
	:return: QWidget or subclass instance
	:rtype: QtGui.QWidget
	"""
	if ptr is None:
		return None
	ptr = long(ptr) #Ensure type
	if globals().has_key('shiboken'):
		if base is None:
			qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
			metaObj = qObj.metaObject()
			cls = metaObj.className()
			superCls = metaObj.superClass().className()
			if hasattr(QtGui, cls):
				base = getattr(QtGui, cls)
			elif hasattr(QtGui, superCls):
				base = getattr(QtGui, superCls)
			else:
				base = QtGui.QWidget
		return shiboken.wrapInstance(long(ptr), base)
	elif globals().has_key('sip'):
		base = QtCore.QObject
		return sip.wrapinstance(long(ptr), base)
	else:
		return None


def maya_main_window():
	main_window_ptr = omui.MQtUtil.mainWindow()
	return wrapinstance( long( main_window_ptr ), QtGui.QWidget )	# Works with both PyQt and PySide




''' Main class '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''

class Main(form, base):
	def __init__(self, parent=None):
		"""Super, loadUi, signal connections"""
		super(Main, self).__init__(parent)

		if QtType == 'PySide':
			print 'Loading UI using PySide'
			self.setupUi(self)


		elif QtType == 'PyQt':
			print 'Loading UI using PyQt'
			uic.loadUi(uiFile, self)	
		
		#Windows creation
		self.setObjectName(windowObject)
		self.setWindowTitle(windowTitle)
		#
		
		#First load		
		self.listProjectFiles()
		self.refreshInterface()
		#
		
		#Les signaux		
		currentSetProject = cmds.workspace (q=True, rd=True)	#get the current project in maya
		currentSetProject = currentSetProject.split('/')[-2]	#get the project name
		currentSetProject = self.projectList.findText(currentSetProject, QtCore.Qt.MatchContains)		#search the project in the list
		if currentSetProject !=-1:													# if the project exist select it in the list
			self.projectList.setCurrentIndex(currentSetProject)
			
		self.projectList.currentIndexChanged.connect(self.refreshInterface)
		self.familyList.currentIndexChanged.connect(self.refreshAssetList)
		self.familyInput.textChanged.connect(self.refreshCreateButton)
		self.assetList.currentIndexChanged.connect(self.refreshCreateButton)
		self.assetInput.textChanged.connect(self.refreshCreateButton)
		self.deptList.currentIndexChanged.connect(self.refreshCreateButton)
		self.libraryRadio.clicked.connect(self.refreshInterface)
		self.filmRadio.clicked.connect(self.refreshInterface)		
		self.printRadio.clicked.connect(self.refreshInterface)
		self.createOpenRadio.clicked.connect(self.refreshCreateButton)
		self.createRadio.clicked.connect(self.refreshCreateButton)
		self.saveRadio.clicked.connect(self.refreshCreateButton)
		self.createButton.clicked.connect(self.createFiles)
		#	
		
	def restoreDefault(self):	
		self.libraryRadio.setText(labelLib)
		self.filmRadio.setText(labelFilm)
		self.familyInput.clear()
		self.assetInput.clear()
		self.familyList.clear()
		self.assetList.clear()
		self.deptList.clear()
		self.familyInput.setEnabled(True)
		self.assetInput.setEnabled(True)
		self.familyList.setEnabled(True)
		self.familyList.addItem('')
		self.assetList.addItem('')
		self.deptList.addItem('')
	
	def refreshCreateButton(self):
		self.createButton.setDisabled(True)
		if self.familyInput.text() or self.familyList.currentText():
			if self.assetInput.text() or self.assetList.currentText():
				if self.deptList.currentText():
					if self.libraryRadio.isChecked() and self.familyInput.text() =='DISABLED' and not self.familyList.currentText():
						return 'nothing'
					else:
						self.createButton.setEnabled(True)
		if self.createOpenRadio.isChecked():
			self.createButton.setText(self.createOpenRadio.text())
		if self.createRadio.isChecked():
			self.createButton.setText(self.createRadio.text())		
		if self.saveRadio.isChecked():
			self.createButton.setText(self.saveRadio.text())		
	
	def refreshInterface(self):
		self.restoreDefault()
		
		if self.libraryRadio.isChecked():
			self.familyInput.setDisabled(True)
			self.familyInput.insert('DISABLED')
			self.familyList.addItems(libFamilyList)
			self.deptList.addItems(libDeptList)
			self.familyLabel.setText('Family')
			self.assetLabel.setText('Asset')
			
		if self.filmRadio.isChecked():
			self.deptList.addItems(filmDeptList)
			self.familyList.addItems(os.listdir(self.getProjectPath(self.projectList.currentText())+'\\'+self.delLabel(self.projectList.currentText())+'\\'+defaultFilm))
			self.familyLabel.setText('Seq    ')
			self.assetLabel.setText('Plan   ')
		
		if self.printRadio.isChecked():
			self.familyInput.setDisabled(True)
			self.familyInput.insert('DISABLED')
			self.familyList.setDisabled(True)
			self.deptList.addItems(printDeptList)
			self.familyLabel.setText('         ')
			self.assetLabel.setText('Print  ')
		self.refreshCreateButton()
		
	def refreshAssetList(self):
		self.refreshCreateButton()
		self.assetList.clear()
		currentAssetList = []
		if self.libraryRadio.isChecked():
			currentCat = defaultLib
		if self.filmRadio.isChecked():
			currentCat = defaultFilm
		
		if self.printRadio.isChecked():
			currentCat = defaultPrint
			
		if self.familyList.currentText():
			assetsPath = self.getProjectPath(self.projectList.currentText())+'\\'+self.delLabel(self.projectList.currentText())+'\\'+currentCat+'\\'+self.familyList.currentText()
			getAssetsFiles = os.listdir(assetsPath)
			if len(getAssetsFiles)!= 0:
				for nameB in getAssetsFiles:
					currentAssetList.append(nameB)		
			self.assetList.addItems(currentAssetList)
		
		if currentCat == defaultPrint:
			assetsPath = self.getProjectPath(self.projectList.currentText())+'\\'+self.delLabel(self.projectList.currentText())+'\\'+currentCat
			getAssetsFiles = os.listdir(assetsPath)
			if len(getAssetsFiles)!= 0:
				for nameB in getAssetsFiles:
					currentAssetList.append(nameB)		
			self.assetList.addItems(currentAssetList)
			
								
	def createFiles(self):	
		projectPath = self.getProjectPath(self.projectList.currentText())+'\\'+self.delLabel(self.projectList.currentText())
		familyName = self.familyInput.text()
		if not familyName or familyName == 'DISABLED':
				familyName = self.familyList.currentText()
		assetName = self.assetInput.text()
		if not assetName or assetName == 'DISABLED':
				assetName = self.assetList.currentText()
				
		if self.libraryRadio.isChecked():
			fileName = assetName+'_'+self.deptList.currentText()+'_v00.ma'
			path = projectPath+'\\'+defaultLib+'\\'+self.familyList.currentText()+'\\'+assetName+'\\'+self.deptList.currentText()+'\\Edit\\'
			renderPath = defaultLib+'\\'+self.familyList.currentText()+'\\'+assetName+'\\'+self.deptList.currentText()+imgFilePrefix
			
		if self.filmRadio.isChecked():
			fileName = defaultFilm+'_'+familyName+'_'+assetName+'_'+self.deptList.currentText()+'_v00.ma'
			path = projectPath+'\\'+defaultFilm+'\\'+familyName+'\\'+assetName+'\\'+self.deptList.currentText()+'\\Edit\\'
			renderPath = defaultFilm+'\\'+self.familyList.currentText()+'\\'+assetName+'\\'+self.deptList.currentText()+imgFilePrefix
		
		if self.printRadio.isChecked():
			fileName = defaultPrint+'_'+assetName+'_'+self.deptList.currentText()+'_v00.ma'
			path = projectPath+'\\'+defaultPrint+'\\'+assetName+'\\'+self.deptList.currentText()+'\\Edit\\'
			renderPath = defaultPrint+'\\'+self.familyList.currentText()+'\\'+assetName+'\\'+self.deptList.currentText()+imgFilePrefix
		
		if self.createOpenRadio.isChecked():
			if self.createAssetsFiles(path):
				self.copyRename(templatePath,mayaTemplate,path,fileName)
				cmds.file( path+fileName, force=True, open=True )
				mel.eval('setProject "'+projectPath+'";')
				renderPath = '/'.join(renderPath.split('\\'))
				cmds.setAttr("defaultRenderGlobals.imageFilePrefix",  renderPath, type="string")
				
				
			else:
				self.alertMessage('The file already exist')
		if self.createRadio.isChecked():
			if self.createAssetsFiles(path):
				cmds.file( path+fileName, force=True, open=False )
				mel.eval('setProject "'+projectPath+'";')
				renderPath = '/'.join(renderPath.split('\\'))
				cmds.setAttr("defaultRenderGlobals.imageFilePrefix",  renderPath, type="string")
			else:
				self.alertMessage('The file already exist')
		if self.saveRadio.isChecked():
			if self.createAssetsFiles(path):
				cmds.file( rename=path+fileName )
				cmds.file( save=True, type='mayaAscii' )
				mel.eval('setProject "'+projectPath+'";')
				renderPath = '/'.join(renderPath.split('\\'))
				cmds.setAttr("defaultRenderGlobals.imageFilePrefix",  renderPath, type="string")
			else:
				self.alertMessage('The file already exist')
	
	''' CREATE ASSETS FILES FUNCTION '''
	def createAssetsFiles(self,path):
		if not os.path.exists(path):
			lenProjectPath = len(projectPath.split('\\'))
			dirList = path.split('\\')
			dirList = dirList[lenProjectPath:]
			path = projectPath+'\\'
			for dirs in dirList[:-1]:
				os.chdir(path)
				path = path+dirs+'\\'
				if not os.path.exists(path):
					os.mkdir(dirs)
			return True
		else:
			return False
	''' COPY AND RENAME FILE FUNCTION '''
	def copyRename(self,oldPath,oldFile,newPath,newFile):
		src = oldPath+'\\'+oldFile		
		dst = newPath+'\\'+newFile
		shutil.copy(src,dst)
		
	''' ALERT MESSAGE FUNCTION '''
	def alertMessage(self,message='Sorry an error was occured'):
		message = str(message)
		cmds.confirmDialog(title='Alert', message=message)
			
	''' DEL LABEL fUNCTION '''
	def delLabel(self,selectedProject):						
		if selectedProject.startswith(path1Label):
			lensLabel = len(path1Label)
			selectedProject = selectedProject[lensLabel:]
			
		if selectedProject.startswith(path2Label):
			lensLabel = len(path2Label)
			selectedProject = selectedProject[lensLabel:]
		
		return selectedProject
	
	''' GET PROJECT PATH fUNCTION '''
	def getProjectPath(self,selectedProject):						
		if selectedProject.startswith(path1Label):
			projectPath = path1
			
		if selectedProject.startswith(path2Label):
			projectPath = path2
		
		return projectPath
		
	''' IF PROJECT FUNCTION '''
	def ifProject(self,projectPath):
		displayFile = False
		for file in os.listdir(projectPath):
			if file.endswith("projectSettings"):
				projectSettingPath = projectPath+'\\'+file
				f = open(projectSettingPath, "r")
				f = f.read()
				if f.endswith('True'):
					displayFile = True
					
		return displayFile
	''' LIST PROJECT FILES + CREATE LABEL fUNCTION '''
	def listProjectFiles(self):								
		projectList = []
		if path1 and path1Label:
		    localProjectList = os.listdir(path1)
		    for project in localProjectList:
				projectPath = path1+'\\'+project
				if self.ifProject(projectPath):
					project = path1Label+project
					projectList.append(project)
				
		elif path1:
			projectList.append(os.listdir(path1))
		    
		if path2 and path2Label:
		    serverProjectList = os.listdir(path2)
		    for serverProject in serverProjectList:
				serverProject = path2Label+serverProject
				projectList.append(serverProject)
				
		elif path2:
			projectList.append(os.listdir(path2))

		getProjectFiles = os.listdir(projectPath)  
		self.projectList.addItems(projectList)

	
	def closeEvent(self, event):
		''' Delete this object when closed.'''
		self.deleteLater()




''' Run functions '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''

def runStandalone():
	app = QtGui.QApplication(sys.argv)
	global gui
	gui = Main()
	gui.show()

	if darkorange:
		themePath = os.path.join( os.path.dirname(__file__), 'theme' )
		sys.path.append( themePath )
		import darkorangeResource
		stylesheetFilepath = os.path.join( themePath, 'darkorange.stylesheet' )
		with open( stylesheetFilepath , 'r' ) as shfp:
			gui.setStyleSheet( shfp.read() )
		app.setStyle("plastique")
	
	sys.exit(app.exec_())

def runMaya():
	if cmds.window(windowObject, q=True, exists=True):
		cmds.deleteUI(windowObject)
	if cmds.dockControl( 'MayaWindow|'+windowTitle, q=True, ex=True):
		cmds.deleteUI( 'MayaWindow|'+windowTitle )
	global gui
	gui = Main( parent=maya_main_window() )
	#gui = Main( parent=QtGui.QApplication.activeWindow() ) # Alternative way of setting parent window

	if launchAsDockedWindow:
		allowedAreas = ['right', 'left']
		cmds.dockControl( windowTitle, label=windowTitle, area='left', content=windowObject, allowedArea=allowedAreas )
	else:
		#gui.setWindowModality(QtCore.Qt.WindowModal) # Set modality
		gui.show() 

def runNuke():
	moduleName = __name__
	if moduleName == '__main__':
		moduleName = ''
	else:
		moduleName = moduleName + '.'
	global gui
	if launchAsPanel:
		pane = nuke.getPaneFor('Properties.1')
		panel = panels.registerWidgetAsPanel( moduleName + 'Main' , windowTitle, ('uk.co.thefoundry.'+windowObject+'Window'), True).addToPane(pane) # View pane and add it to panes menu
		gui = panel.customKnob.getObject().widget
	else:
		if parentToNukeMainWindow:
			gui = Main( parent=QtGui.QApplication.activeWindow() )
		else:
			gui = Main()
		#gui.setWindowModality(QtCore.Qt.WindowModal) # Set modality
		gui.show()





if runMode == 'standalone':
	runStandalone()
elif runMode == 'maya':
	runMaya()
elif runMode == 'nuke':
	runNuke()
