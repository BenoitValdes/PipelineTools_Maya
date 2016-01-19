# 
# Author: Fredrik Averpil, fredrik.averpil@gmail.com, http://fredrikaverpil.tumblr.com
# 

# -*- coding: utf8 -*-

''' Imports regardless of Qt type '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''
import os, sys
import xml.etree.ElementTree as xml
from cStringIO import StringIO

''' CONFIGURATION '''
''' --------------------------------------------------------------------------------------------------------------------------------------------------------- '''

# General
QtType = 'PySide'										# Edit this to switch between PySide and PyQt
sys.dont_write_bytecode = True									# Do not generate .pyc files
uiFile = os.path.join(os.path.dirname(__file__), 'UI/MirorBlendShape.ui')				# The .ui file to load
windowTitle = 'Mirror Blenshape'									# The visible title of the window
windowObject = 'mirror_blendshape'									# The name of the window object

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
		
		# Windows creation
		self.setObjectName(windowObject)
		self.setWindowTitle(windowTitle)
		#
		
		# Init
		self.runButton.setDisabled(True)
		#
		
		# Signals
		self.originalButton.clicked.connect(self.addOriginal)
		self.blendButton.clicked.connect(self.addBlend)
		self.delButton.clicked.connect(self.delBlend)
		self.runButton.clicked.connect(self.runScript)
		#
		
	#Slots
	def runScript(self):
		originalMesh = self.originalInput.text() # Get original Mesh
		blendShapesList = []
		allBlendShapeList = []
		
		# List all blendshapes mesh added
		for index in xrange(self.blendList.count()):
			selectedItem = self.blendList.item(index)
			blendShapesList.append(selectedItem.text())
		
		# Create hierarchy
		cmds.group( em=True, name='Geometry' )
		cmds.group( em=True, name='Deformers' )
		cmds.group( em=True, name='Blendshapes' )
		cmds.group( em=True, name='Wraps' )
		cmds.parent(originalMesh, 'Geometry')
		cmds.parent( 'Blendshapes', 'Wraps', 'Deformers' )
		cmds.parent( 'Deformers', 'Geometry' )
		cmds.hide('Deformers')
		
		# Create the mirrored Blendshape mesh
		for blendShapes in blendShapesList:
			cmds.duplicate(originalMesh, name=blendShapes+'_Mirored')
			cmds.duplicate(blendShapes+'_Mirored', name=blendShapes+'_Inverted')
			cmds.blendShape(blendShapes, blendShapes+'_Inverted', name=blendShapes+'_Inverted_Node')			
			cmds.select(blendShapes+'_Inverted', blendShapes+'_Mirored')
			cmds.move(10,0,10)
			cmds.select(blendShapes+'_Inverted')
			if self.scaleXRadio.isChecked():
				cmds.scale(-1,1,1)
			elif self.scaleYRadio.isChecked():
				cmds.scale(1,-1,1)
			elif self.scaleZRadio.isChecked():
				cmds.scale(1,1,-1)
			cmds.select(cl=True)
			self.createWrap(blendShapes+'_Inverted', blendShapes+'_Mirored')
			cmds.blendShape( blendShapes+'_Inverted_Node', edit=True, w=[(0, 1)] )		
			cmds.parent(blendShapes,'Blendshapes')		
			cmds.parent(blendShapes+'_Mirored','Blendshapes')
			cmds.parent(blendShapes+'_Inverted','Blendshapes')			
			cmds.hide(blendShapes+'_Inverted')
			cmds.parent( blendShapes+'_InvertedBase', 'Wraps' )
			allBlendShapeList.append(blendShapes)
			allBlendShapeList.append(blendShapes+'_Mirored')
		
		# Apply all blendshapes on the original mesh
		cmds.select(allBlendShapeList, originalMesh)
		cmds.blendShape(cmds.ls(selection=True))
	
	# check if mesh can be added in "original" input
	def addOriginal(self):
		if cmds.ls( selection=True, tail=1 ):
			items = []
			for index in xrange(self.blendList.count()):
				selectedItem = self.blendList.item(index)
				items.append(selectedItem.text())
			for object in cmds.ls(selection=True):
				if not object in items:
					self.originalInput.setText(cmds.ls( selection=True, tail=1 )[0])
		self.checkRunButton()
	
	# check if mesh can be added in "blendshape" list
	def addBlend(self):
		if cmds.ls(selection=True):
			items = [self.originalInput.text()]
			for index in xrange(self.blendList.count()):
				selectedItem = self.blendList.item(index)
				items.append(selectedItem.text())
			for object in cmds.ls(selection=True):
				if not object in items:
					self.blendList.addItem(object)
		self.checkRunButton()
	
	# Remove a blendshape mesh from the list
	def delBlend(self):
		listSelected = cmds.ls(selection = True)
		listQList = []
		for i in range(self.blendList.count()):
			listQList.append( self.blendList.item(i) )			
		newList = [item for item in listQList if item.text() in listSelected]		
		for item in newList:
			self.blendList.takeItem(self.blendList.row(item))
		
		self.checkRunButton()
	
	#Functions
	
	# Check if the ren button can be enabled or not
	def checkRunButton(self):
		self.runButton.setDisabled(True)
		if self.originalInput.text() and xrange(self.blendList.count()):
			self.runButton.setEnabled(True)
	
	# Wrap function
	def createWrap(self,*args,**kwargs):
		influence=args[0]
		surface = args[1]
		
		shapes = cmds.listRelatives(influence,shapes=True)
		influenceShape = shapes[0]
	 
		shapes = cmds.listRelatives(surface,shapes=True)
		surfaceShape = shapes[0]
	 
		#create wrap deformer
		weightThreshold = kwargs.get('weightThreshold',0.0)
		maxDistance = kwargs.get('maxDistance',1.0)
		exclusiveBind = kwargs.get('exclusiveBind',False)
		autoWeightThreshold = kwargs.get('autoWeightThreshold',True)
		falloffMode = kwargs.get('falloffMode',0)
	 
		wrapData = cmds.deformer(surface, type='wrap')
		wrapNode = wrapData[0]
	 
		cmds.setAttr(wrapNode+'.weightThreshold',weightThreshold)
		cmds.setAttr(wrapNode+'.maxDistance',maxDistance)
		cmds.setAttr(wrapNode+'.exclusiveBind',exclusiveBind)
		cmds.setAttr(wrapNode+'.autoWeightThreshold',autoWeightThreshold)
		cmds.setAttr(wrapNode+'.falloffMode',falloffMode)
	 
		cmds.connectAttr(surface+'.worldMatrix[0]',wrapNode+'.geomMatrix')
		
		#add influence
		duplicateData = cmds.duplicate(influence,name=influence+'Base')
		base = duplicateData[0]
		shapes = cmds.listRelatives(base,shapes=True)
		baseShape = shapes[0]
		cmds.hide(base)
		
		#create dropoff attr if it doesn't exist
		if not cmds.attributeQuery('dropoff',n=influence,exists=True):
			cmds.addAttr( influence, sn='dr', ln='dropoff', dv=4.0, min=0.0, max=20.0  )
			cmds.setAttr( influence+'.dr', k=True )
		
		#if type mesh
		if cmds.nodeType(influenceShape) == 'mesh':
			#create smoothness attr if it doesn't exist
			if not cmds.attributeQuery('smoothness',n=influence,exists=True):
				cmds.addAttr( influence, sn='smt', ln='smoothness', dv=0.0, min=0.0  )
				cmds.setAttr( influence+'.smt', k=True )
	 
			#create the inflType attr if it doesn't exist
			if not cmds.attributeQuery('inflType',n=influence,exists=True):
				cmds.addAttr( influence, at='short', sn='ift', ln='inflType', dv=2, min=1, max=2  )
	 
			cmds.connectAttr(influenceShape+'.worldMesh',wrapNode+'.driverPoints[0]')
			cmds.connectAttr(baseShape+'.worldMesh',wrapNode+'.basePoints[0]')
			cmds.connectAttr(influence+'.inflType',wrapNode+'.inflType[0]')
			cmds.connectAttr(influence+'.smoothness',wrapNode+'.smoothness[0]')
	 
		#if type nurbsCurve or nurbsSurface
		if cmds.nodeType(influenceShape) == 'nurbsCurve' or cmds.nodeType(influenceShape) == 'nurbsSurface':
			#create the wrapSamples attr if it doesn't exist
			if not cmds.attributeQuery('wrapSamples',n=influence,exists=True):
				cmds.addAttr( influence, at='short', sn='wsm', ln='wrapSamples', dv=10, min=1  )
				cmds.setAttr( influence+'.wsm', k=True )
	 
			cmds.connectAttr(influenceShape+'.ws',wrapNode+'.driverPoints[0]')
			cmds.connectAttr(baseShape+'.ws',wrapNode+'.basePoints[0]')
			cmds.connectAttr(influence+'.wsm',wrapNode+'.nurbsSamples[0]')
	 
		cmds.connectAttr(influence+'.dropoff',wrapNode+'.dropoff[0]')
	
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
