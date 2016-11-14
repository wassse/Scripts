import maya.cmds as cmds
import maya.OpenMaya as om
from functools import partial

gStepSize = 1

def UI():
    
    if cmds.window("vertexAnimToolUI", exists = True):
        cmds.deleteUI("vertexAnimToolUI")
    
    window = cmds.window( "vertexAnimToolUI", title = "Vertex Animation Tool", w = 200, h = 125, mnb = False, mxb = False, sizeable = True, titleBarMenu = True, menuBar = True)
    mainLayout = cmds.columnLayout(w = 200, h = 125)
    cmds.separator(height = 5)
    rowLayout = cmds.rowColumnLayout(nc = 1)
    
    #Buttons
    timelineButton = cmds.button(label = "Timeline", w = 200, h = 40, c = vertexAnimTimeline)
    cmds.separator(height = 3, style = "none")
    multipleObjButton = cmds.button(label = "Multiple Objects", w = 200, h = 40, c = vertexAnimSimple)
    cmds.separator(height = 3, style = "none")
    
    #StepSize Textfield
    cmds.rowColumnLayout( numberOfColumns=2, columnAttach=(1, 'right', 0), columnWidth=[(1, 100), (2,30)])
    cmds.text( label='Step Size' )
    inputField = cmds.textField("inputField", width = 30, text = gStepSize)
    
    #HELP MENU AND ABOUT
    helpMenu = cmds.menu("helpMenu", helpMenu = True, l = "Help", parent = "vertexAnimToolUI")
    menuItem = cmds.menuItem(l = "Help", c=r"cmds.confirmDialog(messageAlign='left', title='Help" + r"', button = 'Accept', defaultButton='Accept',message='\
    \n Animation Timeline \
    \n 1. Set the range slider to start and finish of the animation.  \
    \n 3. Select one or more meshes animated on the timeline, with or without skeleton. \
    \n 4. Click the Timeline button and wait. Open log to watch progress if you want. \
    \n 5. Import mesh to UE4 \
    \n \
    \n Frame by Frame \
    \n 2. Select meshes in the order that you want them to appear in the animation \
    \n 3. Click Multiple Objects Button \
    \n 4. Import mesh to UE4 \
    \n \
    \n IMPORTANT: Change texturecoordinate index depending on what UVset you have the animation data in. \
    \n Check script editor log for script computing progress')")


    cmds.showWindow(window)

############### Gets step size from text field  #################
def updateStepSize(*args):
    global gStepSize
    
    try:
        textField = int(cmds.textField("inputField", q=True, text = True))
        gStepSize = textField
        return gStepSize
    except:
        om.MGlobal_displayError("Please no stringerno in inputerino")
        return False

############### Progressbar ################# 
def progressBar(*args):
    cmds.separator(height = 10, style = "none")
    cmds.separator(height = 10, style = "none")
    cmds.text(label = "")
    widgets["progressControl"] = cmds.progressBar(h = 25, width=385)
    cmds.separator(height = 10, style = "none")
    cmds.separator(height = 10, style = "none")
    
############### MAIN for the actual UVing and combining #################
def main(selection, *args):
    print "COMPUTING FRAMES..."
    id = 0
    for item in selection:
        
        #Progress bar
        cmds.separator(height = 10, style = "none")
        cmds.separator(height = 10, style = "none")
        cmds.text(label = "")
        progressControl = cmds.progressBar(h = 25, width=385, max = len(selection))
        cmds.separator(height = 10, style = "none")
        cmds.separator(height = 10, style = "none")
        cmds.progressBar(progressControl, edit=True, step=1)
        
        
        
        copyUVSet(item)
        modifyUVs(item,id)
        print str(id+1) + "/" + str(len(selection)) + " PROCESSED"
        id += 1
    
    print "COMBINGING MESHES..."    
    cmds.select(selection)
    cmds.polyUnite(muv = True)
    cmds.progressBar(progressControl, edit=True, step=1) 
    cmds.DeleteHistory()
    print "FINSIHED"
        
############### COPY UVs TO NEW UVSET #################
def copyUVSet(item,*args):
    
    cmds.select(item)
    cmds.polyUVSet(cp = True)
    cmds.polyUVSet(currentUVSet = True, uvSet = "uvSet1")
    cmds.polyUVSet(rename = True, newUVSet = "morphUVs", uvSet= "uvSet1")

############### MODIFY UV #################
#Move UVs around    
def modifyUVs(item,id, *args):
    cmds.select(item)
    
    cmds.select(cmds.polyListComponentConversion(tuv = True), r = True)
    uvs = cmds.ls(sl=True, fl=True)

    number = 0.5 + id

    for uv in uvs:
       cmds.select (uv)
       cmds.polyEditUV(uv, relative=False, uValue=number, vValue= 0.5)  

############### Starts Simple Version #################       
def vertexAnimSimple(*args):
    selection = cmds.ls(sl=True)
    if len(selection) < 2:
        om.MGlobal.displayError("Please Select at least 2 objects")
        return
    main(selection)
    
############### MAIN for animating with a single mesh #################       
def vertexAnimTimeline(*args):         
   
    selection = cmds.ls(sl=True)
    if len(selection) == 0:
        om.MGlobal.displayError("Please Select Something")
        return
    combinedName = selection[0] + "combined"
    if len(selection) > 1:
        cmds.polyUnite(selection, n = combinedName)
        selection = combinedName

    gStepSize = updateStepSize()
    print "STEPSIZE: " + str(gStepSize)
    startFrame = cmds.playbackOptions(q = True, minTime=True)
    endFrame = cmds.playbackOptions(q = True, maxTime=True)
    
    frameList = range( int( startFrame ), int( endFrame ) + 1 )
    frameList = frameList[0::gStepSize]

    selectionList = []
    for frame in frameList:
        cmds.select(selection)
        newName = "frame" + str(frame)
        
        cmds.currentTime(frame, edit=True)
        cmds.duplicate(name = newName)
        selectionList.append(newName)
        #print selectionList

    cmds.delete(selection)   
    main(selectionList)
