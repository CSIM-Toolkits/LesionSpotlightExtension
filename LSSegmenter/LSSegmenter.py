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
from SimpleITK._SimpleITK import sitkComposite
from slicer.ScriptedLoadableModule import *
import logging

#
# LSSegmenter
#

class LSSegmenter(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LS Segmenter"
    self.parent.categories = ["Segmentation"]
    self.parent.dependencies = [] #TODO Colocar dependencia AnomalousFilters
    self.parent.contributors = ["Antonio Carlos Senra Filho (University of Sao Paulo), Luiz Otavio Murta Junior (University of Sao Paulo)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module offer a voxel-intensity lesion segmentation method based on logistic contrast enhancement and threshold level.
    At moment, this method was studied on hyperintense T2-FLAIR lesion segmentation in Multiple Sclerosis lesion segmentation.
    More details about the modules functionalities and how to use it, please check the wiki page: https://www.slicer.org/wiki/Documentation/Nightly/Extensions/LesionSpotlight
    """
    self.parent.acknowledgementText = """
    This work was partially funded by CNPq grant 201871/2015-7/SWE and CAPES.
""" # replace with organization, grant and thanks.

#
# LSSegmenterWidget
#

class LSSegmenterWidget(ScriptedLoadableModuleWidget):
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
    # Apply noise attenuation step
    #
    self.setApplyNoiseAttenuationWidget = ctk.ctkCheckBox()
    self.setApplyNoiseAttenuationWidget.setChecked(False)
    self.setApplyNoiseAttenuationWidget.setToolTip(
      "Apply noise attenuation based on the anisotropic anomalous diffusion algorithm on the input data (T1 and T2-FLAIR).")
    parametersInputFormLayout.addRow("Apply noise attenuation step",
                                      self.setApplyNoiseAttenuationWidget)

    #
    # Apply bias field correction step
    #
    self.setApplyBiasFieldnWidget = ctk.ctkCheckBox()
    self.setApplyBiasFieldnWidget.setChecked(False)
    self.setApplyBiasFieldnWidget.setToolTip(
      "Apply bias field correction based on the N4ITK algorithm on the input data (T1 and T2-FLAIR).")
    parametersInputFormLayout.addRow("Apply bias field correction step",
                                      self.setApplyBiasFieldnWidget)

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
    self.setFilteringCondutanceWidget.minimum=1
    self.setFilteringCondutanceWidget.value=5
    self.setFilteringCondutanceWidget.singleStep = 1
    self.setFilteringCondutanceWidget.setToolTip("Condutance parameter.")
    parametersNoiseAttenuationFormLayout.addRow("Condutance ", self.setFilteringCondutanceWidget)

    #
    # Filtering Parameters: Number of iterations
    #
    self.setFilteringNumberOfIterationWidget = ctk.ctkSliderWidget()
    self.setFilteringNumberOfIterationWidget.maximum =30
    self.setFilteringNumberOfIterationWidget.minimum = 1
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

    #
    # Percentage Sampling Area
    #
    self.setPercSamplingQWidget = qt.QDoubleSpinBox()
    self.setPercSamplingQWidget.setDecimals(4)
    self.setPercSamplingQWidget.setMaximum(1)
    self.setPercSamplingQWidget.setMinimum(0.0001)
    self.setPercSamplingQWidget.setSingleStep(0.001)
    self.setPercSamplingQWidget.setValue(0.02)
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
      "Choose the interpolation method used to register the standard space to input image space. Options: Linear, NearestNeighbor, B-Spline")
    parametersRegistrationFormLayout.addRow("Interpolation ", self.setInterpolationMethodBooleanWidget)

    #
    # Segmentation Parameters Area
    #
    parametersSegmentationParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersSegmentationParametersCollapsibleButton.text = "Segmentation Parameters"
    self.layout.addWidget(parametersSegmentationParametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersSegmentationFormLayout = qt.QFormLayout(parametersSegmentationParametersCollapsibleButton)

    #
    # Lesion Threshold
    #
    self.setLesionThresholdWidget = ctk.ctkSliderWidget()
    self.setLesionThresholdWidget.singleStep = 0.01
    self.setLesionThresholdWidget.minimum = 0.05
    self.setLesionThresholdWidget.maximum = 0.99
    self.setLesionThresholdWidget.value = 0.95
    self.setLesionThresholdWidget.setToolTip("Define the lesion threshold used in the probability map, i.e. the percentage of voxels that do not belongs to the MS lesion region."
                                             " Example: l=0.95 means that only 5% of voxels are actual MS lesions.")
    parametersSegmentationFormLayout.addRow("Lesion Threshold", self.setLesionThresholdWidget)

    #
    # White Matter Search Matching
    #
    self.setWMMatchWidget = qt.QDoubleSpinBox()
    self.setWMMatchWidget.setMinimum(0.1)
    self.setWMMatchWidget.setMaximum(1.0)
    self.setWMMatchWidget.setSingleStep(0.1)
    self.setWMMatchWidget.setValue(0.6)
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
    self.setMinimumLesionWidget.setToolTip("Set the minimum lesion size adopted as a true lesion in the final lesion map. Units given in number of voxels.")
    parametersSegmentationFormLayout.addRow("Minimum Lesion Size ", self.setMinimumLesionWidget)

    #
    # Lesions Map Iteartive Updates
    #
    self.setLesionMapUpdatesWidget = ctk.ctkSliderWidget()
    self.setLesionMapUpdatesWidget.singleStep = 1
    self.setLesionMapUpdatesWidget.minimum = 1
    self.setLesionMapUpdatesWidget.maximum = 10
    self.setLesionMapUpdatesWidget.value = 4
    self.setLesionMapUpdatesWidget.setToolTip("Set the number of updates that will be applied over the lesion probability map. Usually 4 iterations result "
                                              "in a reasonbale lesion segmentation, but if the lesions are subtle you may increase this parameter.")
    parametersSegmentationFormLayout.addRow("Lesion Map Iterative Updates", self.setLesionMapUpdatesWidget)

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
    parametersSegmentationFormLayout.addRow("Threshold Method ", self.setThresholdLFMethodBooleanWidget)

    #
    # Number Of Bins
    #
    self.setNumberOfBinsWidget = qt.QSpinBox()
    self.setNumberOfBinsWidget.setMaximum(256)
    self.setNumberOfBinsWidget.setMinimum(10)
    self.setNumberOfBinsWidget.setValue(128)
    self.setNumberOfBinsWidget.setToolTip("Number Of Bins for the histogram calculation")
    parametersSegmentationFormLayout.addRow("Number Of Bins ", self.setNumberOfBinsWidget)

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
    logic = LSSegmenterLogic()
    logic.run(self.inputT1Selector.currentNode()
              ,self.inputFLAIRSelector.currentNode()
              ,self.outputSelector.currentNode()
              ,self.setIsBETWidget.isChecked()
              ,self.setApplyNoiseAttenuationWidget.isChecked()
              ,self.setApplyBiasFieldnWidget.isChecked()
              ,self.setPercSamplingQWidget.value
              ,self.setInitiationRegistrationBooleanWidget.currentText
              ,self.setInterpolationMethodBooleanWidget.currentText
              ,self.setWMMatchWidget.value
              ,self.setMinimumLesionWidget.value
              ,self.setFilteringCondutanceWidget.value
              ,self.setFilteringNumberOfIterationWidget.value
              ,self.setFilteringQWidget.value
              ,self.setLesionMapUpdatesWidget.value
              ,self.setThresholdLFMethodBooleanWidget.currentText
              ,self.setNumberOfBinsWidget.value
              ,self.setLesionThresholdWidget.value
              )


#
# LSSegmenterLogic
#

class LSSegmenterLogic(ScriptedLoadableModuleLogic):
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

  def isValidInputOutputData(self, inputFLAIRVolume, outputLabel):
    """Validates if the output is not the same as input
    """
    if not inputFLAIRVolume:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputLabel:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputFLAIRVolume.GetID()==outputLabel.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def run(self, inputT1Volume, inputFLAIRVolume, outputLabel, isBET,applyNoiseAttenuation,applyBias, sampling, initiation, interpolation,
          wmMatch, minimumSize, conductance, nIter, qValue, lUpdate, thrMethod, numBins, lThr):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputFLAIRVolume, outputLabel):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')
    slicer.util.showStatusMessage("Processing started")

    #################################################################################################################
    #                                        Registration  - FLAIR to T1                                            #
    #################################################################################################################
    slicer.util.showStatusMessage("Step 1/...: T1 to T2-FLAIR registration...")
    registrationT12FLAIRTransform = slicer.vtkMRMLLinearTransformNode()
    registrationT12FLAIRTransform.SetName("regT12FLAIR_linear")
    slicer.mrmlScene.AddNode(registrationT12FLAIRTransform)
    inputT1_FLAIRVolume = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(inputT1_FLAIRVolume)
    regParams = {}
    regParams["fixedVolume"] = inputFLAIRVolume.GetID()
    regParams["movingVolume"] = inputT1Volume.GetID()
    regParams["samplingPercentage"] = sampling
    regParams["outputVolume"] = inputT1_FLAIRVolume.GetID()
    regParams["linearTransform"] = registrationT12FLAIRTransform.GetID()
    regParams["initializeTransformMode"] = initiation
    regParams["useRigid"] = True
    regParams["interpolationMode"] = interpolation

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                        Registration  - MNI to T1                                              #
    #################################################################################################################
    if platform.system() is "Windows":
      home = expanduser("%userprofile%")
    else:
      home = expanduser("~")

    if platform.system() is "Windows":
      if isBET:
        (read, MNITemplateNode) = slicer.util.loadVolume(home + '\\LSSegmenter-Data\\MNI152_T1_1mm_brain.nii.gz', {}, True)
      else:
        (read, MNITemplateNode) = slicer.util.loadVolume(home + '\\LSSegmenter-Data\\MNI152_T1_1mm.nii.gz', {}, True)
    else:
      if isBET:
        (read, MNITemplateNode) = slicer.util.loadVolume(home + '/LSSegmenter-Data/MNI152_T1_1mm_brain.nii.gz', {}, True)
      else:
        (read, MNITemplateNode) = slicer.util.loadVolume(home + '/LSSegmenter-Data/MNI152_T1_1mm.nii.gz', {}, True)

    #
    # Registering the MNI template to T1 image.
    #
    slicer.util.showStatusMessage("Step 1/...: MNI152 to T1 registration...")
    registrationMNI2T1Transform = slicer.vtkMRMLLinearTransformNode()
    registrationMNI2T1Transform.SetName("regMNI2T1_linear")
    slicer.mrmlScene.AddNode(registrationMNI2T1Transform)

    regParams = {}
    regParams["fixedVolume"] = inputT1_FLAIRVolume.GetID()
    regParams["movingVolume"] = MNITemplateNode.GetID()
    regParams["samplingPercentage"] = sampling
    regParams["splineGridSize"] = '8,8,8'
    regParams["linearTransform"] = registrationMNI2T1Transform.GetID()
    regParams["initializeTransformMode"] = initiation
    regParams["useRigid"] = True
    regParams["useAffine"] = True
    regParams["interpolationMode"] = interpolation

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    if platform.system() is "Windows":
      (read, MNIWM_thin_Label) = slicer.util.loadLabelVolume(home + '\\LSSegmenter-Data\\MNI152_T1_1mm_WhiteMatter_thinner.nii.gz', {}, True)
      (read, MNIWMLabel) = slicer.util.loadLabelVolume(home + '\\LSSegmenter-Data\\MNI152_T1_WhiteMatter.nii.gz', {}, True)
    else:
      (read, MNIWM_thin_Label) = slicer.util.loadLabelVolume(home + '/LSSegmenter-Data/MNI152_T1_1mm_WhiteMatter_thinner.nii.gz', {}, True)
      (read, MNIWMLabel) = slicer.util.loadLabelVolume(home + '/LSSegmenter-Data/MNI152_T1_WhiteMatter.nii.gz', {}, True)

    brainWM_thin_Label = slicer.vtkMRMLLabelMapVolumeNode()
    slicer.mrmlScene.AddNode(brainWM_thin_Label)
    params = {}
    params["inputVolume"] = MNIWM_thin_Label.GetID()
    params["referenceVolume"] = inputFLAIRVolume.GetID()
    params["outputVolume"] = brainWM_thin_Label.GetID()
    params["warpTransform"] = registrationMNI2T1Transform.GetID()
    params["inverseTransform"] = False
    params["interpolationMode"] = "NearestNeighbor"
    params["pixelType"] = "binary"

    slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)

    brainWMLabel = slicer.vtkMRMLLabelMapVolumeNode()
    slicer.mrmlScene.AddNode(brainWMLabel)
    params = {}
    params["inputVolume"] = MNIWMLabel.GetID()
    params["referenceVolume"] = inputFLAIRVolume.GetID()
    params["outputVolume"] = brainWMLabel.GetID()
    params["warpTransform"] = registrationMNI2T1Transform.GetID()
    params["inverseTransform"] = False
    params["interpolationMode"] = "Linear"
    params["pixelType"] = "binary"

    slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)

    # Creating FLAIR image copy for processing pipeline
    inputFLAIRVolume_tmp = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(inputFLAIRVolume_tmp)
    # volumesLogic = slicer.modules.volumes.logic()
    # inputFLAIRVolume_tmp = volumesLogic.CloneVolume(slicer.mrmlScene, inputFLAIRVolume, inputFLAIRVolume.GetName())
    #################################################################################################################
    #                                              Image Processing                                                 #
    #################################################################################################################
    if applyBias:
      #################################################################################################################
      #                                    T2-FLAIR Bias Field Correction                                             #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 3/...: Bias field correction...")

      regParams = {}
      regParams["inputImageName"] = inputFLAIRVolume.GetID()
      regParams["maskImageName"] = brainWMLabel.GetID()
      regParams["outputImageName"] = inputFLAIRVolume_tmp.GetID()

      slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)
    if applyNoiseAttenuation:
      #################################################################################################################
      #                                       T2-FLAIR Noise Attenuation                                              #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 5/...: Decreasing image noise level...")

      regParams = {}
      regParams["inputVolume"] = inputFLAIRVolume_tmp.GetID()
      regParams["outputVolume"] = inputFLAIRVolume_tmp.GetID()
      regParams["conductance"] = conductance
      regParams["iterations"] = nIter
      regParams["q"] = qValue

      slicer.cli.run(slicer.modules.aadimagefilter, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                            Lesion segmentation                                                #
    #################################################################################################################
    # TODO Acertar o problema que se nao fizer bias e AAD o inputFLAIRVolume_tmp nao existe...pensar se mantem ou nao a escolha do AAD e bias...
    lesionUpdate = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(lesionUpdate)
    lUpdate=int(lUpdate)
    for i in range(lUpdate):
      # Enhancing lesion contrast...
      regParams = {}
      regParams["inputVolume"] = inputFLAIRVolume_tmp.GetID()
      regParams["outputVolume"] = lesionUpdate.GetID()
      regParams["maskVolume"] = brainWM_thin_Label.GetID()
      regParams["numberOfBins"] = numBins
      regParams["flipObject"] = False
      regParams["thrType"] = thrMethod

      slicer.cli.run(slicer.modules.logisticcontrastenhancement, None, regParams, wait_for_completion=True)

      # Increasing FLAIR lesions contrast...
      regParams = {}
      regParams["inputVolume"] = inputFLAIRVolume_tmp.GetID()
      regParams["contrastMap"] = lesionUpdate.GetID()
      regParams["regionMask"] = brainWM_thin_Label.GetID()
      regParams["outputVolume"] = inputFLAIRVolume_tmp.GetID()
      regParams["weight"] = 0
      regParams["lesionThr"] = lThr

      slicer.cli.run(slicer.modules.weightedenhancementimagefilter, None, regParams, wait_for_completion=True)


    #
    # Lesion Map Refinement
    #
    params= {}
    params["lesionProbMap"]= lesionUpdate.GetID()
    params["wmMask"] = brainWMLabel.GetID()
    params["outputLesionMap"] = outputLabel.GetID()
    params["lesionThr"] = (1-lThr)
    params["wmMatch"] = wmMatch
    params["minimumSize"] = minimumSize

    slicer.cli.run(slicer.modules.lesionmaprefinement, None, params, wait_for_completion=True)

    # Removing unnecessary nodes
    slicer.mrmlScene.RemoveNode(registrationT12FLAIRTransform)
    slicer.mrmlScene.RemoveNode(inputT1_FLAIRVolume)
    slicer.mrmlScene.RemoveNode(registrationMNI2T1Transform)
    slicer.mrmlScene.RemoveNode(MNITemplateNode)
    slicer.mrmlScene.RemoveNode(MNIWM_thin_Label)
    slicer.mrmlScene.RemoveNode(MNIWMLabel)
    slicer.mrmlScene.RemoveNode(inputFLAIRVolume_tmp)
    slicer.mrmlScene.RemoveNode(brainWMLabel)
    slicer.mrmlScene.RemoveNode(brainWM_thin_Label)
    slicer.mrmlScene.RemoveNode(lesionUpdate)

    slicer.util.showStatusMessage("Processing completed")
    logging.info('Processing completed')

    return True



class LSSegmenterTest(ScriptedLoadableModuleTest):
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
    self.test_LSSegmenter1()

  def test_LSSegmenter1(self):
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
    logic = LSSegmenterLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
