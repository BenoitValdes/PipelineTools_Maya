###################################################
# File :    NamespaceManager.py
# Author :  Paul
# DoC :     31/07/2014
# LM :      31/07/2014
###################################################
import sys
import os
import json
sys.path.append("R:\\Benoit\\Scripts\\maya\\scripts")
import maya.cmds as cmds



class NamespaceManager:
    def __init__(self):
        
    
        #liste des attributs
        self.listNamespace = []
        self.listEmptyNamespace = []
        self.listSelectedNamespace = []
        
        
        #If the window already exists, erase it
        if cmds.window('InE_NSMWin', exists=True):
            cmds.deleteUI('InE_NSMWin')
        #Create the window
        #s : Can window be resized?
        #rtf : Resize to fit childrens?
        self.window = cmds.window('InE_NSMWin', title = "Namespace Manager", widthHeight=(520, 435), s = False, rtf=True)
        #Main layout
        cmds.formLayout("InE_NSMFlowLayout", p = 'InE_NSMWin', w = 50, h = 50)
        cmds.image(image="R:\Benoit\Scripts\maya\icons\NSMBackground.png")
        #Layout that draws an empty space at the top to see the beautyful flowers
        cmds.columnLayout('InE_NSMEmptyLayout', p = "InE_NSMFlowLayout", columnAttach=('both', 14), rowSpacing=5, columnWidth=520, cal="left"  )
        cmds.text(label = "", p = 'InE_NSMEmptyLayout')
        cmds.text(label = "", p = 'InE_NSMEmptyLayout')
        cmds.text(label = "", p = 'InE_NSMEmptyLayout')
        cmds.text(label = "", p = 'InE_NSMEmptyLayout')
        cmds.text(label = "", p = 'InE_NSMEmptyLayout')
        #Real main layout containing all the UI
        cmds.rowColumnLayout( 'InE_NSMMainLayout', p = "InE_NSMEmptyLayout", numberOfColumns=2, columnWidth=[(1, 300), (2, 190)], h = 330, ro = [[1, "both", 20], [2, "both", 10]], co = [[1, "both", 10], [2, "both", 0]])
        
        
        cmds.treeView('InE_NSMTextScrollList', parent = "InE_NSMMainLayout", numberOfButtons = 0, h= 150, abr = False, ams = True, adr = True, arp = True, idc = self.emptyMethod, sc = self.selectNamespace )
        cmds.treeView('InE_NSMTextScrollList', edit = True, enk = True)
        
        cmds.columnLayout('InE_NSMInformations', p = "InE_NSMMainLayout", columnAttach=('both', 0), cw = 250, rowSpacing=5, cal="left" , ebg = True)
        cmds.text(p = 'InE_NSMInformations', label = "Informations")
        cmds.text('InE_NSMNameInformations', p = 'InE_NSMInformations', label = "")
        cmds.text('InE_NSMEmptyInformations', p = 'InE_NSMInformations', label = "")
        
        cmds.columnLayout('InE_NSMModifications', p = "InE_NSMMainLayout", columnAttach=('both', 20), co = ("both", 10), cw = 250, rowSpacing=6, cal="left" , ebg = True)
        cmds.text(p = 'InE_NSMModifications', label = "Rename selected to: ")
        cmds.textField('InE_NSMNameInput', p = 'InE_NSMModifications')
        cmds.radioCollection('InE_NSMRadioCollection', p = 'InE_NSMModifications')
        cmds.radioButton('InE_NSMRadioButton1', label='and keep namespace hierarchy', select=True )
        cmds.radioButton('InE_NSMRadioButton2', label='and move namespace to root' )
        cmds.button('InE_NSMRenameSelected', p = 'InE_NSMModifications', label = "Rename selected", en = True, command = self.renameSelected)
        
        cmds.columnLayout('InE_NSMButtons', p = "InE_NSMMainLayout", columnAttach=('both', 20), co = ("both", 10), rowSpacing=23, cal="left" , ebg = True)
        cmds.button('InE_NSMRemoveSelected', p = 'InE_NSMButtons', label = "Remove selected", w = 128, en = True, command = self.removeSelected)
        cmds.button('InE_NSMRemoveEmpty', p = 'InE_NSMButtons', label = "Remove empty", w = 128, en = True, command = self.removeEmpty)
        cmds.button('InE_NSMRemoveAll', p = 'InE_NSMButtons', label = "Remove all", w = 128, en = True, command = self.removeAll)
        
        
        cmds.showWindow()   
        
        self.updateTreeView()
        print self.listNamespace
        
    def removeSelected(self, *args):
        for namespace in self.listSelectedNamespace:
            cmds.namespace( removeNamespace = namespace, mergeNamespaceWithRoot = True)
        del self.listSelectedNamespace[:]
        self.updateTreeView()
            
    def removeEmpty(self, *args):
        self.retrieveListEmptyNamespaces(":")
        for namespace in self.listEmptyNamespace:
            cmds.namespace( removeNamespace = namespace, mergeNamespaceWithRoot = True)
        self.updateTreeView()
        
    def removeAll(self, *args):
        self.retrieveListNamespaces(":")
        for namespace in self.listNamespace:
            try:
                cmds.namespace( removeNamespace = namespace, mergeNamespaceWithRoot = True)
            except: 
                print "Impossible de supprimer " + namespace + ", il a surement deja ete supprime."
        self.updateTreeView()
        
    def renameSelected(self, *args):
        inputValue = cmds.textField('InE_NSMNameInput', query=True, text=True)
        if cmds.radioButton('InE_NSMRadioButton2', query=True, select=True ):
            cmds.namespace(add=inputValue,force=True)
            cmds.namespace( mv=[self.listSelectedNamespace[0], inputValue], force = True)
        else:
            parentNs = ":".join(self.listSelectedNamespace[0].split(":")[0:-1])
            if parentNs == "": parentNs = ":"
            cmds.namespace( ren=[self.listSelectedNamespace[0], inputValue], parent=parentNs, force=True)
            
        del self.listSelectedNamespace[:]
        self.updateTreeView()
        
    def retrieveListNamespaces(self, root):
        del self.listNamespace[:]
        listNs = cmds.namespaceInfo(root, listOnlyNamespaces=True, recurse = True )
        if listNs != None:
            for namespace in listNs:
                if namespace != "UI" and namespace != "shared":
                    self.listNamespace.append(namespace)
        
    def retrieveListEmptyNamespaces(self, root):
        del self.listEmptyNamespace[:]
        listNs = cmds.namespaceInfo(root, listOnlyNamespaces=True, recurse = True )
        if listNs != None:
            for namespace in listNs:
                if namespace != "UI" and namespace != "shared":
                    if cmds.namespaceInfo(namespace, listNamespace=True ) == None:
                        self.listEmptyNamespace.append(namespace)
        
    def updateTreeView(self):
        cmds.treeView( 'InE_NSMTextScrollList', edit=True, removeAll = True )
        self.retrieveListNamespaces(":")
        
        for namespace in self.listNamespace:
            if ":" in namespace:
                cmds.treeView( 'InE_NSMTextScrollList', e=True, addItem = (namespace, ":".join(namespace.split(":")[0:-1]) ))
            else:
                cmds.treeView( 'InE_NSMTextScrollList', e=True, addItem = (namespace, ""))
        
    def emptyMethod(self, *args):
        a=0
        
    def selectNamespace(self, *args):
        if args[1] == 1:
            self.listSelectedNamespace.append(args[0])
        else:
            self.listSelectedNamespace.remove(args[0])
        
        cmds.text('InE_NSMNameInformations', e=True, label = "Name: " + args[0])
        if cmds.namespaceInfo(args[0], listNamespace=True ) == None:
            cmds.text('InE_NSMEmptyInformations', edit = True, label = "Empty: Yes")
        else:
            cmds.text('InE_NSMEmptyInformations', edit = True, label = "Empty: No")
        return True