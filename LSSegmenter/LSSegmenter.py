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
    self.parent.dependencies = [] #TODO Colocar dependencia BrainTissues
    self.parent.contributors = ["Antonio Carlos Senra Filho (University of Sao Paulo), Luiz Otavio Murta Junior (University of Sao Paulo)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This Module offer a voxel-intensity lesion segmentation method based on logistic contrast enhancement and threshold level.
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
    #ScriptedLoadableModuleWidget.setup(self)
	# TODO Retirar as variaveis de valores GM e WM da mascara...pode deixar automatico
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
    # Absolute Error Threshold
    #
    self.setAbsErrorThresholdWidget = qt.QDoubleSpinBox()
    self.setAbsErrorThresholdWidget.setMaximum(0.99)
    self.setAbsErrorThresholdWidget.setMinimum(0.01)
    self.setAbsErrorThresholdWidget.setSingleStep(0.01)
    self.setAbsErrorThresholdWidget.setValue(0.1)
    self.setAbsErrorThresholdWidget.setToolTip("Define the absolute error threshold for gray matter statistics. "
                                               "This measure evaluated the similarity between the MNI152 template and the T2-FLAIR gray matter "
                                               "fluctuation estimative. A higher error gives a higher variability in the final lesion segmentation")
    parametersSegmentationFormLayout.addRow("Absolute Error Threshold ", self.setAbsErrorThresholdWidget)

    #
    # Gamma
    #
    self.setGammaWidget = qt.QDoubleSpinBox()
    self.setGammaWidget.setMinimum(0.1)
    self.setGammaWidget.setMaximum(5)
    self.setGammaWidget.setSingleStep(0.1)
    self.setGammaWidget.setValue(2)
    self.setGammaWidget.setToolTip("Define the outlier detection based on units of standard deviation in the T2-FLAIR gray matter voxel intensity distribution.")
    parametersSegmentationFormLayout.addRow("Gamma ", self.setGammaWidget)

    #
    # White Matter Search Matching
    #
    self.setWMMatchWidget = qt.QDoubleSpinBox()
    self.setWMMatchWidget.setMinimum(0.1)
    self.setWMMatchWidget.setMaximum(1.0)
    self.setWMMatchWidget.setSingleStep(0.1)
    self.setWMMatchWidget.setValue(0.6)
    self.setWMMatchWidget.setToolTip("Set the local neighborhood searching for label refinement step. This metric defines the percentage of white matter"
                                     " tissue that surrounds the hyperintense lesions. Higher values defines a conservative segmentation.")
    parametersSegmentationFormLayout.addRow("White Matter Matching ", self.setWMMatchWidget)

    #
    # Minimum Lesion Size
    #
    self.setMinimumLesionWidget = qt.QSpinBox()
    self.setMinimumLesionWidget.setMinimum(1)
    self.setMinimumLesionWidget.setValue(10)
    self.setMinimumLesionWidget.setToolTip("Set the minimum lesion size adopted as a true lesion in the final lesion map. Units given in number of voxels.")
    parametersSegmentationFormLayout.addRow("Minimum Lesion Size ", self.setMinimumLesionWidget)

    #
    # Gray Matter Mask Value
    #
    self.setGMMaskValueWidget = qt.QSpinBox()
    self.setGMMaskValueWidget.setMaximum(255)
    self.setGMMaskValueWidget.setMinimum(1)
    self.setGMMaskValueWidget.setValue(2)
    self.setGMMaskValueWidget.setToolTip("Set the mask value that represents the gray matter. Default is defined based on the Basic Brain Tissues module output.")
    parametersSegmentationFormLayout.addRow("Gray Matter Mask Value ", self.setGMMaskValueWidget)

    #
    # White Matter Mask Value
    #
    self.setWMMaskValueWidget = qt.QSpinBox()
    self.setWMMaskValueWidget.setMaximum(255)
    self.setWMMaskValueWidget.setMinimum(1)
    self.setWMMaskValueWidget.setValue(3)
    self.setWMMaskValueWidget.setToolTip("Set the mask value that represents the white matter. Default is defined based on the Basic Brain Tissues module output.")
    parametersSegmentationFormLayout.addRow("White Matter Mask Value ", self.setWMMaskValueWidget)

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
              ,self.setAbsErrorThresholdWidget.value
              ,self.setGammaWidget.value
              ,self.setWMMatchWidget.value
              ,self.setMinimumLesionWidget.value
              ,self.setGMMaskValueWidget.value
              ,self.setWMMaskValueWidget.value
              ,self.setFilteringCondutanceWidget.value
              ,self.setFilteringNumberOfIterationWidget.value
              ,self.setFilteringQWidget.value
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
          absError, gamma, wmMatch, minimumSize, gmMaskValue, wmMaskValue, conductance, nIter, qValue):
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
    slicer.util.showStatusMessage("Step 1/...: T2-FLAIR to T1 registration...")
    registrationFLAIR2T1Transform = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(registrationFLAIR2T1Transform)
    inputFLAIR_T1Volume = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(inputFLAIR_T1Volume)
    regParams = {}
    regParams["fixedVolume"] = inputT1Volume.GetID()
    regParams["movingVolume"] = inputFLAIRVolume.GetID()
    regParams["samplingPercentage"] = sampling
    regParams["outputVolume"] = inputFLAIR_T1Volume.GetID()
    regParams["linearTransform"] = registrationFLAIR2T1Transform.GetID()
    regParams["initializeTransformMode"] = initiation
    regParams["useRigid"] = True
    # regParams["useAffine"] = True
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
    registrationMNI2T1Transform = slicer.vtkMRMLBSplineTransformNode()
    slicer.mrmlScene.AddNode(registrationMNI2T1Transform)

    regParams = {}
    regParams["fixedVolume"] = inputT1Volume.GetID()
    regParams["movingVolume"] = MNITemplateNode.GetID()
    regParams["samplingPercentage"] = sampling
    regParams["splineGridSize"] = '8,8,8'
    regParams["bsplineTransform"] = registrationMNI2T1Transform.GetID()
    regParams["initializeTransformMode"] = initiation
    regParams["useRigid"] = True
    regParams["useAffine"] = True
    regParams["useBSpline"] = True
    regParams["interpolationMode"] = interpolation

    slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

    (read, MNIBrainTemplateNode) = slicer.util.loadVolume(home + '/LSSegmenter-Data/MNI152_T1_1mm_brain.nii.gz', {}, True)
    MNINativeVolume = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(MNINativeVolume)
    params = {}
    params["inputVolume"] = MNIBrainTemplateNode.GetID()
    params["referenceVolume"] = inputT1Volume.GetID()
    params["outputVolume"] = MNINativeVolume.GetID()
    params["warpTransform"] = registrationMNI2T1Transform.GetID()
    params["inverseTransform"] = False
    params["interpolationMode"] = "Linear"
    params["pixelType"] = "float"

    slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)


    #################################################################################################################
    #                                              Image Processing                                                 #
    #################################################################################################################
    if applyBias:
      #################################################################################################################
      #                                           T1 Bias Field Correction                                            #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 3/...: Bias field correction...")

      inputFLAIRBiasVolume = slicer.vtkMRMLScalarVolumeNode()
      slicer.mrmlScene.AddNode(inputFLAIRBiasVolume)
      regParams = {}
      regParams["inputImageName"] = inputT1Volume.GetID()
      # regParams["maskImageName"] = MNINativeWMLabel.GetID()
      regParams["outputImageName"] = inputT1Volume.GetID()

      slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)

      #################################################################################################################
      #                                    T2-FLAIR Bias Field Correction                                             #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 3/...: Bias field correction...")

      inputFLAIRBiasVolume = slicer.vtkMRMLScalarVolumeNode()
      slicer.mrmlScene.AddNode(inputFLAIRBiasVolume)
      regParams = {}
      regParams["inputImageName"] = inputFLAIR_T1Volume.GetID()
      # regParams["maskImageName"] = MNINativeWMLabel.GetID()
      regParams["outputImageName"] = inputFLAIR_T1Volume.GetID()

      slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)
    if applyNoiseAttenuation:
      #################################################################################################################
      #                                             T1 Noise Attenuation                                              #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 5/...: Decreasing image noise level...")

      inputFLAIRBiasSmoothVolume = slicer.vtkMRMLScalarVolumeNode()
      slicer.mrmlScene.AddNode(inputFLAIRBiasSmoothVolume)
      regParams = {}
      regParams["inputVolume"] = inputT1Volume.GetID()
      regParams["outputVolume"] = inputT1Volume.GetID()
      regParams["condutance"] = conductance
      regParams["iterations"] = nIter
      regParams["q"] = qValue

      slicer.cli.run(slicer.modules.aadimagefilter, None, regParams, wait_for_completion=True)

      #################################################################################################################
      #                                       T2-FLAIR Noise Attenuation                                              #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 5/...: Decreasing image noise level...")

      inputFLAIRBiasSmoothVolume = slicer.vtkMRMLScalarVolumeNode()
      slicer.mrmlScene.AddNode(inputFLAIRBiasSmoothVolume)
      regParams = {}
      regParams["inputVolume"] = inputFLAIR_T1Volume.GetID()
      regParams["outputVolume"] = inputFLAIR_T1Volume.GetID()
      regParams["condutance"] = conductance
      regParams["iterations"] = nIter
      regParams["q"] = qValue

      slicer.cli.run(slicer.modules.aadimagefilter, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                            Brain tissues estimative                                           #
    #################################################################################################################
    brainTissuesLabel = slicer.vtkMRMLLabelMapVolumeNode()
    slicer.mrmlScene.AddNode(brainTissuesLabel)
    regParams = {}
    regParams["inputVolume"] = MNINativeVolume.GetID()
    regParams["outputLabel"] = brainTissuesLabel.GetID()
    regParams["imageModality"] = "T1"
    regParams["oneTissue"] = False
    regParams["typeTissue"] = "Gray Matter"

    slicer.cli.run(slicer.modules.basicbraintissues, None, regParams, wait_for_completion=True)

    #################################################################################################################
    #                                            MNI segmentation                                                   #
    #################################################################################################################
    params= {}
    params["inputT1Volume"]= inputT1Volume.GetID()
    params["inputT2FLAIRVolume"] = inputFLAIR_T1Volume.GetID()
    params["inputMNIVolume"] = MNINativeVolume.GetID()
    params["brainLabels"] = brainTissuesLabel.GetID()
    params["outputLesionMap"] = outputLabel.GetID()
    params["absErrorThreshold"] = absError
    params["gamma"] = gamma
    params["wmMatch"] = wmMatch
    params["minimumSize"] = minimumSize
    params["gmMaskValue"] = gmMaskValue
    params["wmMaskValue"] = wmMaskValue

    slicer.cli.run(slicer.modules.automaticflairthreshold, None, params, wait_for_completion=True)

    # Removing unnecessary nodes
    slicer.mrmlScene.RemoveNode(registrationFLAIR2T1Transform)
    slicer.mrmlScene.RemoveNode(inputFLAIR_T1Volume)
    slicer.mrmlScene.RemoveNode(registrationMNI2T1Transform)
    slicer.mrmlScene.RemoveNode(MNINativeVolume)
    slicer.mrmlScene.RemoveNode(MNITemplateNode)
    slicer.mrmlScene.RemoveNode(MNIBrainTemplateNode)
    slicer.mrmlScene.RemoveNode(brainTissuesLabel)

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
