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
import sys
import platform
import unittest
from ctypes.util import find_library

from os.path import expanduser

import vtk, qt, ctk, slicer
from numpy.core.numeric import outer
from slicer.ScriptedLoadableModule import *
import logging

#
# LSContrastEnhancer
#

class LSContrastEnhancer(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LS Contrast Enhancer"
    self.parent.categories = ["Filtering"]
    self.parent.dependencies = []
    self.parent.contributors = ["Antonio Carlos Senra Filho (University of Sao Paulo)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module offer a contrast enhancement approach for hyperintense lesions on T2-FLAIR MRI acquisitions, which is mainly applicable in Multiple Sclerosis lesion detection.
    More details about the modules functionalities and how to use it, please check the wiki page: https://www.slicer.org/wiki/Documentation/Nightly/Extensions/LesionSpotlight
    """
    self.parent.acknowledgementText = """
    This work was partially funded by CNPq grant 201871/2015-7/SWE and CAPES
""" # replace with organization, grant and thanks.

#
# LSContrastEnhancerWidget
#

class LSContrastEnhancerWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
     # ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Input Parameters Area
    #
    parametersInputCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersInputCollapsibleButton.text = "Input/Output Parameters"
    self.layout.addWidget(parametersInputCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersInputFormLayout = qt.QFormLayout(parametersInputCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = False
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = True
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene(slicer.mrmlScene)
    self.inputSelector.setToolTip("Input Volume.")
    parametersInputFormLayout.addRow("Input Volume ", self.inputSelector)

    #
    # output enhanced volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.renameEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = False
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene(slicer.mrmlScene)
    self.outputSelector.setToolTip(
      "Output enhanced volume.")
    parametersInputFormLayout.addRow("Output Volume ", self.outputSelector)

    #
    # Is brain extracted?
    #
    self.setIsBETWidget = ctk.ctkCheckBox()
    self.setIsBETWidget.setChecked(False)
    self.setIsBETWidget.setToolTip(
      "Is the input data already brain extracted? This is information is useful when choosing the brain template that will be adjusted to the native space.")
    parametersInputFormLayout.addRow("Is brain extracted?",
                                            self.setIsBETWidget)


    #
    # Lesion Enhancement Function Parameters Area
    #
    parametersLesionEnhancementCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersLesionEnhancementCollapsibleButton.text = "Lesion Enhancement Function Parameters"
    self.layout.addWidget(parametersLesionEnhancementCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersLesionEnhancementFormLayout = qt.QFormLayout(parametersLesionEnhancementCollapsibleButton)

    #
    # Weighted Lesion Enhancement
    #
    self.setWeightedEnhancementWidget = ctk.ctkSliderWidget()
    self.setWeightedEnhancementWidget.maximum = 0.5
    self.setWeightedEnhancementWidget.minimum = -0.5
    self.setWeightedEnhancementWidget.value = 0
    self.setWeightedEnhancementWidget.singleStep = 0.001
    self.setWeightedEnhancementWidget.setToolTip("The weighting controller that is useful to adjust how much the image signal should be changed. "
                                                 "The contrast map is the baseline spatial weighting distribution to increase the voxel contrast, which should inform the image areas that would be enhanced. "
                                                 "Negative values informs that a smooth increase of signal should be applied (w = -0.5 will not affect the original image). "
                                                 "Positive values indicates a more aggressive signal adjustment, resulting in more signal contrast (w = 0.5 will double the contrast map signal adjustment). "
                                                 "If this weighting value is equal to zero, the contrast map is followed as is. NOTE: If the signal gaussianity is true, the weight value is passed as an absolute value.")
    parametersLesionEnhancementFormLayout.addRow("Weighting Enhancement ", self.setWeightedEnhancementWidget)

    #
    # Maintaing signal gaussianity
    #
    self.setKeepGaussianSignalWidget = ctk.ctkCheckBox()
    self.setKeepGaussianSignalWidget.setChecked(False)
    self.setKeepGaussianSignalWidget.setToolTip(
      "Choose if the enhanced image should maintain the global signal gaussianity, i.e. if the output signal keep the Gaussian distribution after the local contrast enhancement process being made.")
    parametersLesionEnhancementFormLayout.addRow("Maintaing signal gaussianity",
                                     self.setKeepGaussianSignalWidget)

    #
    # Threshold Method Area
    #
    self.setThresholdLFMethodBooleanWidget = ctk.ctkComboBox()
    self.setThresholdLFMethodBooleanWidget.addItem("MaximumEntropy")
    self.setThresholdLFMethodBooleanWidget.addItem("Otsu")
    self.setThresholdLFMethodBooleanWidget.addItem("Moments")
    self.setThresholdLFMethodBooleanWidget.addItem("Intermodes")
    self.setThresholdLFMethodBooleanWidget.addItem("IsoData")
    self.setThresholdLFMethodBooleanWidget.setToolTip(
      "Choose the threhsold method for the lesion enhancement procedure. Options: MaximumEntropy, Otsu, Moments, Intermodes and IsoData")
    parametersLesionEnhancementFormLayout.addRow("Threshold Method ", self.setThresholdLFMethodBooleanWidget)

    #
    # Number Of Bins
    #
    self.setNumberOfBinsWidget = qt.QSpinBox()
    self.setNumberOfBinsWidget.setMaximum(256)
    self.setNumberOfBinsWidget.setMinimum(10)
    self.setNumberOfBinsWidget.setValue(128)
    self.setNumberOfBinsWidget.setToolTip("Number Of Bins for the histogram calculation")
    parametersLesionEnhancementFormLayout.addRow("Number Of Bins ", self.setNumberOfBinsWidget)

    #
    # Flip Object
    #
    self.setFlipObjectWidget = ctk.ctkCheckBox()
    self.setFlipObjectWidget.setChecked(False)
    self.setFlipObjectWidget.setToolTip(
      "Flip object in the image. This informs if the dark part of the histogram that should be enhanced.")
    parametersLesionEnhancementFormLayout.addRow("Flip Object",
                                                 self.setFlipObjectWidget)

    #
    # Noise Attenuation Parameters Area
    #
    parametersNoiseAttenuationCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersNoiseAttenuationCollapsibleButton.text = "Noise Attenuation Parameters"
    parametersNoiseAttenuationCollapsibleButton.collapsed = True
    self.layout.addWidget(parametersNoiseAttenuationCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersNoiseAttenuationFormLayout = qt.QFormLayout(parametersNoiseAttenuationCollapsibleButton)

    #
    # Filtering Parameters: Condutance
    #
    self.setFilteringCondutanceWidget = ctk.ctkSliderWidget()
    self.setFilteringCondutanceWidget.maximum = 50
    self.setFilteringCondutanceWidget.minimum = 1
    self.setFilteringCondutanceWidget.value = 5
    self.setFilteringCondutanceWidget.singleStep = 1
    self.setFilteringCondutanceWidget.setToolTip("Condutance parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Condutance ", self.setFilteringCondutanceWidget)

    #
    # Filtering Parameters: Number of iterations
    #
    self.setFilteringNumberOfIterationWidget = ctk.ctkSliderWidget()
    self.setFilteringNumberOfIterationWidget.maximum = 50
    self.setFilteringNumberOfIterationWidget.minimum = 1
    self.setFilteringNumberOfIterationWidget.value = 5
    self.setFilteringNumberOfIterationWidget.singleStep = 1
    self.setFilteringNumberOfIterationWidget.setToolTip("Number of iterations parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Number Of Iterations ", self.setFilteringNumberOfIterationWidget)

    #
    # Filtering Parameters: Q value
    #
    self.setFilteringQWidget = ctk.ctkSliderWidget()
    self.setFilteringQWidget.singleStep = 0.1
    self.setFilteringQWidget.minimum = 0.01
    self.setFilteringQWidget.maximum = 2.0
    self.setFilteringQWidget.value = 1.2
    self.setFilteringQWidget.setToolTip("Q value parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Q Value ", self.setFilteringQWidget)

    #
    # Registration Parameters Area
    #
    parametersRegistrationCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersRegistrationCollapsibleButton.text = "Registration Parameters"
    parametersRegistrationCollapsibleButton.collapsed = True
    self.layout.addWidget(parametersRegistrationCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersRegistrationFormLayout = qt.QFormLayout(parametersRegistrationCollapsibleButton)

    #
    # Percentage Sampling Area
    #
    self.setPercSamplingQWidget = qt.QDoubleSpinBox()
    self.setPercSamplingQWidget.setDecimals(4)
    self.setPercSamplingQWidget.setMaximum(1)
    self.setPercSamplingQWidget.setMinimum(0.0001)
    self.setPercSamplingQWidget.setSingleStep(0.001)
    self.setPercSamplingQWidget.setValue(0.002)
    self.setPercSamplingQWidget.setToolTip("Percentage of voxel used in registration.")
    parametersRegistrationFormLayout.addRow("Percentage Of Samples ", self.setPercSamplingQWidget)

    #
    # Initiation Method Area
    #
    self.setInitiationRegistrationBooleanWidget = ctk.ctkComboBox()
    self.setInitiationRegistrationBooleanWidget.addItem("useMomentsAlign")
    self.setInitiationRegistrationBooleanWidget.addItem("Off")
    self.setInitiationRegistrationBooleanWidget.addItem("useCenterOfHeadAlign")
    self.setInitiationRegistrationBooleanWidget.addItem("useGeometryAlign")
    self.setInitiationRegistrationBooleanWidget.setToolTip(
      "Initialization method used for the MNI152 registration.")
    parametersRegistrationFormLayout.addRow("Initiation Method ", self.setInitiationRegistrationBooleanWidget)

    #
    # Interpolation Method Area
    #
    self.setInterpolationMethodBooleanWidget = ctk.ctkComboBox()
    self.setInterpolationMethodBooleanWidget.addItem("Linear")
    self.setInterpolationMethodBooleanWidget.addItem("BSpline")
    self.setInterpolationMethodBooleanWidget.addItem("NearestNeighbor")
    self.setInterpolationMethodBooleanWidget.setToolTip(
      "Choose the interpolation method used to register the standard space to the native space. Options: Linear, NearestNeighbor, B-Spline")
    parametersRegistrationFormLayout.addRow("Interpolation ", self.setInterpolationMethodBooleanWidget)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersInputFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = LSContrastEnhancerLogic()
    logic.run( self.inputSelector.currentNode()
              , self.outputSelector.currentNode()
              , self.setIsBETWidget.isChecked()
              , self.setPercSamplingQWidget.value
              , self.setInitiationRegistrationBooleanWidget.currentText
              , self.setInterpolationMethodBooleanWidget.currentText
              , self.setNumberOfBinsWidget.value
              , self.setFlipObjectWidget.isChecked()
              , self.setWeightedEnhancementWidget.value
              , self.setKeepGaussianSignalWidget.isChecked()
              , self.setThresholdLFMethodBooleanWidget.currentText
              , self.setFilteringCondutanceWidget.value
              , self.setFilteringNumberOfIterationWidget.value
              , self.setFilteringQWidget.value
              )

#
# LSContrastEnhancerLogic
#

class LSContrastEnhancerLogic(ScriptedLoadableModuleLogic):
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

  def run(self, inputVolume, outputVolume, isBET, sampling, initiation, interpolation,
              numberOfBins, flipObject, weightingValue, keepGaussianSignal, thresholdMethod, conductance, nIter,
              qValue):

    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')
    slicer.util.showStatusMessage("Processing started")


    #################################################################################################################
    #                                              Image Processing                                                 #
    #################################################################################################################
    #################################################################################################################
    #                                             Bias Field Correction                                             #
    #################################################################################################################
    slicer.util.showStatusMessage("Step 1: Bias field correction...")

    regParams = {}
    regParams["inputImageName"] = inputVolume.GetID()
    regParams["outputImageName"] = outputVolume.GetID()

    slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                              Noise Attenuation                                                #
    #################################################################################################################
    slicer.util.showStatusMessage("Step 2: Decreasing image noise level...")

    regParams = {}
    regParams["inputVolume"] = outputVolume.GetID()
    regParams["outputVolume"] = outputVolume.GetID()
    regParams["conductance"] = conductance
    regParams["iterations"] = nIter
    regParams["q"] = qValue

    slicer.cli.run(slicer.modules.aadimagefilter, None, regParams, wait_for_completion=True)

    # Get the path to LSSegmenter-Data files
    path2files = os.path.dirname(slicer.modules.lssegmenter.path)
    #################################################################################################################
    #                                        Registration  - MNI to Native space                                    #
    #################################################################################################################
    if platform.system() is "Windows":
      if isBET:
        (read, MNITemplateNode) = slicer.util.loadVolume(path2files + '\\Resources\\LSSegmenter-Data\\MNI152_T1_1mm_brain.nii.gz',
                                                         {}, True)
      else:
        (read, MNITemplateNode) = slicer.util.loadVolume(path2files + '\\Resources\\LSSegmenter-Data\\MNI152_T1_1mm.nii.gz', {},
                                                         True)
    else:
      if isBET:
        (read, MNITemplateNode) = slicer.util.loadVolume(path2files + '/Resources/LSSegmenter-Data/MNI152_T1_1mm_brain.nii.gz', {},
                                                         True)
      else:
        (read, MNITemplateNode) = slicer.util.loadVolume(path2files + '/Resources/LSSegmenter-Data/MNI152_T1_1mm.nii.gz', {}, True)

    #
    # Registering the MNI template to native space.
    #
    slicer.util.showStatusMessage("Step 3: MNI152 to native space registration...")
    registrationMNI2NativeTransform = slicer.vtkMRMLLinearTransformNode()
    registrationMNI2NativeTransform.SetName("regMNI2Native_linear")
    slicer.mrmlScene.AddNode(registrationMNI2NativeTransform)

    regParams = {}
    regParams["fixedVolume"] = outputVolume.GetID()
    regParams["movingVolume"] = MNITemplateNode.GetID()
    regParams["samplingPercentage"] = sampling
    regParams["splineGridSize"] = '8,8,8'
    regParams["linearTransform"] = registrationMNI2NativeTransform.GetID()
    regParams["initializeTransformMode"] = initiation
    regParams["useRigid"] = True
    regParams["useAffine"] = True
    regParams["interpolationMode"] = interpolation

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    if platform.system() is "Windows":
      (read, MNIWM_thin_Label) = slicer.util.loadLabelVolume(path2files + '\\Resources\\LSSegmenter-Data\\MNI152_T1_1mm_WhiteMatter_thinner.nii.gz', {}, True)
    else:
      (read, MNIWM_thin_Label) = slicer.util.loadLabelVolume(path2files + '/Resources/LSSegmenter-Data/MNI152_T1_1mm_WhiteMatter_thinner.nii.gz', {}, True)

    brainWM_thin_Label = slicer.vtkMRMLLabelMapVolumeNode()
    slicer.mrmlScene.AddNode(brainWM_thin_Label)
    params = {}
    params["inputVolume"] = MNIWM_thin_Label.GetID()
    params["referenceVolume"] = outputVolume.GetID()
    params["outputVolume"] = brainWM_thin_Label.GetID()
    params["warpTransform"] = registrationMNI2NativeTransform.GetID()
    params["inverseTransform"] = False
    params["interpolationMode"] = "NearestNeighbor"
    params["pixelType"] = "binary"

    slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)

    #################################################################################################################
    #                                            Lesion segmentation                                                #
    #################################################################################################################
    slicer.util.showStatusMessage("Step 4: Enhancing hyperintenses lesions...")
    lesionUpdate = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(lesionUpdate)

    # Enhancing lesion contrast...
    regParams = {}
    regParams["inputVolume"] = outputVolume.GetID()
    regParams["outputVolume"] = lesionUpdate.GetID()
    regParams["maskVolume"] = brainWM_thin_Label.GetID()
    regParams["numberOfBins"] = numberOfBins
    regParams["flipObject"] = flipObject
    regParams["thrType"] = thresholdMethod

    slicer.cli.run(slicer.modules.logisticcontrastenhancement, None, regParams, wait_for_completion=True)

    # Increasing FLAIR lesions contrast...
    regParams = {}
    regParams["inputVolume"] = inputVolume.GetID()
    regParams["contrastMap"] = lesionUpdate.GetID()
    regParams["outputVolume"] = outputVolume.GetID()
    regParams["weight"] = weightingValue
    regParams["maintainGaussianity"] = keepGaussianSignal

    slicer.cli.run(slicer.modules.weightedenhancementimagefilter, None, regParams, wait_for_completion=True)


    # Removing unnecessary nodes
    slicer.mrmlScene.RemoveNode(registrationMNI2NativeTransform)
    slicer.mrmlScene.RemoveNode(MNITemplateNode)
    slicer.mrmlScene.RemoveNode(MNIWM_thin_Label)
    slicer.mrmlScene.RemoveNode(brainWM_thin_Label)
    slicer.mrmlScene.RemoveNode(lesionUpdate)

    slicer.util.showStatusMessage("Processing completed")
    logging.info('Processing completed')

    return True


class LSContrastEnhancerTest(ScriptedLoadableModuleTest):
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
    self.test_LSContrastEnhancer1()

  def test_LSContrastEnhancer1(self):
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
    logic = LSContrastEnhancerLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
