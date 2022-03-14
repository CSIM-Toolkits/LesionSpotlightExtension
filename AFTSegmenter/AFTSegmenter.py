# Copyright 2016 Antonio Carlos da Silva Senra Filho
#
# Licensed under the Apache License, Version 2.0(the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http: // www.apache.org / licenses / LICENSE - 2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import os
import unittest
import sys
import platform
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# AFTSegmenter
#

class AFTSegmenter(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "AFT Segmenter" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Segmentation"]
    self.parent.dependencies = []
    self.parent.contributors = ["Antonio Carlos Senra Filho (University of Sao Paulo), Luiz Otavio Murta Junior (University of Sao Paulo)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module offer a simple implamentation of MS lesion segmentation method described by Cabezas M. et al. paper (2014)
    "Automatic multiple sclerosis lesion detection in brain MRI by FLAIR thresholding", Computer Methods and Programs in
    Biomedicine, DOI: 10.1016/j.cmpb.2014.04.006.
    More details about the modules functionalities and how to use it, please check the wiki page: https://www.slicer.org/wiki/Documentation/Nightly/Extensions/LesionSpotlight
    """
    self.parent.acknowledgementText = """
    This work was originally developed by Antonio Carlos Senra Filho, CSIM Lab. and was partially funded by CNPq grant 201871/2015-7/SWE and CAPES.
""" # replace with organization, grant and thanks.

#
# AFTSegmenterWidget
#

class AFTSegmenterWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    # ScriptedLoadableModuleWidget.setup(self)
    #
    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Input Parameters Area
    #
    parametersInputCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersInputCollapsibleButton.text = "Input/Output Parameters"
    self.layout.addWidget(parametersInputCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersInputFormLayout = qt.QFormLayout(parametersInputCollapsibleButton)

    # TODO pensar em dar um upgrade no algoritmo...colocar um tratamento de imagem similar ao BET, fazendo um histograma cumulativo e retirar os valores menores que 2% e maiores que 98%...assim retira o sinal outlier da imagem que pode dar problema para estimar a curva sigmoidal...caso estranho no dado MICCAI2016 SATH

    #
    # input T1 volume selector
    #
    self.inputT1Selector = slicer.qMRMLNodeComboBox()
    self.inputT1Selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputT1Selector.selectNodeUponCreation = False
    self.inputT1Selector.addEnabled = False
    self.inputT1Selector.removeEnabled = True
    self.inputT1Selector.noneEnabled = False
    self.inputT1Selector.showHidden = False
    self.inputT1Selector.showChildNodeTypes = False
    self.inputT1Selector.setMRMLScene(slicer.mrmlScene)
    self.inputT1Selector.setToolTip("T1 Volume")
    parametersInputFormLayout.addRow("T1 Volume ", self.inputT1Selector)

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
    # Is brain extracted?
    #
    self.setIsBETWidget = ctk.ctkCheckBox()
    self.setIsBETWidget.setChecked(False)
    self.setIsBETWidget.setToolTip(
      "Is the input data (T1 and T2-FLAIR) already brain extracted?")
    parametersInputFormLayout.addRow("Is brain extracted?",
                                     self.setIsBETWidget)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersInputFormLayout.addRow(self.applyButton)

    #
    # Segmentation Parameters Area
    #
    parametersSegmentationParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersSegmentationParametersCollapsibleButton.text = "Segmentation Parameters"
    self.layout.addWidget(parametersSegmentationParametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersSegmentationFormLayout = qt.QFormLayout(parametersSegmentationParametersCollapsibleButton)

    #
    # Absolute Error Threshold
    #
    self.setAbsErrorThresholdWidget = ctk.ctkSliderWidget()
    self.setAbsErrorThresholdWidget.singleStep = 0.01
    self.setAbsErrorThresholdWidget.minimum = 0.01
    self.setAbsErrorThresholdWidget.maximum = 0.99
    self.setAbsErrorThresholdWidget.value = 0.1
    self.setAbsErrorThresholdWidget.setToolTip(
      "Define the absolute error threshold for gray matter statistics. This measure evaluated the similarity between the MNI152 template "
      "and the T2-FLAIR gray matter fluctuation estimative. A higher error gives a higher variability in the final lesion segmentation.")
    parametersSegmentationFormLayout.addRow("Absolute Error Threshold", self.setAbsErrorThresholdWidget)

    #
    # Gamma Search Matching
    #
    self.setGammaWidget = ctk.ctkSliderWidget()
    self.setGammaWidget.minimum = 0.1
    self.setGammaWidget.maximum = 4.0
    self.setGammaWidget.singleStep = 0.1
    self.setGammaWidget.value = 2.0
    self.setGammaWidget.setToolTip(
      "Define the outlier detection based on units of standard deviation in the T2-FLAIR gray matter voxel intensity distribution.")
    parametersSegmentationFormLayout.addRow("Gamma ", self.setGammaWidget)

    #
    # White Matter Search Matching
    #
    self.setWMMatchWidget = ctk.ctkSliderWidget()
    self.setWMMatchWidget.minimum = 0.1
    self.setWMMatchWidget.maximum = 1.0
    self.setWMMatchWidget.singleStep = 0.1
    self.setWMMatchWidget.value = 0.6
    self.setWMMatchWidget.setToolTip("Set the local neighborhood searching for label refinement step. This metric defines the percentage of white matter"
                                     " tissue surrounding the hyperintense lesions. Large values defines a conservative segmentation, i.e. in order to define a true MS lesion"
                                     "it must be close to certain percentage of white matter area.")
    parametersSegmentationFormLayout.addRow("White Matter Matching ", self.setWMMatchWidget)

    #
    # Minimum Lesion Size
    #
    self.setMinimumLesionWidget = qt.QSpinBox()
    self.setMinimumLesionWidget.setMinimum(1)
    self.setMinimumLesionWidget.setMaximum(5000)
    self.setMinimumLesionWidget.setValue(10)
    self.setMinimumLesionWidget.setToolTip(
      "Set the minimum lesion size adopted as a true lesion in the final lesion map. Units given in number of voxels.")
    parametersSegmentationFormLayout.addRow("Minimum Lesion Size ", self.setMinimumLesionWidget)

    #
    # Gray Matter Label
    #
    self.setGMLabelWidget = qt.QSpinBox()
    self.setGMLabelWidget.setMinimum(1)
    self.setGMLabelWidget.setMaximum(255)
    self.setGMLabelWidget.setValue(2)
    self.setGMLabelWidget.setToolTip(
      "Set the mask value that represents the gray matter. Default is defined based on the Basic Brain Tissues module output.")
    parametersSegmentationFormLayout.addRow("Gray Matter Label Value ", self.setGMLabelWidget)

    #
    # Minimum Lesion Size
    #
    self.setWMLabelWidget = qt.QSpinBox()
    self.setWMLabelWidget.setMinimum(1)
    self.setWMLabelWidget.setMaximum(255)
    self.setWMLabelWidget.setValue(3)
    self.setWMLabelWidget.setToolTip(
      "et the mask value that represents the white matter. Default is defined based on the Basic Brain Tissues module output.")
    parametersSegmentationFormLayout.addRow("White Matter Label Value ", self.setWMLabelWidget)


    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputT1Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputFLAIRSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputT1Selector.currentNode() and self.outputSelector.currentNode() and self.inputFLAIRSelector.currentNode()

  def onApplyButton(self):
    logic = AFTSegmenterLogic()
    # enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    # imageThreshold = self.imageThresholdSliderWidget.value
    isBET=self.setIsBETWidget.isChecked()
    absError=self.setAbsErrorThresholdWidget.value
    gamma=self.setGammaWidget.value
    WMMath=self.setWMMatchWidget.value
    minLesionSize=self.setMinimumLesionWidget.value
    GMLabel=self.setGMLabelWidget.value
    WMLabel=self.setWMLabelWidget.value
    logic.run(self.inputT1Selector.currentNode(), self.inputFLAIRSelector.currentNode(), self.outputSelector.currentNode(), isBET,
              absError,gamma,WMMath,minLesionSize,GMLabel,WMLabel)

#
# AFTSegmenterLogic
#

class AFTSegmenterLogic(ScriptedLoadableModuleLogic):
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

  def run(self, inputT1Volume, inputFLAIRVolume, outputVolume, isBET, absError, gamma, WMMath, minLesionSize, GMlabel, WMLabel):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputT1Volume, outputVolume):
      slicer.util.errorDisplay('Input T1 volume is the same as output volume. Choose a different output volume.')
      return False

    if not self.isValidInputOutputData(inputFLAIRVolume, outputVolume):
      slicer.util.errorDisplay('Input FLAIR volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Creating FLAIR image copy for processing pipeline
    inputFLAIRVolume_tmp = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(inputFLAIRVolume_tmp)
    inputT1Volume_tmp = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(inputT1Volume_tmp)
    slicer.util.showStatusMessage("Step 1: Bias field correction...")
    #################################################################################################################
    #                                              Image Processing                                                 #
    #################################################################################################################
    #################################################################################################################
    #                                    T2-FLAIR Bias Field Correction                                             #
    #################################################################################################################

    regParams = {}
    regParams["inputImageName"] = inputFLAIRVolume.GetID()
    regParams["outputImageName"] = inputFLAIRVolume_tmp.GetID()

    slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                    T1 Bias Field Correction                                             #
    #################################################################################################################

    regParams = {}
    regParams["inputImageName"] = inputT1Volume.GetID()
    regParams["outputImageName"] = inputT1Volume_tmp.GetID()

    slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)


    # Get the path to LSSegmenter-Data files
    path2files = os.path.dirname(slicer.modules.lssegmenter.path)

    #################################################################################################################
    #                                        Registration  - MNI to Native space                                    #
    #################################################################################################################
    if platform.system() == "Windows":
      if isBET:
        (read, MNITemplateNode) = slicer.util.loadVolume(
          path2files + '\\Resources\\LSSegmenter-Data\\MNI152_T1_1mm_brain.nii.gz',
          {}, True)
      else:
        (read, MNITemplateNode) = slicer.util.loadVolume(
          path2files + '\\Resources\\LSSegmenter-Data\\MNI152_T1_1mm.nii.gz', {},
          True)
    else:
      if isBET:
        (read, MNITemplateNode) = slicer.util.loadVolume(
          path2files + '/Resources/LSSegmenter-Data/MNI152_T1_1mm_brain.nii.gz', {},
          True)
      else:
        (read, MNITemplateNode) = slicer.util.loadVolume(
          path2files + '/Resources/LSSegmenter-Data/MNI152_T1_1mm.nii.gz', {}, True)

    #
    # Registering the FLAIR to T1 space.
    #
    slicer.util.showStatusMessage("Step 2: FLAIR to T1 space registration...")

    regParams = {}
    regParams["fixedVolume"] = inputT1Volume.GetID()
    regParams["movingVolume"] = inputFLAIRVolume_tmp.GetID()
    regParams["outputVolume"] = inputFLAIRVolume_tmp.GetID()
    regParams["samplingPercentage"] = 0.02
    regParams["splineGridSize"] = '8,8,8'
    regParams["initializeTransformMode"] = "useMomentsAlign"
    regParams["useRigid"] = True
    # regParams["useAffine"] = True
    # regParams["useBSpline"] = True
    regParams["interpolationMode"] = "Linear"

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    #
    # Registering the MNI template to native space.
    #
    registrationMNI2NativeTransform = slicer.vtkMRMLLinearTransformNode()
    registrationMNI2NativeTransform.SetName("regMNI2Native_linear")
    slicer.mrmlScene.AddNode(registrationMNI2NativeTransform)
    slicer.util.showStatusMessage("Step 3: MNI152 to native space registration...")

    regParams = {}
    regParams["fixedVolume"] = inputT1Volume_tmp.GetID()
    regParams["movingVolume"] = MNITemplateNode.GetID()
    regParams["outputVolume"] = MNITemplateNode.GetID()
    regParams["samplingPercentage"] = 0.02
    regParams["splineGridSize"] = '8,8,8'
    regParams["linearTransform"] = registrationMNI2NativeTransform.GetID()
    regParams["initializeTransformMode"] = "useMomentsAlign"
    regParams["useRigid"] = True
    regParams["useAffine"] = True
    regParams["useBSpline"] = True
    regParams["interpolationMode"] = "Linear"

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    if platform.system() == "Windows":
      (read, MNIBrainTissues) = slicer.util.loadLabelVolume(
        path2files + '\\Resources\\LSSegmenter-Data\\MNI152_T1_1mm_brain_tissues.nii.gz', {}, True)
    else:
      (read, MNIBrainTissues) = slicer.util.loadLabelVolume(
        path2files + '/Resources/LSSegmenter-Data/MNI152_T1_1mm_brain_tissues.nii.gz', {}, True)

    slicer.util.showStatusMessage("Step 4: MNI brain template conforming...")
    params = {}
    params["inputVolume"] = MNIBrainTissues.GetID()
    params["referenceVolume"] = inputT1Volume_tmp.GetID()
    params["outputVolume"] = MNIBrainTissues.GetID()
    params["transformationFile"] = registrationMNI2NativeTransform.GetID()
    params["inverseITKTransformation"] = False
    params["interpolationType"] = "nn"

    slicer.cli.run(slicer.modules.resamplescalarvectordwivolume, None, params, wait_for_completion=True)

    slicer.util.showStatusMessage("Step 5: MS lesion segmentation...")
    cliParams={}
    cliParams["inputT1Volume"] = inputT1Volume_tmp.GetID()
    cliParams["inputT2FLAIRVolume"] = inputFLAIRVolume_tmp.GetID()
    cliParams["inputMNIVolume"] = MNITemplateNode.GetID()
    cliParams["brainLabels"] = MNIBrainTissues.GetID()
    cliParams["outputLesionMap"] = outputVolume.GetID()
    cliParams["absErrorThreshold"] = absError
    cliParams["gamma"] = gamma
    cliParams["wmMatch"] = WMMath
    cliParams["minimumSize"] = minLesionSize
    cliParams["gmMaskValue"] = GMlabel
    cliParams["wmMaskValue"] = WMLabel

    slicer.cli.run(slicer.modules.automaticflairthreshold, None, cliParams, wait_for_completion=True)


    logging.info('Processing completed')

    # Removing unnecessary nodes
    slicer.mrmlScene.RemoveNode(MNIBrainTissues)
    slicer.mrmlScene.RemoveNode(MNITemplateNode)
    slicer.mrmlScene.RemoveNode(registrationMNI2NativeTransform)
    slicer.mrmlScene.RemoveNode(inputFLAIRVolume_tmp)
    slicer.mrmlScene.RemoveNode(inputT1Volume_tmp)

    return True


class AFTSegmenterTest(ScriptedLoadableModuleTest):
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
    self.test_AFTSegmenter1()

  def test_AFTSegmenter1(self):
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
        logging.info(f'Requesting download {name} from {url}...\n')
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info(f'Loading {name}...')
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = AFTSegmenterLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
