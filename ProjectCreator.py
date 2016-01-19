# 
# Author: Benoit Valdes, valdes.benoit@gmail.com, http://www.benoitvaldes.com
# 

# -*- coding: utf8 -*-

''' Imports regardless of Qt type '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
import os, sys
import xml.etree.ElementTree as xml
from cStringIO import StringIO
import maya.cmds as cmds
from config import *
import shutil


''' CONFIGURATION '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''

# General
QtType = 'PySide'										# Edit this to switch between PySide and PyQt
sys.dont_write_bytecode = True									# Do not generate .pyc files
uiFile = os.path.join(os.path.dirname(__file__), 'UI/ProjectCreator.ui')				# The .ui file to load
windowTitle = 'Project Creator'									# The visible title of the window
windowObject = 'projectCreator'									# The name of the window object

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
		
		#Create and input start value in the form
		if not path2:
			self.serverRadio.setDisabled(True)
		self.createButton.setDisabled(True)	
		self.projectInput.textChanged.connect(self.createProjectButton)
		#
		
		#Signals 
		self.createButton.clicked.connect(self.createProject)
		#
			
	#Function to enable 'CREATE' button if all input arnt' empty
	def createProjectButton(self):
		if self.projectInput.text():
			self.createButton.setEnabled(True)
		else:
			self.createButton.setDisabled(True)		
	#
	
	#Function to create the project	
	def createProject(self):
		selectedPath = path1		#Default project path is the path1
		if self.serverRadio.isChecked():
			selectedPath = path2		#If 'Server' is checked project path become 'Server'
			
		os.chdir(selectedPath)		#Go in the project path directory to work
		
		if os.path.isdir(self.projectInput.text()):		#If the Project name already exist prompt:
			cmds.confirmDialog(title='Alert', message='Project already exist')
			mkdir = False
			
		else:										#Else create the Project
			try:
				os.mkdir(self.projectInput.text())
				os.chdir(selectedPath+'\\'+self.projectInput.text())
				os.mkdir(defaultLib)
				os.mkdir(defaultFilm)
				os.mkdir(defaultPrint)
				os.mkdir('SOURCES')
				os.mkdir('REVIEW')
				os.mkdir('TMP')
				f = open('projectSettings', 'w')	#If the project has not this file it will not be loaded in the Project Opener
				f.write('project = True')			#This variable enable or not the loading of the project in the Project Opener by default the project is visible
				f.close()
				print selectedPath+'\\'+self.projectInput.text()+'\\'+workspaceTemplate
				src = templatePath+'\\'+workspaceTemplate	
				dst = selectedPath+'\\'+self.projectInput.text()+'\\'+workspaceTemplate
				shutil.copy(src,dst)
				#shutil.copy(templatePath+'\\'+workspaceTemplate,selectedPath+'\\'+self.projectInput.text()+'\\'+workspaceTemplate)
				os.chdir(defaultLib)
				for family in libFamilyList:
					os.mkdir(family)
				os.chdir(selectedPath+'\\'+self.projectInput.text()+'\\TMP')
				os.mkdir('Caches')
				os.mkdir('Autosave')
				mkdir = True
			except:
				cmds.confirmDialog(title='Alert', message='Sorry something wrong happend, the project hasn\'t been created')	#If something wrong happend prompt 
				mkdir = False
	
		if cmds.window(windowObject, exists=True) and mkdir:
			cmds.deleteUI(windowObject)
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
