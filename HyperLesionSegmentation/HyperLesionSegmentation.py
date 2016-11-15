import os
import sys
import platform
import unittest

from os.path import expanduser

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# HyperLesionSegmentation
#

class HyperLesionSegmentation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent) # TODO EDITAR QUANDO ESTIVER PRONTO - DEFINIR NOME!!!
    self.parent.title = "HyperLesionSegmentation" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# HyperLesionSegmentationWidget
#

class HyperLesionSegmentationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Input Parameters Area
    #
    parametersInputCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersInputCollapsibleButton.text = "Input/Output Parameters"
    self.layout.addWidget(parametersInputCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersInputFormLayout = qt.QFormLayout(parametersInputCollapsibleButton)

    # #
    # # input T1 volume selector
    # #
    # self.inputT1Selector = slicer.qMRMLNodeComboBox()
    # self.inputT1Selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    # self.inputT1Selector.selectNodeUponCreation = False
    # self.inputT1Selector.addEnabled = False
    # self.inputT1Selector.removeEnabled = True
    # self.inputT1Selector.noneEnabled = True
    # self.inputT1Selector.showHidden = False
    # self.inputT1Selector.showChildNodeTypes = False
    # self.inputT1Selector.setMRMLScene(slicer.mrmlScene)
    # self.inputT1Selector.setToolTip("T1 Volume")
    # parametersInputFormLayout.addRow("T1 Volume ", self.inputT1Selector)

    #
    # input FLAIR volume selector
    #
    self.inputFLAIRSelector = slicer.qMRMLNodeComboBox()
    self.inputFLAIRSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputFLAIRSelector.selectNodeUponCreation = False
    self.inputFLAIRSelector.addEnabled = False
    self.inputFLAIRSelector.removeEnabled = True
    self.inputFLAIRSelector.noneEnabled = False
    self.inputFLAIRSelector.showHidden = False
    self.inputFLAIRSelector.showChildNodeTypes = False
    self.inputFLAIRSelector.setMRMLScene(slicer.mrmlScene)
    self.inputFLAIRSelector.setToolTip("T2-FLAIR Volume")
    parametersInputFormLayout.addRow("T2-FLAIR Volume ", self.inputFLAIRSelector)

    #
    # output label selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.renameEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = False
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene(slicer.mrmlScene)
    self.outputSelector.setToolTip(
      "Output a global lesion mask.")
    parametersInputFormLayout.addRow("Lesion Label ", self.outputSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersInputFormLayout.addRow(self.applyButton)

    #
    # Noise Attenuation Parameters Area
    #
    parametersNoiseAttenuationCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersNoiseAttenuationCollapsibleButton.text = "Noise Attenuation Parameters"
    self.layout.addWidget(parametersNoiseAttenuationCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersNoiseAttenuationFormLayout = qt.QFormLayout(parametersNoiseAttenuationCollapsibleButton)

    #
    # Filtering Parameters: Condutance
    #
    self.setFilteringCondutanceWidget = ctk.ctkSliderWidget()
    self.setFilteringCondutanceWidget.maximum=30
    self.setFilteringCondutanceWidget.minimum=0
    self.setFilteringCondutanceWidget.value=15
    self.setFilteringCondutanceWidget.singleStep = 1
    self.setFilteringCondutanceWidget.setToolTip("Condutance parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Condutance ", self.setFilteringCondutanceWidget)

    #
    # Filtering Parameters: Number of iterations
    #
    self.setFilteringNumberOfIterationWidget = ctk.ctkSliderWidget()
    self.setFilteringNumberOfIterationWidget.maximum =50
    self.setFilteringNumberOfIterationWidget.minimum =0
    self.setFilteringNumberOfIterationWidget.value=5
    self.setFilteringNumberOfIterationWidget.singleStep = 1
    self.setFilteringNumberOfIterationWidget.setToolTip("Number of iterations parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Number Of Iterations ", self.setFilteringNumberOfIterationWidget)

    #
    # Filtering Parameters: Q value
    #
    self.setFilteringQWidget = ctk.ctkSliderWidget()
    self.setFilteringQWidget.singleStep = 0.1
    self.setFilteringQWidget.minimum = 0.0
    self.setFilteringQWidget.maximum = 2.0
    self.setFilteringQWidget.value = 1.2
    self.setFilteringQWidget.setToolTip("Q value parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Q Value ", self.setFilteringQWidget)

    #
    # Registration Parameters Area
    #
    parametersRegistrationCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersRegistrationCollapsibleButton.text = "Registration Parameters"
    self.layout.addWidget(parametersRegistrationCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersRegistrationFormLayout = qt.QFormLayout(parametersRegistrationCollapsibleButton)

    # #
    # # Percentage Sampling Area
    # #
    # self.setPercSamplingQWidget = qt.QDoubleSpinBox()
    # self.setPercSamplingQWidget.setMaximum(1)
    # self.setPercSamplingQWidget.setMinimum(0.0001)
    # self.setPercSamplingQWidget.setSingleStep(0.001)
    # self.setPercSamplingQWidget.setValue(0.002)
    # self.setPercSamplingQWidget.setToolTip("Percentage of voxel used in registration.")
    # parametersRegistrationFormLayout.addRow("Percentage Of Samples ", self.setPercSamplingQWidget)

    # #
    # # Initiation Method Area
    # #
    # self.setThresholdLFMethodBooleanWidget = ctk.ctkComboBox()
    # self.setThresholdLFMethodBooleanWidget.addItem("Off")
    # self.setThresholdLFMethodBooleanWidget.addItem("CenterOfHead")
    # self.setThresholdLFMethodBooleanWidget.setToolTip(
    #   "")
    # parametersRegistrationFormLayout.addRow("Initiation Method ", self.setThresholdLFMethodBooleanWidget)

    #
    # Interpolation Method Area
    #
    self.setInterpolationMethodBooleanWidget = ctk.ctkComboBox()
    self.setInterpolationMethodBooleanWidget.addItem("Linear")
    self.setInterpolationMethodBooleanWidget.addItem("BSpline")
    self.setInterpolationMethodBooleanWidget.addItem("NearestNeighbor")
    self.setInterpolationMethodBooleanWidget.setToolTip(
      "Choose the interpolation method used to register the input images into the standard space. Options: Linear, Tri-linear and Spline")
    parametersAdvancedFormLayout.addRow("Interpolation ", self.setInterpolationMethodBooleanWidget)

    # TODO Terminar de colocar o coregistro

    #
    # Lesion Enhancement Function Parameters Area
    #
    parametersLesionEnhancementCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersLesionEnhancementCollapsibleButton.text = "Lesion Enhancement Function Parameters"
    self.layout.addWidget(parametersLesionEnhancementCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersLesionEnhancementFormLayout = qt.QFormLayout(parametersLesionEnhancementCollapsibleButton)

    #
    # Threshold Method Area
    #
    self.setThresholdLFMethodBooleanWidget = ctk.ctkComboBox()
    self.setThresholdLFMethodBooleanWidget.addItem("MaximumEntropy")
    self.setThresholdLFMethodBooleanWidget.addItem("Otsu")
    # self.setThresholdLFMethodBooleanWidget.addItem("NearestNeighbor")
    self.setThresholdLFMethodBooleanWidget.setToolTip(
      "Choose the threhsold method for the lesion enhancement procedure. Options: MaximumEntropy, Otsu")
    parametersLesionEnhancementFormLayout.addRow("Threshold Method ", self.setThresholdLFMethodBooleanWidget)








    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputFLAIRSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputFLAIRSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = HyperLesionSegmentationLogic()
    # enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    # imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(self.inputFLAIRSelector.currentNode()
              ,self.outputSelector.currentNode()
              ,self.setInterpolationMethodBooleanWidget
              )

#
# HyperLesionSegmentationLogic
#

class HyperLesionSegmentationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True


  def run(self, inputFLAIRVolume, outputLabel):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputFLAIRVolume, outputLabel):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')
    slicer.util.showStatusMessage("Processing started")

    #################################################################################################################
    #                                        Registration  - MNI to FLAIR                                           #
    #################################################################################################################
    if platform.system() is "Windows":
      home = expanduser("%userprofile%")
    else:
      home = expanduser("~")

    MNITemplate = slicer.util.loadVolume(
      home + '/MSLesionTrack-Data/DTI-Templates/MNI152_T1_1mm_brain.nii.gz')
    MNITemplateNodeName = "MNI152_T1_1mm_brain"

    # Parameter(0 / 0): fixedVolume(Fixed
    # Parameter(0 / 1): movingVolume(Moving
    # Parameter(0 / 2): samplingPercentage(Percentage
    # Parameter(0 / 3): splineGridSize(B - Spline
    # # Parameter(1 / 0): linearTransform(Slicer
    # # Linear
    # # Transform)
    # # Parameter(1 / 1): bsplineTransform(Slicer
    # # BSpline
    # # Transform)
    # Parameter(1 / 2): outputVolume(Output
    # Parameter(2 / 1): initializeTransformMode(Initialize
    # Transform
    # Mode)
    # Parameter(3 / 0): useRigid(Rigid(6
    # Parameter(3 / 3): useAffine(Affine(12
    # Parameter(3 / 4): useBSpline(BSpline( > 27
    # Parameter(5 / 5): interpolationMode(Interpolation
    # Parameter(7 / 2): numberOfHistogramBins(Histogram
    # Parameter(7 / 4): costMetric(Cost
    #
    # Registering the FLAIR image to T1 image.
    #
    slicer.util.showStatusMessage("Step 1/...: MNI152 to T2-FLAIR registration...")
    registrationFLAIR2T1Transform = slicer.vtkMRMLLinearTransformNode()
    # slicer.mrmlScene.AddNode(registrationFLAIR2T1Transform)
    MNINativeVolume = slicer.vtkMRMLScalarVolumeNode()
    # slicer.mrmlScene.AddNode(inputFLAIRVolume_reg)
    regParams = {}
    regParams["fixedVolume"] = inputFLAIRVolume.GetID()
    regParams["movingVolume"] = slicer.util.getNode(DTITemplateNodeName)
    regParams["samplingPercentage"] = 0.02
    regParams["splineGridSize"] = '14,10,12'
    regParams["outputVolume"] = MNINativeVolume.GetID()
    regParams["linearTransform"] = registrationFLAIR2T1Transform.GetID()
    regParams["initializeTransformMode"] = "useMomentsAlign"
    regParams["useRigid"] = True
    regParams["useAffine"] = True
    regParams["interpolationMode"] = interpolationMethod.currentText
    regParams["numberOfSamples"] = 200000

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                              White Matter Mask                                                #
    #################################################################################################################

    # Parameter(0 / 0): inputVolume(Input
    # Parameter(0 / 1): outputLabel(Brain
    # Parameter(1 / 0): oneTissue(Separate
    # Parameter (1 / 1): typeTissue(Tissue)
    # Parameter(2 / 0): segMethod(Segmentation
    # Parameter(2 / 1): numClass(Number
    #
    # White Matter Mask.
    #
    slicer.util.showStatusMessage("Step 2/...: Extracting the White Matter mask...")
    wmLabelVolume = slicer.vtkMRMLLabelVolumeNode()
    # slicer.mrmlScene.AddNode(inputFLAIRVolume_reg)
    regParams = {}
    regParams["inputVolume"] = MNINativeVolume.GetID()
    regParams["outputLabel"] = wmLabelVolume.GetID()
    regParams["oneTissue"] = True
    regParams["typeTissue"] = "White Matter"
    regParams["segMethod"] = "KMeans"
    regParams["numClass"] = 4

    slicer.cli.run(slicer.modules.braintissuesmask, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                              White Matter Mask                                                #
    #################################################################################################################


    slicer.util.showStatusMessage("Processing completed")
    logging.info('Processing completed')

    return True


class HyperLesionSegmentationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_HyperLesionSegmentation1()

  def test_HyperLesionSegmentation1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
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
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = HyperLesionSegmentationLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
