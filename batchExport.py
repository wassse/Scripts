import maya.cmds as cmds
import maya.OpenMaya as om
import os
import maya.mel as mm
import subprocess
import batchExportSettings
from batchExportSettings import ExportSettings
reload(batchExportSettings)


#Getting script Dirs
shelfDir = cmds.internalVar(ush = True).split(";", 1)[0]
scriptsDir = str(shelfDir.split("/shelfpath", 1)[0]) + "/scriptpath/"
settingsName = scriptsDir + "batchExport_Settings.txt"


#Import settings Class
settings = ExportSettings()

############### CREATES THE UI #################
def UI():
    settings.readFromFile(settingsName)

    #Icon path
    icon = scriptsDir + "Icons/menuIconFile.png"

	#Check to see if our window exists
    if cmds.window("batchExportUI", exists = True):
		cmds.deleteUI("batchExportUI")

	#Create UI window
    window = cmds.window( "batchExportUI", title = "batchExport", w = 400, h = 190, mnb = False, mxb = False, sizeable = False, titleBarMenu = True, menuBar = True)

	#Create main layout
    mainLayout = cmds.columnLayout(w = 400, h = 190)

    #Banner image
    bannerPath = scriptsDir + "Icons/batchExportBanner.jpg"
    cmds.image(w = 400, h = 40, image = bannerPath)

	#Create our row column layout
    cmds.separator(height = 5)
    rowColumnLayout = cmds.rowColumnLayout(nc = 2, cw = [(1,360), (2,40)], columnOffset = [(1, "both", 5), (2, "both", 5)])

    #Export Directory
    cmds.text(label = "Export Directory:", align = "left")
    cmds.text(label = "")
    inputField = cmds.textField("inputField", width = 360)

    #Edit the inputfield to have filepath as default
    defaultDir = getDefaultDir()
    if defaultDir == "/FBX":
        cmds.textField( "inputField", edit = True, text = "SET OUTPUT DIR" )
    else:
        cmds.textField( "inputField", edit = True, text = defaultDir )
    exportBrowseButton = cmds.symbolButton(w = 20, h = 25, image = icon, c = browseFilePath)

    #Origo checkbox
    cmds.separator(height = 10, style = "none")
    cmds.separator(height = 10, style = "none")
    rowColumnLayout2 = cmds.rowColumnLayout(nc = 2, cw = [(1,200), (2,148)])
    origoBox = cmds.checkBox("origoBox", label = "Move to Origo", value = settings.moveToOrigo, cc = saveSettings)

    #FBX dropdown
    cmds.optionMenu("FBXVersion", label = "FBXVersion", cc = saveSettings)
    cmds.menuItem(label='2013') 
    cmds.menuItem(label='2014')
    cmds.menuItem(label='2016')
    cmds.optionMenu("FBXVersion", edit = True, v = settings.FBXVersion)

    #Build Button
    cmds.separator(height = 10, style = "none")
    cmds.separator(height = 10, style = "none")
    createButton = cmds.button(label = "EXPORT", w = 385, h = 40,p=mainLayout, c = exportMain)

	#Show window
    cmds.showWindow(window)

############### SAVE SETTINGS ###############
def saveSettings(*args):
    
    origoBoxResult = int(cmds.checkBox("origoBox", q = True, v = True))
    fbxVersionResult = cmds.optionMenu("FBXVersion", q = True, v=True)
    settings.saveToFile(settingsName, origoBoxResult, fbxVersionResult)

############### BROWSE importDir ###############
def browseFilePath(*args):
    
    #Dialog box
    returnPath = cmds.fileDialog2(fm = 3, fileFilter = None, ds = 2)[0]
    #Set inputField to the filepath selected
    cmds.textField("inputField", edit = True, text = returnPath)

############## GET SCENE DIR ##################
def getDefaultDir(*args):
    
    defaultSceneDir = cmds.file(q=True, sceneName=True)
    defaultDirectory = os.path.dirname(defaultSceneDir) + "/FBX"
    return defaultDirectory

############## GET FILE NAME ##################
def getFileName(object, inputField):
    if "|" in object:
        newObjName = object.split("|")[1]
        object = "|" + newObjName
        fileName = inputField + "/" + newObjName + ".fbx"
    else:
        fileName = inputField + "/" + object + ".fbx"
    
    return fileName
    
############## OBJECT SELECTION ##################
#Selects the correct object before export. If a mesh inside a group, export group instead.
def objectSelection(object):
    if "|" in object:
        newObjName = object.split("|")[1]
        object = "|" + newObjName
        cmds.select(str(object), r = True)
    else:
        cmds.select(str(object), r = True)
    
############## GET SCENE DIR ##################
#Loops through selection and adding writable objects to a list and locked object to errorstring
def checkWritable(selection, inputField):
    
    errorString = ""
    writableObjects = []
    for object in selection:
        fileName = getFileName(object, inputField) 
        
        fileExists = os.path.isfile(fileName) == True
        fileWritable = os.access(fileName, os.W_OK) == True
        if not fileExists or ( fileExists and fileWritable ):
            writableObjects.append(object)
        else:
            errorString += fileName + "\n"
            
    if len(errorString) > 0:
        if len(selection) == 1:
            stringText = "FBX is not writable. Please check out FBX in Perforce."
            cmds.confirmDialog( title='File not Writable', message=stringText, button="Confirm", defaultButton='Confirm')
            return writableObjects
        stringText = "File(s) are not writable:\n\n" + errorString + "\nContinue anyway?"
        result = cmds.confirmDialog( title='Files not Writable', message=stringText, button=['Continue','Cancel'], defaultButton='Continue', cancelButton='Cancel', dismissString='Cancel' )
        if result == "Continue":
            return writableObjects
    else:
        return writableObjects

############## EXPORT ##################
def export(object, fileName):
    
    objectSelection(object)
    print fileName
    mm.eval('FBXExportSmoothingGroups -v true;' )
    mm.eval('FBXExportFileVersion -v FBX{0}00;'.format(settings.FBXVersion))
    mm.eval('FBXExport -f "{0}" -s;'.format(fileName))

############### MESH EXPORT ###############
def exportMain(*args):
    
    settings.readFromFile(settingsName)
    if not cmds.pluginInfo("OneClick.mll", q=True, loaded=True):
        try: 
            cmds.loadPlugin("OneClick.mll")
        except:
            om.MGlobal.displayError("OneClick Plugin not found. Enable the plug-in in the plug-in manager")
            return
            
    #Stores the selection in a list and gives error if no selection was made
    selection = cmds.ls(sl=True)
    if len(selection) == 0:
        om.MGlobal.displayError("No Objects Selected")
        return

    #Gets the output directory and checks if its valid or the standard text
    inputField = cmds.textField("inputField", q = True, text = True)
    if inputField == "SET OUTPUT DIR":
        om.MGlobal.displayError("Please set export directory")
        return

    #Checks to see if the export directory exists, if not it creates the folders
    if not os.path.exists(inputField):
        os.makedirs(inputField)    
        
    #exports writable objects only
    writableObjects = checkWritable(selection, inputField)
    if not writableObjects:
        return
    for object in writableObjects:
        fileName = getFileName(object, inputField)
        print fileName
        if settings.moveToOrigo == False:
            export(object, fileName)
            cmds.select(str(object), r = True)
        else:
            cmds.select(str(object), r = True)
            orgx = cmds.getAttr(".tx")
            orgy = cmds.getAttr(".ty")
            orgz = cmds.getAttr(".tz")
            cmds.move( 0,0,0, ws = True, rpr = True)  
            export(object, fileName)
            cmds.setAttr(".tx", orgx)
            cmds.setAttr(".ty", orgy)
            cmds.setAttr(".tz", orgz)
            
    #TODO open file location after export. Not used atm, make it into button
    #sceneDir = inputField.replace("/", "\\")
    #exportDir = 'explorer "%s"' % sceneDir
    #subprocess.Popen(exportDir)