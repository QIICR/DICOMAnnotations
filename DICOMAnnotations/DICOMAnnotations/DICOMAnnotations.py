from __future__ import division
import os
import unittest
import numpy as np
from __main__ import vtk, qt, ctk, slicer

#
# DICOMAnnotations
#

class DICOMAnnotations:
  def __init__(self, parent):
    parent.title = "DICOM Annotations" # TODO make this more human readable by adding spaces
    parent.categories = ["Quantification"]
    parent.dependencies = []
    parent.contributors = ["Alireza Mehrtash (SPL, BWH), Andrey Fedorov (SPL, BWH), Steve Pieper (Isomics)"]
    parent.helpText = """
    The DICOM Annotations module is used to get the useful meta-data information from DICOM images
    and add display them on the corners of Slice views.
    """
    parent.acknowledgementText = """
    Supported by NIH U01CA151261 (PI Fennessy) and U24 CA180918 (PIs Kikinis and Fedorov).
    """
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['DICOMAnnotations'] = self.runTest

  def runTest(self):
    tester = DICOMAnnotationsTest()
    tester.runTest()
#
# DICOMAnnotationsWidget
#

class DICOMAnnotationsWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

    self.cornerTexts =[]
    # Bottom Left Corner Text
    self.cornerTexts.append({'1-Label':'','2-Foreground':'','3-Background':''})
    # Bottom Rihgt Corner Text
    self.cornerTexts.append({'1-TR':'','2-TE':''})
    # Top Left Corner Text
    self.cornerTexts.append({'1-PatientName':'','2-PatientID':'','3-PatientInfo':'',
      '4-Bg-StudyDate':'','5-Fg-StudyDate':'','6-Bg-StudyTime':'','7-Bg-StudyTime':'',
      '8-Bg-SeriesDescription':'','9-Fg-SeriesDescription':''})
    # Top Rihgt Corner Text
    self.cornerTexts.append({'1-Institution-Name':'','2-Referring-Phisycian':'','3-Manufacturer':'',
      '4-Model':'','5-Patient-Position':''})

    self.topLeftAnnotationDisplay = True
    self.topRightAnnotationDisplay = True
    self.bottomLeftAnnotationDisplay = True
    self.bottomRightAnnotationDisplay = True

    self.layoutManager = slicer.app.layoutManager()
    self.sliceCornerAnnotations = {}
    
    #
    # Loading the Human 3D Model into scene
    #
    self.scene = slicer.mrmlScene

    # Module's Path
    # TODO: Update when moving to Data Probe
    modulePath= slicer.modules.dicomannotations.path.replace("DICOMAnnotations.py","")

    modelPath = modulePath + "Resources/Models/" + "slicer-human-model.stl"
    successfulLoad = slicer.util.loadModel(modelPath)
    if successfulLoad != True:
      print 'Warning: human model did not load'

    nodes = self.scene.GetNodesByName('slicer-human-model') 
    n = nodes.GetNumberOfItems()
    self.humanModelNode = nodes.GetItemAsObject(0)
    self.humanModelNode.SetDisplayVisibility(False)
    displayNode = self.humanModelNode.GetDisplayNode()
    # Color R:239, G:208, B:207
    #displayNode.SetColor(0.93,0.81,0.80)
    displayNode.SetSliceIntersectionVisibility(False)

    # Shorts model
    shortsPath = modulePath + "Resources/Models/" + "shorts-model.stl"
    successfulLoad = slicer.util.loadModel(shortsPath)
    if successfulLoad != True:
      print 'Warning: shorts model did not load'
    nodes = self.scene.GetNodesByName('shorts-model') 
    n = nodes.GetNumberOfItems()
    self.shortsModelNode = nodes.GetItemAsObject(0)
    self.shortsModelNode.SetDisplayVisibility(False)
    displayNode = self.shortsModelNode.GetDisplayNode()
    # Color R:239, G:208, B:207
    #displayNode.SetColor(0.93,0.81,0.80)
    displayNode.SetSliceIntersectionVisibility(False)

    # Left Shoe
    leftShoePath = modulePath + "Resources/Models/" + "left-shoe.stl"
    successfulLoad = slicer.util.loadModel(leftShoePath)
    if successfulLoad != True:
      print 'Warning: left shoe model did not load'
    nodes = self.scene.GetNodesByName('left-shoe') 
    n = nodes.GetNumberOfItems()
    self.leftShoeNode = nodes.GetItemAsObject(0)
    self.leftShoeNode.SetDisplayVisibility(False)
    displayNode = self.leftShoeNode .GetDisplayNode()
    # Color R:239, G:208, B:207
    #displayNode.SetColor(0.93,0.81,0.80)
    displayNode.SetSliceIntersectionVisibility(False)

    # Right Shoe
    rightShoePath = modulePath + "Resources/Models/" + "right-shoe.stl"
    successfulLoad = slicer.util.loadModel(rightShoePath)
    if successfulLoad != True:
      print 'Warning: right-shoe model did not load'
    nodes = self.scene.GetNodesByName('right-shoe') 
    n = nodes.GetNumberOfItems()
    self.rightShoeNode = nodes.GetItemAsObject(0)
    self.rightShoeNode.SetDisplayVisibility(False)
    displayNode = self.rightShoeNode.GetDisplayNode()
    # Color R:239, G:208, B:207
    #displayNode.SetColor(0.93,0.81,0.80)
    displayNode.SetSliceIntersectionVisibility(False)

  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "DICOMAnnotations Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # DICOM Annotations Checkbox
    #
    self.sliceViewAnnotationsCheckBox = qt.QCheckBox('Slice View Annotations')
    parametersFormLayout.addRow(self.sliceViewAnnotationsCheckBox)

    #
    # Corner Annotations Activation Checkboxes
    #
    self.cornerActivationsGroupBox = ctk.ctkCollapsibleGroupBox()
    self.cornerActivationsGroupBox.setTitle('Active Corners')
    self.cornerActivationsGroupBox.enabled = False
    parametersFormLayout.addRow(self.cornerActivationsGroupBox)
    cornerActionHBoxLayout = qt.QHBoxLayout(self.cornerActivationsGroupBox)

    self.cornerActivationCheckbox = []

    for i in xrange(4):
      self.cornerActivationCheckbox.append(qt.QCheckBox())
      self.cornerActivationCheckbox[i].checked = True
      cornerActionHBoxLayout.addWidget(self.cornerActivationCheckbox[i])
      self.cornerActivationCheckbox[i].connect('clicked()', self.updateSliceViewFromGUI)

    self.cornerActivationCheckbox[0].setText('Top Left')
    self.cornerActivationCheckbox[1].setText('Top Right')
    self.cornerActivationCheckbox[2].setText('Bottom Left')
    self.cornerActivationCheckbox[3].setText('Bottom Right')

    #
    # Corner Annotations Font Properties
    #
    self.fontPropertiesGroupBox = ctk.ctkCollapsibleGroupBox()
    self.fontPropertiesGroupBox.setTitle('Font Properties')
    self.fontPropertiesGroupBox.enabled = False
    parametersFormLayout.addRow(self.fontPropertiesGroupBox)
    fontPropertiesHBoxLayout = qt.QHBoxLayout(self.fontPropertiesGroupBox)

    fontFamilyLabel = qt.QLabel('Font Family: ')
    fontPropertiesHBoxLayout.addWidget(fontFamilyLabel)
    self.timesFontRadioButton = qt.QRadioButton('Times')
    fontPropertiesHBoxLayout.addWidget(self.timesFontRadioButton)
    self.timesFontRadioButton.connect('clicked()', self.updateSliceViewFromGUI)
    self.timesFontRadioButton.checked = True
    self.arialFontRadioButton = qt.QRadioButton('Arial')
    self.arialFontRadioButton.connect('clicked()', self.updateSliceViewFromGUI)
    fontPropertiesHBoxLayout.addWidget(self.arialFontRadioButton)

    fontSizeLabel = qt.QLabel('Font Size: ')
    fontPropertiesHBoxLayout.addWidget(fontSizeLabel)
    self.fontSizeSpinBox = qt.QSpinBox()
    self.fontSizeSpinBox.setMinimum(10)
    self.fontSizeSpinBox.setMaximum(20)
    self.fontSizeSpinBox.value = 14
    fontPropertiesHBoxLayout.addWidget(self.fontSizeSpinBox)
    self.fontSizeSpinBox.connect('valueChanged(int)', self.updateSliceViewFromGUI)

    #
    # Scaling Bar Area
    #
    self.scalingBarCollapsibleButton = ctk.ctkCollapsibleButton()
    self.scalingBarCollapsibleButton.enabled = False
    self.scalingBarCollapsibleButton.text = "Scaling Bar"
    self.layout.addWidget(self.scalingBarCollapsibleButton)

    # Layout within the dummy collapsible button
    scalingBarFormLayout = qt.QFormLayout(self.scalingBarCollapsibleButton)

    #
    # Scaling Bar Activation Checkbox
    #
    self.showScalingBarCheckBox = qt.QCheckBox('Show Scaling Bar')
    scalingBarFormLayout.addRow(self.showScalingBarCheckBox)

    #
    # Human Model Area
    #
    self.humanModelCollapsibleButton = ctk.ctkCollapsibleButton()
    self.humanModelCollapsibleButton.text = "Human Model"
    self.humanModelCollapsibleButton.enabled = False
    self.layout.addWidget(self.humanModelCollapsibleButton)

    # Layout within the dummy collapsible button
    humanModelFormLayout = qt.QFormLayout(self.humanModelCollapsibleButton)

    #
    # Human Model Activation Checkbox
    #
    self.showHumanModelCheckBox = qt.QCheckBox('Show Human Model')
    humanModelFormLayout.addRow(self.showHumanModelCheckBox)

    # connections

    # Add vertical spacer
    self.layout.addStretch(1)
    self.sliceViewAnnotationsCheckBox.connect('clicked()', self.updateSliceViewFromGUI)
    self.showScalingBarCheckBox.connect('clicked()', self.updateSliceViewFromGUI)
    self.showHumanModelCheckBox.connect('clicked()', self.updateSliceViewFromGUI)

  def cleanup(self):
    pass

  def updateSliceViewFromGUI(self):
    # Create corner annotations if have not created already
    if len(self.sliceCornerAnnotations.items()) == 0:
      self.createCornerAnnotations()

    if self.timesFontRadioButton.checked:
      fontFamily = 'Times'
    else:
      fontFamily = 'Arial'

    fontSize = self.fontSizeSpinBox.value

    for sliceViewName in self.sliceViewNames:
      cornerAnnotation = self.sliceCornerAnnotations[sliceViewName]
      cornerAnnotation.SetMaximumFontSize(fontSize)
      cornerAnnotation.SetMinimumFontSize(fontSize)
      textProperty = cornerAnnotation.GetTextProperty()
      if fontFamily == 'Times':
        textProperty.SetFontFamilyToTimes()
      else:
        textProperty.SetFontFamilyToArial()

    if self.cornerActivationCheckbox[0].checked:
      self.topLeftAnnotationDisplay = True
    else:
      self.topLeftAnnotationDisplay = False

    if self.cornerActivationCheckbox[1].checked:
      self.topRightAnnotationDisplay = True
    else:
      self.topRightAnnotationDisplay = False

    if self.cornerActivationCheckbox[2].checked:
      self.bottomLeftAnnotationDisplay = True
    else:
      self.bottomLeftAnnotationDisplay = False

    if self.cornerActivationCheckbox[3].checked:
      self.bottomRightAnnotationDisplay = True
    else:
      self.bottomRightAnnotationDisplay = False

    if self.sliceViewAnnotationsCheckBox.checked:
      self.cornerActivationsGroupBox.enabled = True
      self.fontPropertiesGroupBox.enabled = True
      self.humanModelCollapsibleButton.enabled = True
      self.scalingBarCollapsibleButton.enabled = True

      for sliceViewName in self.sliceViewNames:
        sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
        sl = sliceWidget.sliceLogic()
        #bl =sl.GetBackgroundLayer()
        self.makeAnnotationText(sl)
    else:
      self.cornerActivationsGroupBox.enabled = False
      self.fontPropertiesGroupBox.enabled = False
      self.humanModelCollapsibleButton.enabled = False
      self.scalingBarCollapsibleButton.enabled = False

      for sliceViewName in self.sliceViewNames:
        self.sliceCornerAnnotations[sliceViewName].SetText(0, "")
        self.sliceCornerAnnotations[sliceViewName].SetText(1, "")
        self.sliceCornerAnnotations[sliceViewName].SetText(2, "")
        self.sliceCornerAnnotations[sliceViewName].SetText(3, "")
        self.sliceViews[sliceViewName].scheduleRender()

  def createCornerAnnotations(self):
    self.sliceViewNames = []
    self.sliceWidgets = {}
    self.sliceViews = {}
    self.cameras = {}
    self.blNodeObserverTag = {}
    self.sliceLogicObserverTag = {}
    self.sliceCornerAnnotations = {}
    self.humanModelRenderers = {}
    self.renderers = {}
    self.scalingBarActors = {}
    self.points = {}
    self.scalingBarTextActors = {}
    #self.sliceRightOrientaionMarker = {}
    #self.sliceTopOrientaionMarker = {}
    # NOTE: New
    self.colorScalarBars = {}

    sliceViewNames = self.layoutManager.sliceViewNames()

    for sliceViewName in sliceViewNames:
      self.sliceViewNames.append(sliceViewName)
    for sliceViewName in self.sliceViewNames:
      self.addObserver(sliceViewName)

  def addObserver(self, sliceViewName):
    sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
    self.sliceWidgets[sliceViewName] = sliceWidget
    sliceView = sliceWidget.sliceView()

    renderWindow = sliceView.renderWindow()
    renderer = renderWindow.GetRenderers().GetItemAsObject(0)
    self.renderers[sliceViewName] = renderer

    #
    # Create the Scaling Bar
    #
    self.points[sliceViewName] = vtk.vtkPoints()
    self.points[sliceViewName].SetNumberOfPoints(10)

    # Create line#0
    line0 = vtk.vtkLine()
    line0.GetPointIds().SetId(0,0)
    line0.GetPointIds().SetId(1,1)

    # Create line#1
    line1 = vtk.vtkLine()
    line1.GetPointIds().SetId(0,0)
    line1.GetPointIds().SetId(1,2)

    # Create line#2
    line2 = vtk.vtkLine()
    line2.GetPointIds().SetId(0,2)
    line2.GetPointIds().SetId(1,3)

    # Create line#3
    line3 = vtk.vtkLine()
    line3.GetPointIds().SetId(0,2)
    line3.GetPointIds().SetId(1,4)

    # Create line#4
    line4 = vtk.vtkLine()
    line4.GetPointIds().SetId(0,4)
    line4.GetPointIds().SetId(1,5)

    # Create line#5
    line5 = vtk.vtkLine()
    line5.GetPointIds().SetId(0,4)
    line5.GetPointIds().SetId(1,6)

    # Create line#6
    line6 = vtk.vtkLine()
    line6.GetPointIds().SetId(0,6)
    line6.GetPointIds().SetId(1,7)

    # Create line#7
    line7 = vtk.vtkLine()
    line7.GetPointIds().SetId(0,6)
    line7.GetPointIds().SetId(1,8)

    # Create line#8
    line8 = vtk.vtkLine()
    line8.GetPointIds().SetId(0,8)
    line8.GetPointIds().SetId(1,9)

    # Create a cell array to store the lines in and add the lines to it
    lines = vtk.vtkCellArray()
    lines.InsertNextCell(line0)
    lines.InsertNextCell(line1)
    lines.InsertNextCell(line2)
    lines.InsertNextCell(line3)
    lines.InsertNextCell(line4)
    lines.InsertNextCell(line5)
    lines.InsertNextCell(line6)
    lines.InsertNextCell(line7)
    lines.InsertNextCell(line8)

    # Create a polydata to store everything in
    linesPolyData = vtk.vtkPolyData()

    # Add the points to the dataset
    linesPolyData.SetPoints(self.points[sliceViewName])

    # Add the lines to the dataset
    linesPolyData.SetLines(lines)

    self.scalingBarTextActors[sliceViewName] = vtk.vtkTextActor()
    '''
    self.sliceRightOrientaionMarker[sliceViewName] = vtk.vtkTextActor()
    self.sliceTopOrientaionMarker[sliceViewName] = vtk.vtkTextActor()
    textActors = [self.scalingBarTextActors[sliceViewName],
      self.sliceRightOrientaionMarker[sliceViewName],
      self.sliceTopOrientaionMarker[sliceViewName]]

    for textActor in textActors:
      txtprop = textActor.GetTextProperty()
      txtprop.SetFontFamilyToTimes
      if textActor == (self.scalingBarTextActors[sliceViewName]):
        txtprop.SetFontSize(14)
      # Larger font size for orientation markers
      else:
        txtprop.SetFontSize(20)
      txtprop.SetColor(1,1,1)
      textActor.SetInput("")
    '''

    # mapper
    mapper = vtk.vtkPolyDataMapper2D()
    if vtk.VTK_MAJOR_VERSION <= 5:
      mapper.SetInput(linesPolyData)
    else:
      mapper.SetInputData(linesPolyData)
    # actor
    self.scalingBarActors[sliceViewName] = vtk.vtkActor2D()
    actor = self.scalingBarActors[sliceViewName]
    actor.SetMapper(mapper)
    # color actor
    actor.GetProperty().SetColor(1,1,1)
    actor.GetProperty().SetLineWidth(1)
    if self.showScalingBarCheckBox.checked:
      renderer.AddActor(actor)
      renderer.AddActor(textActor)

    #NOTE
    scalarBar = vtk.vtkScalarBarActor()
    lookupTable = vtk.vtkLookupTable()
    scalarBar.SetLookupTable(lookupTable)
    #renderer.AddActor2D(scalarBar)
    self.colorScalarBars[sliceViewName] = scalarBar

    self.sliceViews[sliceViewName] = sliceView
    self.sliceCornerAnnotations[sliceViewName] = sliceView.cornerAnnotation()
    sliceLogic = sliceWidget.sliceLogic()
    self.sliceLogicObserverTag[sliceViewName] = sliceLogic.AddObserver(vtk.vtkCommand.ModifiedEvent, 
                                             self.updateCornerAnnotations)


    #
    # Making the human model mapper and actor
    #

    # Mapper
    humanMapper = vtk.vtkPolyDataMapper()
    shortsMapper = vtk.vtkPolyDataMapper()
    leftShoeMapper = vtk.vtkPolyDataMapper()
    rightShoeMapper = vtk.vtkPolyDataMapper()

    if vtk.VTK_MAJOR_VERSION <= 5:
      humanMapper.SetInput(self.humanModelNode.GetPolyData())
      shortsMapper.SetInput(self.shortsModelNode.GetPolyData())
      leftShoeMapper.SetInput(self.leftShoeNode.GetPolyData())
      rightShoeMapper.SetInput(self.rightShoeNode.GetPolyData())
    else:
      humanMapper.SetInputData(self.humanModelNode.GetPolyData())
      shortsMapper.SetInputData(self.shortsModelNode.GetPolyData())
      leftShoeMapper.SetInputData(self.leftShoeNode.GetPolyData())
      rightShoeMapper.SetInputData(self.rightShoeNode.GetPolyData())

    # Actor
    self.humanActor = vtk.vtkActor()
    self.humanActor.SetMapper(humanMapper)
    self.humanActor.GetProperty().SetColor(0.93,0.81,0.80)

    self.shortsActor = vtk.vtkActor()
    self.shortsActor.SetMapper(shortsMapper)
    self.shortsActor.GetProperty().SetColor(0,0,1)

    self.leftShoeActor = vtk.vtkActor()
    self.leftShoeActor.SetMapper(leftShoeMapper)
    self.leftShoeActor.GetProperty().SetColor(1,0,0)

    self.rightShoeActor = vtk.vtkActor()
    self.rightShoeActor.SetMapper(rightShoeMapper)
    self.rightShoeActor.GetProperty().SetColor(0,1,0)

    # Renderer
    self.humanModelRenderers[sliceViewName] = vtk.vtkRenderer()
    ren = self.humanModelRenderers[sliceViewName]

    # assign actor to the renderer
    ren.AddActor(self.humanActor)
    ren.AddActor(self.shortsActor)
    ren.AddActor(self.leftShoeActor)
    ren.AddActor(self.rightShoeActor)
    ren.SetViewport(0.8,0,1,.3)
    rw = self.sliceViews[sliceViewName].renderWindow()

    backgroundLayer = sliceLogic.GetBackgroundLayer()
    sliceNode = backgroundLayer.GetSliceNode()
    m = sliceNode.GetXYToRAS()

    self.cameras[sliceViewName] = vtk.vtkCamera()
    '''
    if self.showHumanModelCheckBox.checked:
      camera = self.cameras[sliceViewName]

      x = np.matrix([[m.GetElement(0,0),m.GetElement(0,1),m.GetElement(0,2)],
          [m.GetElement(1,0),m.GetElement(1,1),m.GetElement(1,2)],
          [m.GetElement(2,0),m.GetElement(2,1),m.GetElement(2,2)]])
      y = np.array([0,0,300])
      position = np.inner(x,y)
      camera.SetPosition(-position[0,0],-position[0,1],-position[0,2])
      n = np.array([0,1,0])
      viewUp = np.inner(x,n)
      camera.SetViewUp(viewUp[0,0],viewUp[0,1],viewUp[0,2])

      #ren.PreserveDepthBufferOff()
      #print ren.GetPreserveDepthBuffer()
      #print 'transparent',ren.Transparent()
      ren.SetActiveCamera(camera)
      rw.AddRenderer(ren)
    '''

  def updateCornerAnnotations(self,caller,event):
    sliceViewNames = self.layoutManager.sliceViewNames()
    for sliceViewName in sliceViewNames:
      if sliceViewName not in self.sliceViewNames:
        self.sliceViewNames.append(sliceViewName)
        self.addObserver(sliceViewName)
        self.updateSliceViewFromGUI()
    self.makeAnnotationText(caller)

  def sliceLogicModifiedEvent(self, caller,event):
    self.updateLayersAnnotation(caller)

  def makeAnnotationText(self, sliceLogic):
    self.resetTexts()
    sliceCompositeNode = sliceLogic.GetSliceCompositeNode()

    backgroundLayer = sliceLogic.GetBackgroundLayer()
    foregroundLayer = sliceLogic.GetForegroundLayer()
    labelLayer = sliceLogic.GetLabelLayer()

    backgroundVolume = backgroundLayer.GetVolumeNode()
    foregroundVolume = foregroundLayer.GetVolumeNode()
    labelVolume = labelLayer.GetVolumeNode()

    sliceNode = backgroundLayer.GetSliceNode()
    sliceViewName = sliceNode.GetLayoutName()
    self.currentSliceViewName = sliceNode.GetLayoutName()
    
    if self.sliceViews[self.currentSliceViewName]:

      viewWidth = self.sliceViews[self.currentSliceViewName].width
      #print 'viewWidth is: ', viewWidth
      viewHeight = self.sliceViews[self.currentSliceViewName].height
      rasToXY = vtk.vtkMatrix4x4()
      m = sliceNode.GetXYToRAS()
      rasToXY.DeepCopy(m)
      rasToXY.Invert()
      #print rasToXY
      scalingFactorString = " mm"

      #print rasToXY
      # TODO: Fix the bug
      scalingFactor = 1
      import math
      scalingFactor = math.sqrt( rasToXY.GetElement(0,0)**2 + 
          rasToXY.GetElement(0,1)**2 +rasToXY.GetElement(0,2) **2 )

      #rulerArea = viewWidth/scalingFactor/3
      rulerArea = viewWidth/scalingFactor/7
      import numpy as np
      rulerSizesArray = np.array([1,5,10,50,100])
      index = np.argmin(np.abs(rulerSizesArray- rulerArea))

      '''
      if self.sliceWidgets[self.currentSliceViewName].sliceOrientation == 'Axial':
        scalingFactor = rasToXY.GetElement(1,1)
      elif self.sliceWidgets[self.currentSliceViewName].sliceOrientation == 'Sagittal':
        scalingFactor = rasToXY.GetElement(2,1)
      elif self.sliceWidgets[self.currentSliceViewName].sliceOrientation == 'Coronal':
        scalingFactor = rasToXY.GetElement(2,1)
      '''

      if rulerSizesArray[index]/10 > 1:
        scalingFactorString = str(int(rulerSizesArray[index]/10))+" cm"
      else:
        scalingFactorString = str(rulerSizesArray[index])+" mm"

      RASRulerSize = rulerSizesArray[index]

      pts = self.points[sliceViewName]
      pts.SetPoint(0,[(viewWidth-RASRulerSize*scalingFactor)/2,10, 0])
      pts.SetPoint(1,[(viewWidth-RASRulerSize*scalingFactor)/2,20, 0])
      pts.SetPoint(2,[(viewWidth-RASRulerSize*scalingFactor/2)/2,10, 0])
      pts.SetPoint(3,[(viewWidth-RASRulerSize*scalingFactor/2)/2,17, 0])
      pts.SetPoint(4,[viewWidth/2,10, 0])
      pts.SetPoint(5,[viewWidth/2,20, 0])
      pts.SetPoint(6,[(viewWidth+RASRulerSize*scalingFactor/2)/2,10, 0])
      pts.SetPoint(7,[(viewWidth+RASRulerSize*scalingFactor/2)/2,17, 0])
      pts.SetPoint(8,[(viewWidth+RASRulerSize*scalingFactor)/2,10, 0])
      pts.SetPoint(9,[(viewWidth+RASRulerSize*scalingFactor)/2,20, 0])
      #print [(viewWidth-RASRulerSize*scalingFactor)/2,10, 0]
      #print scalingFactor
      textActor = self.scalingBarTextActors[self.currentSliceViewName]

      textActor.SetInput(scalingFactorString)

      #NOTE: changed
      textActor.SetDisplayPosition(int((viewWidth+RASRulerSize*scalingFactor)/2)+10,7)

      self.minimumWidthForScalingRuler = 300

      #NOTE
      scalarBAr = self.colorScalarBars[self.currentSliceViewName]
      renderer = self.renderers[self.currentSliceViewName]
      #scalarBAr.SetWidth(20)
      #scalarBAr.SetHeight(60)
      if ( backgroundVolume != None):
        vdn = backgroundVolume.GetDisplayNode()
        vcn = vdn.GetColorNode()
        lut = vcn.GetLookupTable()
        #scalarBAr.SetLookupTable(lut)
        print scalarBAr.GetPosition()
        print scalarBAr.GetPosition2()
        #scalarBAr.SetPosition(9/10*viewWidth,2/5*viewHeight)
        #scalarBAr.SetPosition2(9/10*viewWidth+10,3/5*viewHeight)
        #renderer.AddActor2D(scalarBAr)
        #scalarBAr.SetTitle("Title")
        lut = vcn.GetLookupTable()
        lut2 = vtk.vtkLookupTable()
        lut2.DeepCopy(lut)
        width = vtk.mutable(0)
        level = vtk.mutable(0)
        rangeLow = vtk.mutable(0)
        rangeHigh = vtk.mutable(0)
        sliceLogic.GetBackgroundWindowLevelAndRange(width,level,rangeLow,rangeHigh)
        lut2.SetRange(int(level-width/2),int(level+width/2))
        scalarBAr.SetLookupTable(lut2)

      if self.showScalingBarCheckBox.checked and \
          viewWidth > self.minimumWidthForScalingRuler and\
         rulerArea>0.5 and rulerArea<500 :
        self.renderers[self.currentSliceViewName].AddActor(
            self.scalingBarActors[self.currentSliceViewName])
        self.renderers[self.currentSliceViewName].AddActor(textActor)
        #NOTE
        self.renderers[self.currentSliceViewName].AddActor(
            self.colorScalarBars[self.currentSliceViewName])
        #self.renderers[self.currentSliceViewName].AddActor(rightMarker)
        #self.renderers[self.currentSliceViewName].AddActor(topMarker)
      else:
        self.renderers[self.currentSliceViewName].RemoveActor(
            self.scalingBarActors[self.currentSliceViewName])
        # TODO: Add a statement to check the existance of textActor
        self.renderers[self.currentSliceViewName].RemoveActor(textActor)
        #NOTE
        self.renderers[self.currentSliceViewName].RemoveActor(
            self.colorScalarBars[self.currentSliceViewName])
        #self.renderers[self.currentSliceViewName].RemoveActor(rightMarker)
        #self.renderers[self.currentSliceViewName].RemoveActor(topMarker)
   
      ren = self.humanModelRenderers[sliceViewName]
      rw = self.sliceViews[sliceViewName].renderWindow()

      if self.showHumanModelCheckBox.checked:
        # assign actor to the renderer
        ren.AddActor(self.humanActor)
        ren.AddActor(self.shortsActor)
        ren.AddActor(self.leftShoeActor)
        ren.AddActor(self.rightShoeActor)
        backgroundLayer = sliceLogic.GetBackgroundLayer()
        sliceNode = backgroundLayer.GetSliceNode()
        m = sliceNode.GetXYToRAS()
        self.cameras[sliceViewName] = vtk.vtkCamera()
        camera = self.cameras[sliceViewName]
        x = np.matrix([[m.GetElement(0,0),m.GetElement(0,1),m.GetElement(0,2)],
            [m.GetElement(1,0),m.GetElement(1,1),m.GetElement(1,2)],
            [m.GetElement(2,0),m.GetElement(2,1),m.GetElement(2,2)]])
        y = np.array([0,0,300])
        position = np.inner(x,y)
        print x
        #position = position-((np.max(position))-350)
        camera.SetPosition(-position[0,0],-position[0,1],-position[0,2])
        n = np.array([0,1,0])
        viewUp = np.inner(x,n)
        print viewUp
        camera.SetViewUp(viewUp[0,0],viewUp[0,1],viewUp[0,2])

        #ren.PreserveDepthBufferOff()
        #print ren.GetPreserveDepthBuffer()
        #print 'transparent',ren.Transparent()
        ren.SetActiveCamera(camera)
        rw.AddRenderer(ren)
      else:
        ren.RemoveActor(self.humanActor)
        ren.RemoveActor(self.shortsActor)
        ren.RemoveActor(self.leftShoeActor)
        ren.RemoveActor(self.leftShoeActor)
        rw.RemoveRenderer(ren)

      # Both background and foregraound
      if ( backgroundVolume != None and foregroundVolume != None):
        foregroundOpacity = sliceCompositeNode.GetForegroundOpacity()
        backgroundVolumeName = backgroundVolume.GetName()
        foregroundVolumeName = foregroundVolume.GetName()
        self.cornerTexts[0]['3-Background'] = 'B: ' + backgroundVolumeName
        self.cornerTexts[0]['2-Foreground'] = 'F: ' + foregroundVolumeName +  ' (' + str(
                      "%.1f"%foregroundOpacity) + ')'

        bgUids = backgroundVolume.GetAttribute('DICOM.instanceUIDs')
        fgUids = foregroundVolume.GetAttribute('DICOM.instanceUIDs')
        if (bgUids and fgUids):
          bgUid = bgUids.partition(' ')[0]
          fgUid = fgUids.partition(' ')[0]
          self.makeDicomAnnotation(bgUid,fgUid)
        else:
          for key in self.cornerTexts[2]:
            self.cornerTexts[2][key] = ''

      # Only background
      elif (backgroundVolume != None):
        backgroundVolumeName = backgroundVolume.GetName()
        if self.bottomLeftAnnotationDisplay:
          self.cornerTexts[0]['3-Background'] = 'B: ' + backgroundVolumeName

        uids = backgroundVolume.GetAttribute('DICOM.instanceUIDs')
        if uids:
          uid = uids.partition(' ')[0]
          self.makeDicomAnnotation(uid,None)

      # Only foreground
      elif (foregroundVolume != None):
        if self.bottomLeftAnnotationDisplay:
          foregroundVolumeName = foregroundVolume.GetName()
          self.cornerTexts[0]['2-Foreground'] = 'F: ' + foregroundVolumeName

        uids = foregroundVolume.GetAttribute('DICOM.instanceUIDs')
        if uids:
          uid = uids.partition(' ')[0]
          # passed UID as bg
          self.makeDicomAnnotation(uid,None)

      if (labelVolume != None):
        labelOpacity = sliceCompositeNode.GetLabelOpacity()
        labelVolumeName = labelVolume.GetName()
        self.cornerTexts[0]['1-Label'] = 'L: ' + labelVolumeName + ' (' + str(
                      "%.1f"%labelOpacity) + ')'

      self.drawCornerAnnotations()
      #labelOpacity = sliceCompositeNode.GetLabelOpacity()

  def makeDicomAnnotation(self,bgUid,fgUid):
    if fgUid != None and bgUid != None:
      backgroundDicomDic = self.extractDICOMValues(bgUid)
      foregroundDicomDic = self.extractDICOMValues(fgUid)
      # check if background and foreground are from different patients
      # and remove the annotations

      if self.topLeftAnnotationDisplay:
        if backgroundDicomDic['Patient Name'] != foregroundDicomDic['Patient Name'
            ] or backgroundDicomDic['Patient ID'] != foregroundDicomDic['Patient ID'
              ] or backgroundDicomDic['Patient Birth Date'] != foregroundDicomDic['Patient Birth Date']:
              for key in self.cornerTexts[2]:
                self.cornerTexts[2][key] = ''
        else:
          self.cornerTexts[2]['1-PatientName'] = backgroundDicomDic['Patient Name'].replace('^',', ')
          self.cornerTexts[2]['2-PatientID'] = 'ID: ' + backgroundDicomDic['Patient ID']
          backgroundDicomDic['Patient Birth Date'] = self.formatDICOMDate(backgroundDicomDic['Patient Birth Date'])
          self.cornerTexts[2]['3-PatientInfo'] = self.makePatientInfo(backgroundDicomDic)

          if (backgroundDicomDic['Study Date'] != foregroundDicomDic['Study Date']):
            self.cornerTexts[2]['4-Bg-StudyDate'] = 'B: ' + self.formatDICOMDate(backgroundDicomDic['Study Date'])
            self.cornerTexts[2]['5-Fg-StudyDate'] = 'F: ' + self.formatDICOMDate(foregroundDicomDic['Study Date'])
          else:
            self.cornerTexts[2]['4-Bg-StudyDate'] =  self.formatDICOMDate(backgroundDicomDic['Study Date'])

          if (backgroundDicomDic['Study Time'] != foregroundDicomDic['Study Time']):
            self.cornerTexts[2]['6-Bg-StudyTime'] = 'B: ' + self.formatDICOMTime(backgroundDicomDic['Study Time'])
            self.cornerTexts[2]['7-Fg-StudyTime'] = 'F: ' + self.formatDICOMTime(foregroundDicomDic['Study Time'])
          else:
            self.cornerTexts[2]['6-Bg-StudyTime'] = self.formatDICOMTime(backgroundDicomDic['Study Time'])

          if (backgroundDicomDic['Series Description'] != foregroundDicomDic['Series Description']):
            self.cornerTexts[2]['8-Bg-SeriesDescription'] = 'B: ' + backgroundDicomDic['Series Description']
            self.cornerTexts[2]['9-Fg-SeriesDescription'] = 'F: ' + foregroundDicomDic['Series Description']
          else:
            self.cornerTexts[2]['8-Bg-SeriesDescription'] = backgroundDicomDic['Series Description']

    # Only Background or Only Foreground
    else:
      uid = bgUid
      dicomDic = self.extractDICOMValues(uid)
      if self.topLeftAnnotationDisplay:
        self.cornerTexts[2]['1-PatientName'] = dicomDic['Patient Name'].replace('^',', ')
        self.cornerTexts[2]['2-PatientID'] = 'ID: ' + dicomDic ['Patient ID']
        dicomDic['Patient Birth Date'] = self.formatDICOMDate(dicomDic['Patient Birth Date'])
        self.cornerTexts[2]['3-PatientInfo'] = self.makePatientInfo(dicomDic)
        self.cornerTexts[2]['4-Bg-StudyDate']  = self.formatDICOMDate(dicomDic['Study Date'])
        self.cornerTexts[2]['6-Bg-StudyTime'] = self.formatDICOMTime(dicomDic['Study Time'])
        self.cornerTexts[2]['8-Bg-SeriesDescription'] = dicomDic['Series Description']

      if (self.sliceWidgets[self.currentSliceViewName].width > 600 and self.topRightAnnotationDisplay):
        self.cornerTexts[3]['1-Institution-Name'] = dicomDic['Institution Name']
        self.cornerTexts[3]['2-Referring-Phisycian'] = dicomDic['Referring Physician Name'].replace('^',', ')
        self.cornerTexts[3]['3-Manufacturer'] = dicomDic['Manufacturer']
        self.cornerTexts[3]['4-Model'] = dicomDic['Model']
        self.cornerTexts[3]['5-Patient-Position'] = dicomDic['Patient Position']

      # Bottom Right Corner Annotations:
      # Modality Specific and Image Comments
      #
      if self.bottomRightAnnotationDisplay:
        modality = dicomDic['Modality']
        if modality == 'MR':
         self.cornerTexts[1]['1-TR']  = 'TR ' + dicomDic['Repetition Time']
         self.cornerTexts[1]['2-TE'] = 'TE ' + dicomDic['Echo Time']
  
  def makePatientInfo(self,dicomDic):
    # This will give an string of patient's birth date,
    # patient's age and sex
    patientInfo = dicomDic['Patient Birth Date'
          ] + ', ' + dicomDic['Patient Age'
              ] + ', ' + dicomDic['Patient Sex']
    return patientInfo

  def formatDICOMDate(self, date):
      return date[4:6] + '/' + date[6:]+ '/' + date[:4]

  def formatDICOMTime(self, time):
    studyH = time[:2]
    if int(studyH) > 12 :
      studyH = str (int(studyH) - 12)
      clockTime = ' PM'
    else:
      studyH = studyH
      clockTime = ' AM'
    studyM = time[2:4]
    studyS = time[4:6]
    return studyH + ':' + studyM  + ':' + studyS +clockTime

  def drawCornerAnnotations(self):
    cornerAnnotation = ''
    for i, cornerText in enumerate(self.cornerTexts):
      keys = sorted(cornerText.keys())
      cornerAnnotation = ''
      for key in keys:
        if ( cornerText[key] != ''):
          cornerAnnotation = cornerAnnotation+ cornerText[key] + '\n'
      sliceCornerAnnotation = self.sliceCornerAnnotations[self.currentSliceViewName]
      sliceCornerAnnotation.SetText(i, cornerAnnotation)
    self.sliceViews[self.currentSliceViewName].scheduleRender()

  def resetTexts(self):
    for i, cornerText in enumerate(self.cornerTexts):
      self.cornerTexts[i] =  dict((k,'') for k,v in cornerText.iteritems())

  def extractDICOMValues(self,uid):
    p ={}
    slicer.dicomDatabase.loadInstanceHeader(uid)
    tags = {
    "0008,0020": "Study Date",
    "0008,0030": "Study Time",
    "0008,0060": "Modality",
    "0008,0070": "Manufacturer",
    "0008,0080": "Institution Name",
    "0008,0090": "Referring Physician Name",
    # "0008,1030": "Study Description",
    "0008,103e": "Series Description",
    "0008,1090": "Model",
    "0010,0010": "Patient Name",
    "0010,0020": "Patient ID",
    "0010,0030": "Patient Birth Date",
    "0010,0040": "Patient Sex",
    "0010,1010": "Patient Age",
    # "0010,4000": "Patient Comments",
    # "0018,1030": "Protocol Name",
    "0018,5100": "Patient Position",
    # "0020,0010": "Study ID",
    # "0020,0011": "Series Number",
    #"0020,4000": "Image Comments"
    }

    p = self.extractTagValue(p, tags)
    if self.bottomRightAnnotationDisplay:
      if p['Modality'] == 'MR':
        mrTags = {
        "0018,0080": "Repetition Time",
        "0018,0081": "Echo Time"
        }
        p = self.extractTagValue(p, mrTags)
      '''
      These tags are not available in dicom tag cache now
      if p['Modality'] == 'CT':
        ctTags = {
        "0018,0060": "KVP",
        "0018,1152": "Exposure"
        }
        p = self.extractTagValue(p, ctTags)
      '''
    return p

  def extractTagValue(self,p,tags):
    for tag in tags.keys():
        dump = slicer.dicomDatabase.headerValue(tag)
        try:
          value = dump[dump.index('[')+1:dump.index(']')]
        except ValueError:
          value = "Unknown"
        p[tags[tag]] = value
    return p
  
  def onReload(self,moduleName="DICOMAnnotations"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onReloadAndTest(self,moduleName="DICOMAnnotations"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

#
# DICOMAnnotationsLogic
#

class DICOMAnnotationsLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def delayDisplay(self,message,msec=1000):
    #
    # logic version of delay display
    #
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()


class DICOMAnnotationsTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_DICOMAnnotations1()

  def test_DICOMAnnotations1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = DICOMAnnotationsLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
