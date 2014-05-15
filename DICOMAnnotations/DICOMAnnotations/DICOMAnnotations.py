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
    #print 'update sliceview from gui'

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
        self.foo2(sl)
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

    #print 'create corner annotations'
    self.sliceViewNames = []
    self.sliceWidgets = {}
    self.sliceViews = {}
    self.blNodeObserverTag = {}
    self.sliceLogicObserverTag = {}
    self.sliceCornerAnnotations = {}

    sliceViewNames = self.layoutManager.sliceViewNames()

    for sliceViewName in sliceViewNames:
      self.sliceViewNames.append(sliceViewName)
    for sliceViewName in self.sliceViewNames:
      self.addObserver(sliceViewName)

  def addObserver(self, sliceViewName):
    sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
    self.sliceWidgets[sliceViewName] = sliceWidget
    sliceView = sliceWidget.sliceView()
    self.sliceViews[sliceViewName] = sliceView
    self.sliceCornerAnnotations[sliceViewName] = sliceView.cornerAnnotation()
    sliceLogic = sliceWidget.sliceLogic()

    self.sliceLogicObserverTag[sliceViewName] = sliceLogic.AddObserver(vtk.vtkCommand.ModifiedEvent, 
                                              self.updateCornerAnnotations)

  def updateCornerAnnotations(self,caller,event):

    sliceViewNames = self.layoutManager.sliceViewNames()
    for sliceViewName in sliceViewNames:
      if sliceViewName not in self.sliceViewNames:
        self.sliceViewNames.append(sliceViewName)
        self.addObserver(sliceViewName)
        self.updateSliceViewFromGUI()

    self.foo2(caller)

  def sliceLogicModifiedEvent(self, caller, event):
    self.updateLayersAnnotation(caller)

  def makeAnnotationText(self, sliceLogic):

    backgroundLayer = sliceLogic.GetBackgroundLayer()
    foregroundLayer = sliceLogic.GetForegroundLayer()

    sliceNode = backgroundLayer.GetSliceNode()
    sliceViewName = sliceNode.GetLayoutName()
    self.currentSliceViewName = sliceNode.GetLayoutName()

    backgroundVolume = backgroundLayer.GetVolumeNode()

    backgroundVolumeNode = backgroundLayer.GetVolumeNode()
    if backgroundVolumeNode:
      self.foo2(sliceLogic,backgroundVolumeNode,'background')
    else:
      self.backgroundVolumeName = 'None'
      self.backgroundDicomDic = {}
      self.topLeftLines =  ['']*7
      self.topRightLines =  ['']*5

    foregroundVolumeNode = foregroundLayer.GetVolumeNode()
    if foregroundVolumeNode:
      self.foo2(sliceLogic,foregroundVolumeNode,'foreground')
    else:
      self.foregroundVolumeName = 'None'
      self.foregroundDicomDic = {}
      self.topLeftLines =  ['']*7
      self.topRightLines =  ['']*5

    labelLayer = sliceLogic.GetLabelLayer()
    labelVolumeNode = labelLayer.GetVolumeNode()
    if labelVolumeNode:
      self.foo2(sliceLogic,labelVolumeNode,'label')
    else:
      self.labelVolumeName = 'None'

  def foo2(self, sliceLogic):

    #print 'foo2'
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
        self.foo4(bgUid,fgUid)
      else:
        for key in self.cornerTexts[2]:
          self.cornerTexts[2][key] = ''

    # Only background
    elif (backgroundVolume != None):
      #print 'only bg is present'
      backgroundVolumeName = backgroundVolume.GetName()
      if self.bottomLeftAnnotationDisplay:
        self.cornerTexts[0]['3-Background'] = 'B: ' + backgroundVolumeName

      if self.topLeftAnnotationDisplay:
        uids = backgroundVolume.GetAttribute('DICOM.instanceUIDs')
        if uids:
          uid = uids.partition(' ')[0]
          self.foo4(uid,None)

    # Only foreground
    elif (foregroundVolume != None):
      if self.bottomLeftAnnotationDisplay:
        foregroundVolumeName = foregroundVolume.GetName()
        self.cornerTexts[0]['2-Foreground'] = 'F: ' + foregroundVolumeName

      if self.topLeftAnnotationDisplay:
        uids = foregroundVolume.GetAttribute('DICOM.instanceUIDs')
        if uids:
          uid = uids.partition(' ')[0]
          # passed UID as bg
          self.foo4(uid,None)

    if (labelVolume != None):
      labelOpacity = sliceCompositeNode.GetLabelOpacity()
      labelVolumeName = labelVolume.GetName()
      self.cornerTexts[0]['1-Label'] = 'L: ' + labelVolumeName + ' (' + str(
                    "%.1f"%labelOpacity) + ')'

    self.drawCornerAnnotations()
    #labelOpacity = sliceCompositeNode.GetLabelOpacity()

  def foo4(self,bgUid,fgUid):

    if fgUid != None and bgUid != None:
      backgroundDicomDic = self.extractDICOMValues(bgUid)
      foregroundDicomDic = self.extractDICOMValues(fgUid)
      # check if background and foreground are from different patients
      # and remove the annotations
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
