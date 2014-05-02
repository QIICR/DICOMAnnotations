import os
import unittest
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

    self.backgroundVolumeName = 'None'
    self.foregroundVolumeName = 'None'
    self.labelVolumeName = 'None'
    self.backgroundDicomDic = {}
    self.foregroundDicomDic = {}
    self.topLeftLines =  ['']*7
    self.topRightLines =  ['']*5

    self.topLeftAnnotationDisplay = True
    self.topRightAnnotationDisplay = True
    self.bottomLeftAnnotationDisplay = True
    self.bottomRightAnnotationDisplay = True

    self.layoutManager = slicer.app.layoutManager()
    self.sliceCornerAnnotations = {}

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
    self.dicomAnnotationsCheckBox = qt.QCheckBox('DICOM Slice Annotations')
    parametersFormLayout.addRow(self.dicomAnnotationsCheckBox)

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

    # connections

    # Add vertical spacer
    self.layout.addStretch(1)
    self.dicomAnnotationsCheckBox.connect('clicked()', self.updateSliceViewFromGUI)

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

    if self.dicomAnnotationsCheckBox.checked:
      self.cornerActivationsGroupBox.enabled = True
      self.fontPropertiesGroupBox.enabled = True

      for sliceViewName in self.sliceViewNames:
        sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
        sl = sliceWidget.sliceLogic()
        #bl =sl.GetBackgroundLayer()
        self.makeAnnotationText(sl)
    else:
      self.cornerActivationsGroupBox.enabled = False
      self.fontPropertiesGroupBox.enabled = False

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
    self.blNodeObserverTag = {}
    sliceLogicObserverTag = {}
    self.sliceCornerAnnotations = {}

    self.sliceViewNames = self.layoutManager.sliceViewNames()
    for sliceViewName in self.sliceViewNames:
      sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
      self.sliceWidgets[sliceViewName] = sliceWidget
      sliceView = sliceWidget.sliceView()
      self.sliceViews[sliceViewName] = sliceView
      self.sliceCornerAnnotations[sliceViewName] = sliceView.cornerAnnotation()
      sl = sliceWidget.sliceLogic()
      bl = sl.GetBackgroundLayer()

      sliceLogicObserverTag[sliceViewName] = sl.AddObserver(vtk.vtkCommand.ModifiedEvent, 
                                              self.updateCornerAnnotations)

  def updateCornerAnnotations(self,caller,event):
    self.makeAnnotationText(caller)

  def sliceLogicModifiedEvent(self, caller, event):
    self.updateLayersAnnotation(caller)

  def makeLayersAnnotation(self, sliceLogic):
    foregroundOpacity = sliceLogic.GetForegroundOpacity()
    backgroundLayer = sliceLogic.GetBackgroundLayer()
    sliceNode = backgroundLayer.GetSliceNode()
    sliceViewName = sliceNode.GetLayoutName()

    backgroundVolume = backgroundLayer.GetVolumeNode()
    backgroundVolumeName = backgroundVolume.GetName()

    foregroundLayer = sliceLogic.GetBackgroundLayer()
    foregroundVolume = foregroundLayer.GetVolumeNode()
    foregroundVolumeName = foregroundVolume.GetName()

    bottomLeftAnnotation   = ''

    bottomLeftLines = []
    bottomLeftLines.append('Bg: '+ backgroundVolumeName)
    bottomLeftLines.append('Fg: '+ foregroundVolumeName)

    for lineNumber, line in enumerate(bottomLeftLines):
      if lineNumber < bottomLeftLines:
        bottomLeftAnnotation = bottomLeftAnnotation + line + '\n'

    sliceCornerAnnotation = self.sliceCornerAnnotations[sliceViewName]
    sliceCornerAnnotation.SetText(0, bottomLeftAnnotation)
    self.sliceViews[sliceViewName].scheduleRender()

  def makeAnnotationText(self, sliceLogic):

    backgroundLayer = sliceLogic.GetBackgroundLayer()
    foregroundLayer = sliceLogic.GetForegroundLayer()

    sliceNode = backgroundLayer.GetSliceNode()
    sliceViewName = sliceNode.GetLayoutName()

    backgroundVolume = backgroundLayer.GetVolumeNode()
    '''
    backgroundVolumeName = backgroundVolume.GetName()

    foregroundVolumeName = ''
    foregroundVolume = foregroundLayer.GetVolumeNode()
    foregroundVolumeName = foregroundVolume.GetName()

    sliceNode = backgroundLayer.GetSliceNode()

    bottomLeftAnnotation   = ''
    topLeftAnnotation = ''
    topRightAnnotation = ''
    '''

    backgroundVolumeNode = backgroundLayer.GetVolumeNode()
    if backgroundVolumeNode:
      self.foo(sliceLogic,backgroundVolumeNode,'background')
    else:
      self.backgroundVolumeName = 'None'
      self.backgroundDicomDic = {}
      self.topLeftLines =  ['']*7
      self.topRightLines =  ['']*5

    foregroundVolumeNode = foregroundLayer.GetVolumeNode()
    if foregroundVolumeNode:
      self.foo(sliceLogic,foregroundVolumeNode,'foreground')
    else:
      self.foregroundVolumeName = 'None'
      self.foregroundDicomDic = {}
      self.topLeftLines =  ['']*7
      self.topRightLines =  ['']*5

    labelLayer = sliceLogic.GetLabelLayer()
    labelVolumeNode = labelLayer.GetVolumeNode()
    if labelVolumeNode:
      self.foo(sliceLogic,labelVolumeNode,'label')
    else:
      self.labelVolumeName = 'None'
    '''
    bottomLeftLines = []
    bottomLeftLines.append('Bg: '+ backgroundVolumeName)
    bottomLeftLines.append('Fg: '+ foregroundVolumeName)

    for lineNumber, line in enumerate(bottomLeftLines):
      if lineNumber < bottomLeftLines:
        bottomLeftAnnotation = bottomLeftAnnotation + line + '\n'

    sliceCornerAnnotation = self.sliceCornerAnnotations[sliceViewName]
    sliceCornerAnnotation.SetText(0, bottomLeftAnnotation)
    sliceCornerAnnotation.SetText(2, topLeftAnnotation)
    sliceCornerAnnotation.SetText(3, topRightAnnotation)
    self.sliceViews[sliceViewName].scheduleRender()
    '''

  def foo(self, sliceLogic, volumeNode, role):

    backgroundLayer = sliceLogic.GetBackgroundLayer()
    sliceNode = backgroundLayer.GetSliceNode()
    sliceViewName = sliceNode.GetLayoutName()

    sliceCompositeNode = sliceLogic.GetSliceCompositeNode()
    foregroundOpacity = sliceCompositeNode.GetForegroundOpacity()
    labelOpacity = sliceCompositeNode.GetLabelOpacity()

    bottomLeftAnnotation   = ''
    bottomRightAnnotation   = ''
    topLeftAnnotation = ''
    topRightAnnotation = ''

    uids = volumeNode.GetAttribute('DICOM.instanceUIDs')
    if uids:
      uid = uids.partition(' ')[0]

      topLineNumbers = 10
      sliceHeight = self.sliceWidgets[sliceViewName].height
      if  sliceHeight < 300:
        topLineNumbers = 1
      elif 300 < sliceHeight < 320:
        topLineNumbers = 2
      elif 320 < sliceHeight < 340:
        topLineNumbers = 3
      elif 340 < sliceHeight < 360:
        topLineNumbers = 4

      if role == 'background' and foregroundOpacity == 0.0:

        # check if the dic is not empty
        #if len(self.backgroundDicomDic.keys()) == 0:
        self.backgroundDicomDic = self.extractDICOMValues(uid)

        #
        # Top Left Corner Annotations including:
        # Patient Name
        # Patient ID
        # Patient Birthdate, Age, Sex
        # Series Date
        # Series Time
        # Study ID
        # Study Description

        if self.topLeftAnnotationDisplay:
          self.topLeftLines[0] = self.backgroundDicomDic['Patient Name'].replace('^',', ')
          self.topLeftLines[1] = 'ID: ' + self.backgroundDicomDic ['Patient ID']
          val = self.backgroundDicomDic['Patient Birth Date']
          val = val[4:6] + '/' + val[6:]+ '/' + val[:4]
          self.topLeftLines[2] = self.backgroundDicomDic['Patient Birth Date'
              ] + ', ' + self.backgroundDicomDic['Patient Age'
                  ] + ', ' + self.backgroundDicomDic['Patient Sex']
          val = self.backgroundDicomDic['Study Date']
          self.topLeftLines[3] = val[4:6] + '/' + val[6:]+ '/' + val[:4]
          val = self.backgroundDicomDic['Study Time']
          studyH = val[:2]
          if int(studyH) > 12 :
            studyH = str (int(studyH) - 12)
            clockTime = ' PM'
          else:
            studyH = studyH
            clockTime = ' AM'
          studyM = val[2:4]
          studyS = val[4:6]
          self.topLeftLines[4] = studyH + ':' + studyM  + ':' + studyS +clockTime
          self.topLeftLines[5] = self.backgroundDicomDic['Series Description'
              ] + ' (' + self.backgroundDicomDic['Series Number'] + ')'
          self.topLeftLines[6] = ''

        #
        # Top Right Corner Annotations including:
        # Institution Name
        # Referring Physicians Name
        # Manufacturerer
        # Model
        # Patient Position
        #

        if (self.sliceWidgets[sliceViewName].width > 600 and self.topRightAnnotationDisplay):
          self.topRightLines[0] = self.backgroundDicomDic['Institution Name']
          val = self.backgroundDicomDic['Referring Physician Name']
          self.topRightLines[1] = 'Ref: ' + val.replace('^',', ')
          self.topRightLines[2] = self.backgroundDicomDic['Manufacturer']
          self.topRightLines[3] = self.backgroundDicomDic['Model']
          self.topRightLines[4] = self.backgroundDicomDic['Patient Position']

        #
        # Bottom Right Corner Annotations:
        # Modality Specific and Image Comments
        #
        if self.bottomRightAnnotationDisplay:
          bottomRightLines =  []
          modality = self.backgroundDicomDic['Modality']
          if modality == 'MR':
            bottomRightLines.append('TR ' + self.backgroundDicomDic['Repetition Time'])
            bottomRightLines.append('TE ' + self.backgroundDicomDic['Echo Time'])
          for line in bottomRightLines:
              bottomRightAnnotation = bottomRightAnnotation + line + '\n'

      elif role == 'foreground':
        # forground available
        # Check if bg volume is available
        self.topRightLines = ['']*5
        if self.backgroundVolumeName != 'None':
          #if len(self.foregroundDicomDic.keys()) == 0:
          self.foregroundDicomDic = self.extractDICOMValues(uid)
          if self.backgroundDicomDic['Patient ID'] != self.foregroundDicomDic['Patient ID']:
            self.topLeftLines =  ['']*8
          else:
            if self.backgroundDicomDic['Study ID'] != self.foregroundDicomDic['Study ID']:
              for i in xrange(3, 5):
                self.topLeftLines [i] = ''

            if self.backgroundDicomDic['Series Number'] != self.foregroundDicomDic['Series Number']:
              self.topLeftLines[5] = 'B: ' + self.backgroundDicomDic['Series Description'
                  ] + ' ('+ self.backgroundDicomDic['Series Number'] + ')'
              self.topLeftLines[6] = 'F: ' + self.foregroundDicomDic['Series Description'
                  ] + ' (' +self.foregroundDicomDic['Series Number'] + ')'

      for lineNumber, line in enumerate(self.topLeftLines):
        if lineNumber < topLineNumbers:
          if line != ('Unknown' and ''):
            topLeftAnnotation = topLeftAnnotation + line + '\n'

      for lineNumber, line in enumerate(self.topRightLines):
        if lineNumber < topLineNumbers:
          if line != ('Unknown' and ''):
            topRightAnnotation = topRightAnnotation + line + '\n'

    # bottomLeftLines
    bottomLeftLines = []
    if role == 'background':
      self.backgroundVolumeName = volumeNode.GetName()
    elif role == 'foreground':
      self.foregroundVolumeName = volumeNode.GetName()
    elif role == 'label':
      self.labelVolumeName = volumeNode.GetName()

    foregroundOpacityString = ''
    labelOpacityString = ''

    if self.foregroundVolumeName != 'None':
      foregroundOpacityString = ' (' + str(foregroundOpacity) + ')'
    if self.labelVolumeName != 'None':
      labelOpacityString = ' (' + str(labelOpacity) + ')'

    bottomLeftLines.append('L: '+ self.labelVolumeName + labelOpacityString)
    bottomLeftLines.append('F: '+ self.foregroundVolumeName + foregroundOpacityString)
    bottomLeftLines.append('B: '+ self.backgroundVolumeName)

    for lineNumber, line in enumerate(bottomLeftLines):
      if lineNumber < bottomLeftLines:
        bottomLeftAnnotation = bottomLeftAnnotation + line + '\n'

    sliceCornerAnnotation = self.sliceCornerAnnotations[sliceViewName]
    sliceCornerAnnotation.SetText(0, bottomLeftAnnotation)
    sliceCornerAnnotation.SetText(1, bottomRightAnnotation)
    sliceCornerAnnotation.SetText(2, topLeftAnnotation)
    sliceCornerAnnotation.SetText(3, topRightAnnotation)
    self.sliceViews[sliceViewName].scheduleRender()

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
    "0008,1030": "Study Description",
    "0008,103e": "Series Description",
    "0008,1090": "Model",
    "0010,0010": "Patient Name",
    "0010,0020": "Patient ID",
    "0010,0030": "Patient Birth Date",
    "0010,0040": "Patient Sex",
    "0010,1010": "Patient Age",
    "0010,4000": "Patient Comments",
    "0018,1030": "Protocol Name",
    "0018,5100": "Patient Position",
    "0020,0010": "Study ID",
    "0020,0011": "Series Number",
    "0020,4000": "Image Comments"
    }
    p = self.extractTagValue(p, tags)
    if self.bottomLeftAnnotationDisplay:
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
