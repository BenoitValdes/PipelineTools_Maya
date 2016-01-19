# 
# Author: For the QT part: Fredrik Averpil, fredrik.averpil@gmail.com, http://fredrikaverpil.tumblr.com
#
#
# Author: For the File Opener script: Benoit Valdes, valdes.benoit@gmail.com, http://www.benoitvaldes.com
# 

''' Imports regardless of Qt type '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
import os, sys, time, datetime, os.path
import xml.etree.ElementTree as xml
from cStringIO import StringIO	
from config import *
import re



''' CONFIGURATION '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''

# General
QtType = 'PySide'										# Edit this to switch between PySide and PyQt
sys.dont_write_bytecode = True									# Do not generate .pyc files
uiFile = os.path.join(os.path.dirname(__file__), 'UI/FileOpener.ui')				# The .ui file to load
windowTitle = 'File Opener'									# The visible title of the window
windowObject = 'FileOpener'									# The name of the window object

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
	import maya.mel as mel	
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
		
		#Window creation
		self.setObjectName(windowObject)
		self.setWindowTitle(windowTitle)
		#

		#First INIT
		self.listProjectFiles()				#fill the project list
		
		currentSetProject = cmds.workspace (q=True, rd=True)	#get the current project in maya
		currentSetProject = currentSetProject.split('/')[-2]	#get the project name
		currentSetProject = self.projectList.findText(' '+currentSetProject, QtCore.Qt.MatchContains)		#search the project in the list
		if currentSetProject !=-1:													# if the project exist select it in the list
			self.projectList.setCurrentIndex(currentSetProject)
			
		self.setFamilyandDeptList()			#fill the family & dept list
		self.listAssetsFiles()				#fill the asset list
		os.chdir(self.getProjectPath(self.projectList.currentText()))	#Set the work folder
		self.openButton.setDisabled(True)		#disable opent button
		#
		
		#Signals
		self.projectList.currentIndexChanged.connect(self.refreshAssets)
		
		self.libraryRadio.clicked.connect(self.setFamilyandDeptList)
		self.filmRadio.clicked.connect(self.setFamilyandDeptList)
		self.printRadio.clicked.connect(self.setFamilyandDeptList)
		
		self.familyList.currentIndexChanged.connect(self.refreshAssets)
		self.deptList.currentIndexChanged.connect(self.refreshAssets)
		
		self.assetList.currentTextChanged.connect(self.refreshEditRef)
		self.finalList.currentTextChanged.connect(self.checkFinalList)
		self.editList.currentTextChanged.connect(self.checkEditList)
		
		self.openRadio.clicked.connect(self.checkRadio)
		self.importRadio.clicked.connect(self.checkRadio)
		self.refRadio.clicked.connect(self.checkRadio)
		
		self.openButton.clicked.connect(self.clickOpen)
		#	
	#Functions
	
	''' FILL FAMILY AND DEPT LIST FUNCTION '''
	def setFamilyandDeptList(self):
		selectedProject = self.projectList.currentText()
		projectPath = self.getProjectPath(selectedProject)
		self.familyList.clear()
		self.familyList.addItem('All')
		self.deptList.clear()
		self.deptList.addItem('All')
		if self.libraryRadio.isChecked():
			self.familyList.addItems(libFamilyList)
			self.deptList.addItems(libDeptList)
			
		if self.filmRadio.isChecked():
			self.familyList.addItems(os.listdir(projectPath+'\\'+self.delLabel(selectedProject)+'\\'+defaultFilm))
			self.deptList.addItems(filmDeptList)
			
			
		if self.printRadio.isChecked():
			self.deptList.addItems(printDeptList)
			
	
	''' GET FILE MODIF DATE FUNCTION '''
	def getModifDate(self,file):
		date = os.path.getmtime(file)
		date = str(datetime.datetime.fromtimestamp(date))
		return date[:10]
	
	''' DEL LABEL fUNCTION '''
	def delLabel(self,selectedProject):						
		if selectedProject.startswith(path1Label):
			lensLabel = len(path1Label)
			selectedProject = selectedProject[lensLabel:]
			
		if selectedProject.startswith(path2Label):
			lensLabel = len(path2Label)
			selectedProject = selectedProject[lensLabel:]
		
		return selectedProject
	
	''' LIST TO TEXT FUNCTION '''
	def listToText(self,listEntry):
		listEntry = listEntry.text()
		return listEntry	
		
	''' GET PROJECT PATH fUNCTION '''
	def getProjectPath(self,selectedProject):						
		if selectedProject.startswith(path1Label):
			projectPath = path1
			
		if selectedProject.startswith(path2Label):
			projectPath = path2
		
		return projectPath
		
	''' GET CATEGORY FUNCTION'''
	def getCategory(self):
		if self.libraryRadio.isChecked():
			selectedCategory = defaultLib
		
		if self.filmRadio.isChecked():
			selectedCategory = defaultFilm
			
		if self.printRadio.isChecked():
			selectedCategory = defaultPrint
		
		return selectedCategory	
		
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
		
	''' LIST ASSETS FILES FUNCTION '''
	def listAssetsFiles(self):
		self.getCategory()
		assetFiles = []
		
		selectedProject = self.projectList.currentText()
		projectPath = self.getProjectPath(selectedProject)
		selectedFamilly = self.familyList.currentText()
		selectedDept = self.deptList.currentText()
		selectedCategory = self.getCategory()
		familyList = os.listdir(projectPath+'\\'+self.delLabel(selectedProject)+'\\'+selectedCategory)
		if selectedFamilly =='All':	
			if selectedDept =='All':
				for name in familyList:
					assetsPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+selectedCategory+'\\'+name
					getAssetsFiles = os.listdir(assetsPath)
					if len(getAssetsFiles)!= 0:
						for nameB in getAssetsFiles:
							currentAssetsPath = assetsPath+'\\'+nameB
							if self.getCategory() == defaultPrint:
								nameC = nameC = name+'\\'+nameB
								assetFiles.append(nameC)
							else:
								for nameC in os.listdir(currentAssetsPath):
									nameC = name+'\\'+nameB+'\\'+nameC
									assetFiles.append(nameC)
			else:
				for name in familyList:
					assetsPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+selectedCategory+'\\'+name
					getAssetsFiles = os.listdir(assetsPath)
					if len(getAssetsFiles)!= 0:
						for nameB in getAssetsFiles:
							currentAssetsPath = assetsPath+'\\'+nameB
							if self.getCategory() == defaultPrint:
								if nameB == selectedDept:
									nameC = nameC = name+'\\'+nameB
									assetFiles.append(nameC)
							else:
								for nameC in os.listdir(currentAssetsPath):
									if nameC == selectedDept:
										nameC = name+'\\'+nameB+'\\'+nameC
										assetFiles.append(nameC)
									
		else:
			if selectedDept =='All':
				for name in familyList:
					if name == selectedFamilly:
						assetsPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+selectedCategory+'\\'+name
						getAssetsFiles = os.listdir(assetsPath)
						if len(getAssetsFiles)!= 0:
							for nameB in getAssetsFiles:
								currentAssetsPath = assetsPath+'\\'+nameB
								if self.getCategory() == defaultPrint:
									nameC = nameC = name+'\\'+nameB
									assetFiles.append(nameC)
								else:
									for nameC in os.listdir(currentAssetsPath):
										nameC = name+'\\'+nameB+'\\'+nameC
										assetFiles.append(nameC)
			else:
				for name in familyList:
					if name == selectedFamilly:
						assetsPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+selectedCategory+'\\'+name
						getAssetsFiles = os.listdir(assetsPath)
						if len(getAssetsFiles)!= 0:
							for nameB in getAssetsFiles:
								currentAssetsPath = assetsPath+'\\'+nameB
								if self.getCategory() == defaultPrint:
									nameC = nameC = name+'\\'+nameB
									assetFiles.append(nameC)
								else:
									for nameC in os.listdir(currentAssetsPath):
										if nameC == selectedDept:
											nameC = name+'\\'+nameB+'\\'+nameC
											assetFiles.append(nameC)
		for dept in assetFiles:
			if 'Comp' in dept:
				assetFiles.remove(dept)
		self.assetList.addItems(assetFiles)
		
	def openFile(self,file):
		keep = len(file)-len(tab)-10
		file = file[:keep]
		cmds.file( file, force=True, open=True )
		
	def importFile(self,file):
		keep = len(file)-len(tab)-10
		file = file[:keep]
		cmds.file( file, i=True )
		
		
	def referenceFile(self,file):
		keep = len(file)-len(tab)-10
		file = file[:keep]
		cmds.file( file, reference=True, ns='' )
		
	def catLabelToName(self,file):
		if file == labelLib:
			cat = defaultLib
		if file == labelFilm:
			cat = defaultFilm
		return cat
	
	#
	
	#Slots
	def checkFinalList(self):
		if self.editList.currentItem() and self.finalList.currentItem():
			self.editList.clear()
			selectedProject = self.projectList.currentText()
			projectPath = self.getProjectPath(selectedProject)
			selectedFamilly = self.familyList.currentText()
			selectedDept = self.deptList.currentText()
			selectedCategory = self.getCategory()
			selectedAsset = self.listToText(self.assetList.currentItem())
			finalPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+self.getCategory()+'\\'+selectedAsset
			editPath = finalPath+'\\Edit'
			finalListFiles = []		
			editListFiles = []
			for editFiles in os.listdir(editPath):
			    if editFiles.endswith(".ma") or editFiles.endswith(".mb"):
					date = self.getModifDate(editPath+'\\'+editFiles)        
					editListFiles.append(editFiles+tab+date)
			editListFiles = sorted(editListFiles, reverse=True)
			self.editList.addItems(editListFiles)
		self.refreshOpenButton()
		
	def checkEditList(self):
		if self.finalList.currentItem() and self.editList.currentItem():
			self.finalList.clear()
			selectedProject = self.projectList.currentText()
			projectPath = self.getProjectPath(selectedProject)
			selectedFamilly = self.familyList.currentText()
			selectedDept = self.deptList.currentText()
			selectedCategory = self.getCategory()
			selectedAsset = self.listToText(self.assetList.currentItem())
			finalPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+self.getCategory()+'\\'+selectedAsset
			editPath = finalPath+'\\Edit'
			finalListFiles = []	
			for finalFiles in os.listdir(finalPath):
			    if finalFiles.endswith(".ma") or finalFiles.endswith(".mb"):
					date = self.getModifDate(finalPath+'\\'+finalFiles)	        
					finalListFiles.append(finalFiles+tab+date)
			self.finalList.addItems(finalListFiles)
		self.refreshOpenButton()
				
	def refreshAssets(self):
		self.assetList.clear()
		self.listAssetsFiles()			
	
	def refreshEditRef(self):
		self.finalList.clear()
		self.editList.clear()
		selectedProject = self.projectList.currentText()
		projectPath = self.getProjectPath(selectedProject)
		selectedFamilly = self.familyList.currentText()
		selectedDept = self.deptList.currentText()
		selectedCategory = self.getCategory()
		selectedAsset = self.listToText(self.assetList.currentItem())
		finalPath = projectPath+'\\'+self.delLabel(selectedProject)+'\\'+self.getCategory()+'\\'+selectedAsset
		editPath = finalPath+'\\Edit'
		finalListFiles = []		
		editListFiles = []
		for finalFiles in os.listdir(finalPath):
		    if finalFiles.endswith(".ma") or finalFiles.endswith(".mb"):
				date = self.getModifDate(finalPath+'\\'+finalFiles)	        
				finalListFiles.append(finalFiles+tab+date)
				
		for editFiles in os.listdir(editPath):
		    if editFiles.endswith(".ma") or editFiles.endswith(".mb"):
				date = self.getModifDate(editPath+'\\'+editFiles)        
				editListFiles.append(editFiles+tab+date)
		editListFiles = sorted(editListFiles, reverse=True)
		self.finalList.addItems(finalListFiles)
		self.editList.addItems(editListFiles)
	
	''' CHECK RADIO BUTTON FUNCTION'''
	def checkRadio(self):
		if self.openRadio.isChecked():
			self.openButton.setText('Open')
		if self.importRadio.isChecked():
			self.openButton.setText('Import')
		if self.refRadio.isChecked():
			self.openButton.setText('Reference')
			
	''' GET CATEGORY FUNCTION'''
	def getCategory(self):
		self.familyList.setEnabled(True)				
		if self.libraryRadio.isChecked():
			selectedCategory = defaultLib			
		if self.filmRadio.isChecked():
			selectedCategory = defaultFilm			
		if self.printRadio.isChecked():
			self.familyList.setDisabled(True)
			selectedCategory = defaultPrint
		
		return selectedCategory
	
	def refreshOpenButton(self):
		if self.finalList.currentItem() and not self.editList.currentItem():
			self.openButton.setEnabled(True)			
		elif not self.finalList.currentItem() and self.editList.currentItem():
			self.openButton.setEnabled(True)		
		else:
			self.openButton.setDisabled(True)
	
	''' CLICK BUTTON FUNCTION'''
	def clickOpen(self):
		selectedProject = self.projectList.currentText()
		selectedCategory = self.getCategory()
		file = self.getProjectPath(selectedProject)+'\\'+self.delLabel(selectedProject)+'\\'+selectedCategory+'\\'+self.listToText(self.assetList.currentItem())
		if self.finalList.currentItem():
			file = file+'\\'+self.listToText(self.finalList.currentItem())
			
		if self.editList.currentItem():
			file = file+'\\Edit\\'+self.listToText(self.editList.currentItem())
			
		if self.openButton.text() == 'Open':
			if cmds.file(query = True, modified = True): 
				result = cmds.confirmDialog( title='Save Changes', message='Do you want to save your file?', button=['Oui','Non', 'Annuler'], defaultButton='Oui', cancelButton='Annuler', dismissString='Annuler' )
				if result == "Oui":					
					if unicode(cmds.file(q=True, sn=True)) =='':
						mel.eval('SaveSceneAs;')
					else:
						cmds.file(save= True)
					self.openFile(file)
					projectPath =  self.getProjectPath(selectedProject)+'\\'+self.delLabel(selectedProject)
					projectPath = '/'.join(projectPath.split('\\'))
					mel.eval('setProject "'+projectPath+'";')
				if result == "Non":
					self.openFile(file)
					projectPath =  self.getProjectPath(selectedProject)+'\\'+self.delLabel(selectedProject)
					projectPath = '/'.join(projectPath.split('\\'))
					mel.eval('setProject "'+projectPath+'";')
			else:    
				self.openFile(file)
				projectPath =  self.getProjectPath(selectedProject)+'\\'+self.delLabel(selectedProject)
				projectPath = '/'.join(projectPath.split('\\'))
				mel.eval('setProject "'+projectPath+'";')
			
		if self.openButton.text() == 'Import':
			self.importFile(file)			
			projectPath =  self.getProjectPath(selectedProject)+'\\'+self.delLabel(selectedProject)
			projectPath = '/'.join(projectPath.split('\\'))
			mel.eval('setProject "'+projectPath+'";')
			
		if self.openButton.text() == 'Reference':
			self.referenceFile(file)
			projectPath =  self.getProjectPath(selectedProject)+'\\'+self.delLabel(selectedProject)
			projectPath = '/'.join(projectPath.split('\\'))
			mel.eval('setProject "'+projectPath+'";')
	
	#
	
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
