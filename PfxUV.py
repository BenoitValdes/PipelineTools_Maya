import maya.OpenMaya as om
import maya.cmds as mc
import random

'''
pfxUVs.py

author:     David Johnson
contact:    david@djx.com.au
web:        http://www.djx.com.au

version:    1.4
date:       27 March 2011

Description:
    Script is for automatically laying out uv's for meshes created by converting paintFX to polys
    By default the uv's for leaves and grass are the same for each leaf or blade and unitized.
    By offsetting and scaling the uv's for each shell it is possible to create a fileTexture with
    a number of variations and have these randomly distributed to the leaves or blades.
    Can either be run from the UI or directly as a command (marking menu or shelf)
    
    layoutUI()    create UI
    leafLayout()  lays out leaf uvs into tiles in a 2x2, 3x3, or 4x4 array
    grassLayout() lays out grass blades uv's in thin strips, randomly placed along u  
'''
#........................................................................................................

def layoutUI():
    # build UI
    windowName = 'pfxUVsLayoutUI'
    windowTitle = 'djPFXUVs Layout'
    
    if mc.window(windowName, exists=True):
        mc.deleteUI(windowName, window=True)
    
    mc.window(windowName, title=windowTitle)
    mc.columnLayout(columnAttach=("both", 5), rowSpacing=10, columnWidth=400)
    mc.rowColumnLayout( numberOfColumns=2, columnWidth=[(1, 100),(2, 220)], columnAttach=[(1, 'both', 5), (2, 'both', 0)], columnAlign=[(1,'left'),(2,'left')])
    
    # uv set dropdown menu           
    mc.text( label='UV Set <source>')
    mc.optionMenu('UVSetSourceSelection', label='', cc=pfxUVSetSourceCC)
    
    mc.text( label='UV Set <target>')
    mc.optionMenu('UVSetTargetSelection', label='', cc=pfxUVSetTargetOptionVar)
    
    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns=2, columnWidth=[(1, 100),(2, 100)], columnAttach=[(1, 'both', 5), (2, 'both', 0)], columnAlign=[(1,'left'),(2,'left')])

    # layout types
    mc.text( label='UV Layout Type')
    mc.optionMenu('UVLayout', label='', cc=pfxUVLayoutSetOptionVar)
    
    # layout options
    mc.text( 'UVLayoutParam1Text', label='')
    mc.floatField('UVLayoutParam1Val', minValue=0, maxValue=0.05, precision=3, value=0, cc=pfxUVLAyoutParam1SetOptionVar)
    
    mc.setParent('..')

    # doIt button
    mc.button('pfxUVDoItButton', label='', command=pfxUVLayoutDoIt, h=50)
        
    # fill in the blanks
    refreshWindow()
    
    # create scriptJob to refresh UI if selection changes
    mc.scriptJob(parent=windowName, event=['SelectionChanged',refreshWindow] )

    mc.showWindow(windowName)
    
#........................................................................................................
def refreshWindow():
    
    # clear the existing menu items
    menus = ('UVSetSourceSelection', 'UVSetTargetSelection', 'UVLayout')
    for m in menus:
        menuItems = mc.optionMenu(m,q=True,ill=True)
        if menuItems is not None:
            mc.deleteUI( menuItems, mi=True)
            
    # rebuild 'UVSetSourceSelection'
    selList = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(selList)
    uvSets = getUVSets(selList)
    for s in uvSets:
        mc.menuItem( parent=menus[0], label=s  )    
    if len(uvSets)>1:
        mc.menuItem( parent=menus[0], label='<All>' )
        
    # rebuild 'UVSetTargetSelection' (build drop-down later - depends on source)
    mc.menuItem( parent=menus[1], label='<source>'  )    
 
    # rebuild 'UVLayout'
    layoutList = ('2x2', '3x3', '4x4', 'grass')
    for layout in layoutList:
        mc.menuItem( parent=menus[2], label=layout )    
    
    # apply prefs
    if len(uvSets):
        if mc.optionVar(exists='pfxUVSetSource'):
            pref_uvSet = mc.optionVar(q='pfxUVSetSource')
            if pref_uvSet=='<All>' and len(uvSets)>1:
                i=len(uvSets)+1
            else:
                i = pfxUVMenuArrayIndex(pref_uvSet,uvSets)
            mc.optionMenu(menus[0], edit=True, sl=i)
            
        # now build target drop-down            
        if mc.optionMenu(menus[0], q=True, v=True)=='<All>':
            # <All> is a special case where target must be source uv set
            mc.optionMenu(menus[1], edit=True, sl=1)
            mc.optionMenu(menus[1], edit=True, enable=False)
        else:
            mc.optionMenu(menus[1], edit=True, enable=True)
            for s in uvSets:
                mc.menuItem( parent=menus[1], label=s  )    
            mc.menuItem( parent=menus[1], label='<NEW>'  )    
            if mc.optionVar(exists='pfxUVSetTarget'):
                pref_uvSet = mc.optionVar(q='pfxUVSetTarget')
                if pref_uvSet=='<NEW>':
                    i=len(uvSets)+1
                else:
                    i = pfxUVMenuArrayIndex(pref_uvSet,uvSets)
                mc.optionMenu(menus[1], edit=True, sl=i)
            
    if mc.optionVar(exists='pfxUVLayout'):
        pref_uvLayout = mc.optionVar(q='pfxUVLayout')
        i = pfxUVMenuArrayIndex(pref_uvLayout,layoutList)
        mc.optionMenu(menus[2], edit=True, sl=i)
    else:
        pref_uvLayout = '2x2'
            
    refreshLayoutParam1(pref_uvLayout)
    
    # doIt button
    if selList.length():
        doItLabel = 'Layout UVs'
        doItState = True
        doItBgc = (0.6, 0.7, 0.6)
    else:
        doItLabel = '::: You need to select at least 1 poly mesh :::'
        doItState = False
        doItBgc = (0.7, 0.7, 0.5)
    
    mc.button('pfxUVDoItButton', edit=True, label=doItLabel, bgc=doItBgc, enable=doItState )

            
#........................................................................................................
def refreshLayoutParam1(layout):
    mc.text( 'UVLayoutParam1Text', edit=True, label=layoutParam1Text(layout))
    mc.floatField('UVLayoutParam1Val', edit=True, v=pfxUVLAyoutParam1GetOptionVar(layout))
    
#........................................................................................................
def layoutParam1Text(layout='2x2'):
    t = ''
    if layout == '2x2' or layout == '3x3' or layout == '4x4':
        t = 'tile separation'
    elif layout == 'grass':
        t = 'blade width'
    return t

#........................................................................................................
# get menu choices and launch 
def pfxUVLayoutDoIt(*args):
    refresh = 0
    
    # uvset is one or all
    uvSetSource = mc.optionMenu('UVSetSourceSelection', q=True, v=True)
    uvSetTarget = mc.optionMenu('UVSetTargetSelection', q=True, v=True)
    
    # get new target uv set name
    if uvSetTarget == '<NEW>':
        result = mc.promptDialog(title='New Target UV Set Name',
                message='Enter Name: ',
                text='%s_copy' % uvSetSource,
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')

        if result == 'OK':
            uvSetTarget = mc.promptDialog(query=True, text=True)
            refresh +=1
        else:
            print '    chickened out before doing anything'
            return
    
    # layout
    layout = mc.optionMenu('UVLayout', q=True, v=True)
    
    # param1
    param1 = mc.floatField('UVLayoutParam1Val', q=True, v=True)
    
    # layout uv's
    if layout == 'grass':
        grassLayout(uvSetSource, param1, uvSetTarget)
    else:
        leafLayout(uvSetSource, float(layout[0]), param1, uvSetTarget)
        
    # new uv sets
    if refresh:
        refreshWindow()

#........................................................................................................
def pfxUVSetCopy(uvSetSource='map1', uvSetTarget='map2'):
    pass

#........................................................................................................
def getUVSets(selList):   
    ''' get list of all possible uv sets from selected objects shapeNodes '''
    uvSets = []
    pathToShape = om.MDagPath()
    selListIter = om.MItSelectionList(selList, om.MFn.kMesh)
    while not selListIter.isDone():
        pathToShape = om.MDagPath()
        print '    %s' % pathToShape.partialPathName()
        selListIter.getDagPath(pathToShape)
        shapeFn = om.MFnMesh(pathToShape)
        uvSetsThisMesh = []
        shapeFn.getUVSetNames(uvSetsThisMesh)
        
        for s in uvSetsThisMesh:
            if s not in uvSets:
                uvSets.append(s)
                
        selListIter.next()
        
    return uvSets

#........................................................................................................
# menu change commands
def pfxUVSetSourceCC(uvSet):
    pfxUVSetSourceOptionVar(uvSet)
    refreshWindow()

#........................................................................................................
# optionVars handlers
#
def pfxUVSetSourceOptionVar(uvSet):
    mc.optionVar(sv=('pfxUVSetSource', uvSet))

def pfxUVSetTargetOptionVar(uvSet):
    mc.optionVar(sv=('pfxUVSetTarget', uvSet))

def pfxUVLayoutSetOptionVar(uvLayout):
    mc.optionVar(sv=('pfxUVLayout', uvLayout))
    refreshLayoutParam1(uvLayout)
    
def pfxUVLAyoutParam1SetOptionVar(val):
    layoutParamText = mc.text( 'UVLayoutParam1Text', q=True, label=True)
    if layoutParamText == 'tile separation':
        mc.optionVar(fv=('pfxUVTileSeparation', val))
    elif layoutParamText == 'blade width':
        mc.optionVar(fv=('pfxUVBladeWidth', val))

def pfxUVLAyoutParam1GetOptionVar(layout):
    v = 0.0
    if layout == '2x2' or layout == '3x3' or layout == '4x4':
        if mc.optionVar(exists='pfxUVTileSeparation'):
            v = mc.optionVar(q='pfxUVTileSeparation')
    elif layout == 'grass':
        if mc.optionVar(exists='pfxUVBladeWidth'):
            v = mc.optionVar(q='pfxUVBladeWidth')
    return v
#........................................................................................................
def pfxUVMenuArrayIndex(item, list):
    # menu item lists are 1 based
    try:
        i=list.index(item) + 1
    except:
        i=1
        
    return i

#........................................................................................................
# compute constants for the leaf layout math
def leafLayoutConstants(subdivs, separation):
    
    s = 1.0/subdivs - separation    # scale
    x = (1-s)/2                     # pivot back to 0.5,0.5 after scale
    o = {2:1.0/(subdivs*2), 3:1.0/subdivs, 4:1.0/(subdivs*2)}
    
    # build cell offset table (there's gotta be a better way!)
    if subdivs == 2:
        cellOffsets = ((-o[2],-o[2]), (o[2],-o[2]), (-o[2],o[2]), (o[2],o[2]))
    elif subdivs == 3:
        cellOffsets = ((-o[3],-o[3]), (0,-o[3]), (o[3],-o[3]), (-o[3],0), (0,0), (o[3],0), (-o[3],o[3]), (0,o[3]), (o[3],o[3]))
    elif subdivs == 4:
        cellOffsets = ((-3*o[4],-3*o[4]), (-o[4],-3*o[4]), (o[4],-3*o[4]), (3*o[4],-3*o[4]), (-3*o[4],-o[4]), (-o[4],-o[4]), (o[4],-o[4]), (3*o[4],-o[4]), (-3*o[4],o[4]), (-o[4],o[4]), (o[4],o[4]), (3*o[4],o[4]), (-3*o[4],3*o[4]), (-o[4],3*o[4]), (o[4],3*o[4]), (3*o[4],3*o[4]))

    return s,x,cellOffsets

#........................................................................................................
def leafLayout(uvSet='map1', subdivs=3, sep=0.01, uvSetTarget='<source>'):
    '''
    leafLayout(uvSet, subdivs, separation [,uvSetTarget])
        Scale and offset the shell uvs from uvSet into the number of tiles defined by subdivs and separation
        If uvSet == '<All>' then process all uvsets.
        subdivs can be 2, 3 or 4, resulting in 4, 9 or 16 tiles
        separation, the distance between tiles, should be between 0 and 0.1 (large values will create strange layouts)
    '''
    
    print '%s leafLayout start' % (__name__)
    
    # check arguments
    if subdivs not in [2,3,4]:
        print 'subdivs=%i not valid. Must be 2, 3 or 4.' % (subdivs)
        return
    
    f = -1
    if sep<0:
        f=0
    elif sep>0.05:
        f=0.05
    if f != -1:
        print 'sep=%d outside range 0 to 0.05 Using %d' % (sep,f)
        sep=f     
    
    # get the constants for the layout math
    s, x, cellOffsets = leafLayoutConstants(subdivs, sep)
    
    # step through the objects in selection list
    selList = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(selList)
        
    if selList.isEmpty():
        print '    Nothing selected. Select a poly mesh and try again'
        return

    selListIter = om.MItSelectionList(selList, om.MFn.kMesh)
    
    while not selListIter.isDone():
        pathToShape = om.MDagPath()
        selListIter.getDagPath(pathToShape)
        shapeFn = om.MFnMesh(pathToShape)
        
        uvShellArray = om.MIntArray()
        uArray = om.MFloatArray()
        vArray = om.MFloatArray()
        
        shells = om.MScriptUtil()
        shells.createFromInt(0)
        shellsPtr = shells.asUintPtr()
    
        print '    %s' % pathToShape.partialPathName()
        
        # check specified uvSet exists on this mesh
        uvSets = []
        shapeFn.getUVSetNames(uvSets)
        if uvSet != '<All>':
            if uvSet in uvSets and shapeFn.numUVs(uvSet):
                if uvSetTarget != '<source>' and uvSetTarget != uvSet:
                    uvSet = shapeFn.copyUVSetWithName(uvSet, uvSetTarget)
                uvSets = [uvSet]                
            else:
                print '        **** uv set %s not found.' % (uvSet)
                print ''
                selListIter.next()
                continue
              
        uvSetsString=''
        for uvs in uvSets:
            uvSetsString += uvs + ', '
        print '        uvSets: %s' % (uvSetsString[:-2])
        print ''
        
        # remember current uv set
        currentUVSet = shapeFn.currentUVSetName()
    
        for thisUVSet in uvSets:
            # thisUVSet needs to be current
            shapeFn.setCurrentUVSetName(thisUVSet)   
            
            print '        %s' % (thisUVSet)
            shapeFn.getUvShellsIds(uvShellArray, shellsPtr, thisUVSet)
            print '            %s shells' % shells.getUint(shellsPtr)
            
            shapeFn.getUVs(uArray, vArray, thisUVSet)
            print '            %s uvs' % uArray.length()
            
            uvDict = {}
            uvOffDict = {}
            for i in range(uArray.length()):
                if not uvShellArray[i] in uvDict:
                    uvOffDict[uvShellArray[i]] = random.randint(0,pow(subdivs,2)-1)
                    uvDict[uvShellArray[i]] = [i]
                else:
                    uvDict[uvShellArray[i]].append(i)
                
            # compute the new uv's                    
            for i in range(shells.getUint(shellsPtr)):
                for j in uvDict[i]:
                    uArray.set((x + uArray[j]*s + cellOffsets[uvOffDict[i]][0]),j)
                    vArray.set((x + vArray[j]*s + cellOffsets[uvOffDict[i]][1]),j)
                
            # write new uv's
            shapeFn.setUVs(uArray, vArray, thisUVSet)
            print '            done'
            print ''
            
            uvShellArray.clear()
            uArray.clear()
            vArray.clear()
        
        # restore current uv set       
        shapeFn.setCurrentUVSetName(currentUVSet)   
     
        selListIter.next()
        print ''
    
    print '%s leafLayout done\n' % (__name__)
      
#........................................................................................................
def grassLayout(uvSet='map1', bladeWidth=0.01, uvSetTarget='<source>'):
    '''   
    grassLayout(uvSet, bladeWidth [,uvSetTarget])
        Scales the uv's so each blade covers a strip specified by bladeWidth
        Offsets each shell randomly along u
    '''
    
    print '%s grassLayout start' % (__name__)

    # validate arguments
    f = -1
    if bladeWidth<0:
        f=0
    elif bladeWidth>0.5:
        f=0.5
    if f != -1:
        print 'bladeWidth=%d outside valid range 0 to 0.5 Using %d' % (bladeWidth,f)
        bladeWidth=f     

    x = (1-bladeWidth)/2

    selList = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(selList)
    if selList.isEmpty():
        print '    Nothing selected. Select a poly mesh and try again'
        return

    selListIter = om.MItSelectionList(selList, om.MFn.kMesh)
    
    while not selListIter.isDone():
        pathToShape = om.MDagPath()
        selListIter.getDagPath(pathToShape)
        shapeFn = om.MFnMesh(pathToShape)
        
        uvShellArray = om.MIntArray()
        uArray = om.MFloatArray()
        vArray = om.MFloatArray()
        
        shells = om.MScriptUtil()
        shells.createFromInt(0)
        shellsPtr = shells.asUintPtr()
    
        print '    %s' % pathToShape.partialPathName()
        
        # check specified uvSet exists on this mesh
        uvSets = []
        shapeFn.getUVSetNames(uvSets)
        if uvSet != '<All>':
            if uvSet in uvSets and shapeFn.numUVs(uvSet):
                if uvSetTarget != '<source>' and uvSetTarget != uvSet:
                    uvSet = shapeFn.copyUVSetWithName(uvSet, uvSetTarget)
                uvSets = [uvSet]                
            else:
                print '        **** uv set %s not found.' % (uvSet)
                print ''
                selListIter.next()
                continue
              
        uvSetsString=''
        for uvs in uvSets:
            uvSetsString += uvs + ', '
        print '        uvSets: %s' % (uvSetsString[:-2])
        print ''
        
        # remember current uv set
        currentUVSet = shapeFn.currentUVSetName()
    
        for thisUVSet in uvSets:
            # thisUVSet needs to be current
            shapeFn.setCurrentUVSetName(thisUVSet)   
            
            print '        %s' % (thisUVSet)
            shapeFn.getUvShellsIds(uvShellArray, shellsPtr, thisUVSet)
            print '            %s shells' % shells.getUint(shellsPtr)
            
            shapeFn.getUVs(uArray, vArray, thisUVSet)
            print '            %s uvs' % uArray.length()
            
            uvDict = {}
            uvOffDict = {}
            for i in range(uArray.length()):
                if not uvShellArray[i] in uvDict:
                    uvOffDict[uvShellArray[i]] = random.uniform(-x,x)
                    uvDict[uvShellArray[i]] = [i]
                else:
                    uvDict[uvShellArray[i]].append(i)
            
            # compute the new u's                  
            for i in range(shells.getUint(shellsPtr)):
                for j in uvDict[i]:
                    uArray.set((x + uArray[j]*bladeWidth + uvOffDict[i]),j)
              
            # write new u's  
            shapeFn.setUVs(uArray, vArray, thisUVSet)
            print '            done'
            print ''
            
            uvShellArray.clear()
            uArray.clear()
            vArray.clear()
        
        # restore current uv set       
        shapeFn.setCurrentUVSetName(currentUVSet)   
     
        selListIter.next()
        print ''
    
    print '%s grassLayout end\n' % (__name__)
    
#........................................................................................................
