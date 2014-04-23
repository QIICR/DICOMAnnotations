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
    self.dicomAnnotationsCheckBox = qt.QCheckBox('DICOM Annotations')
    parametersFormLayout.addRow(self.dicomAnnotationsCheckBox)
    self.dicomAnnotationsCheckBox.connect('clicked()', self.updateSliceViewFromGUI)

    # connections

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def updateSliceViewFromGUI(self):

    # Create corner annotations if have not created already
    if len(self.sliceCornerAnnotations.items()) == 0:
      self.createCornerAnnotations()

    if self.dicomAnnotationsCheckBox.checked:
      for sliceViewName in self.sliceViewNames:
        sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
        sl = sliceWidget.sliceLogic()
        bl =sl.GetBackgroundLayer()
        self.makeAnnotationText(bl)
    else:
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
    self.sliceCornerAnnotations = {}

    self.sliceViewNames = self.layoutManager.sliceViewNames()
    for sliceViewName in self.sliceViewNames:
      sliceWidget = self.layoutManager.sliceWidget(sliceViewName)
      self.sliceWidgets[sliceViewName] = sliceWidget
      sliceView = sliceWidget.sliceView()
      self.sliceViews[sliceViewName] = sliceView
      self.sliceCornerAnnotations[sliceViewName] = sliceView.cornerAnnotation()
      self.sliceCornerAnnotations[sliceViewName].SetMaximumFontSize(14)
      self.sliceCornerAnnotations[sliceViewName].SetMinimumFontSize(14)
      textProperty = self.sliceCornerAnnotations[sliceViewName].GetTextProperty()
      textProperty.SetFontFamilyToTimes()
      sl = sliceWidget.sliceLogic()
      bl = sl.GetBackgroundLayer()
      self.blNodeObserverTag[sliceViewName] = bl.AddObserver(vtk.vtkCommand.ModifiedEvent, 
                                              self.updateCornerAnnotations)

  def updateCornerAnnotations(self,caller,event):
    self.makeAnnotationText(caller)

  def makeAnnotationText(self, backgroundLayout):
    sliceNode = backgroundLayout.GetSliceNode()
    sliceViewName = sliceNode.GetLayoutName()

    topLeftAnnotation = ''
    topRightAnnotation = ''
    volumeNode = backgroundLayout.GetVolumeNode()
    if volumeNode:
      uids = volumeNode.GetAttribute('DICOM.instanceUIDs')
      if uids:
        uid = uids.partition(' ')[0]
        p = self.extractDICOMValues(uid)

        topRightLines =  []
        topRightLines.append(p['Patient Name'].replace('^',', '))
        if p['Patient Birth Date'] != 'Unknown':
          p['Patient Birth Date'] = p['Patient Birth Date'][4:6] + '/' + p['Patient Birth Date'][6:]+ '/' + p['Patient Birth Date'][:4]
        topRightLines.append(p['Patient Birth Date'] + ', ' + p['Patient Age'] + ', ' + p['Patient Sex'])
        if p['Series Date'] != 'Unknown':
          topRightLines.append(p['Series Date'][4:6] + '/' + p['Series Date'][6:]+ '/' + p['Series Date'][:4])
        else:
          topRightLines.append(p['Series Date'])
        if p['Series Time'] != 'Unknown':
          topRightLines.append(p['Series Time'][:2] + ':' + p['Series Time'][2:4] + ':' + p['Series Time'][4:6])
        else:
          topRightLines.append(p['Series Time'])
        topRightLines.append('Study ID: ' + p['Study ID'])

        sliceHeight = self.sliceWidgets[sliceViewName].height

        if  sliceHeight < 300:
          topLineNumbers = 1
        elif 300 < sliceHeight < 320:
          topLineNumbers = 2
        elif 320 < sliceHeight < 340:
          topLineNumbers = 3
        elif 340 < sliceHeight < 360:
          topLineNumbers = 4
        else:
          topLineNumbers = 10

        for lineNumber, line in enumerate(topRightLines):
          if lineNumber < topLineNumbers:
            topRightAnnotation = topRightAnnotation + line + '\n'


        if self.sliceWidgets[sliceViewName].width > 600:
          #topLeftAnnotation = p['Institution Name'] +'\n' + p['Referring Physician Name'].replace('^',', ')
          topLeftLines =  []
          topLeftLines.append(p['Institution Name'])
          topLeftLines.append(p['Referring Physician Name'].replace('^',', '))
          topLeftLines.append(p['Manufacturer'])
          topLeftLines.append(p['Model'])
          for lineNumber, line in enumerate(topLeftLines):
            if lineNumber < topLineNumbers:
              topLeftAnnotation = topLeftAnnotation + line + '\n'

    self.sliceCornerAnnotations[sliceViewName].SetText(2, topRightAnnotation)
    self.sliceCornerAnnotations[sliceViewName].SetText(3, topLeftAnnotation)
    self.sliceViews[sliceViewName].scheduleRender()

  def extractDICOMValues(self,uid):
    slicer.dicomDatabase.loadInstanceHeader(uid)
    p ={}
    tags = {
    "0008,0080": "Institution Name",
    "0008,0090": "Referring Physician Name",
    "0010,0010": "Patient Name",
    "0010,0020": "Patient ID",
    "0010,0030": "Patient Birth Date",
    "0010,0040": "Patient Sex",
    "0010,1010": "Patient Age",
    "0010,4000": "Patient Comments",
    "0018,1030": "Protocol Name",
    "0020,0010": "Study ID",
    "0008,0021": "Series Date",
    "0008,0031": "Series Time",
    "0008,1030": "Study Description",
    "0008,0060": "Modality",
    "0008,0070": "Manufacturer",
    "0008,1090": "Model"
    }
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
