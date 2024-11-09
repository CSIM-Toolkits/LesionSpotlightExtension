import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# LSLesionLocalizer
#

class LSLesionLocalizer(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LS Lesion Localizer" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# LSLesionLocalizerWidget
#

class LSLesionLocalizerWidget(ScriptedLoadableModuleWidget):
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
    # input FLAIR volume selector
    #
    self.inputFLAIRSelector = slicer.qMRMLNodeComboBox()
    self.inputFLAIRSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputFLAIRSelector.selectNodeUponCreation = False
    self.inputFLAIRSelector.addEnabled = False
    self.inputFLAIRSelector.removeEnabled = True
    self.inputFLAIRSelector.noneEnabled = True
    self.inputFLAIRSelector.showHidden = False
    self.inputFLAIRSelector.showChildNodeTypes = False
    self.inputFLAIRSelector.setMRMLScene(slicer.mrmlScene)
    self.inputFLAIRSelector.setToolTip("T2-FLAIR Volume")
    parametersInputFormLayout.addRow("T2-FLAIR volume that is useful to space normalization with MNI152 template", self.inputFLAIRSelector)

    #
    # input Lesion Load volume selector
    #
    self.inputLesionLoad = slicer.qMRMLNodeComboBox()
    self.inputLesionLoad.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.inputLesionLoad.selectNodeUponCreation = False
    self.inputLesionLoad.addEnabled = False
    self.inputLesionLoad.removeEnabled = True
    self.inputLesionLoad.noneEnabled = False
    self.inputLesionLoad.showHidden = False
    self.inputLesionLoad.showChildNodeTypes = False
    self.inputLesionLoad.setMRMLScene(slicer.mrmlScene)
    self.inputLesionLoad.setToolTip("Lesion Load")
    parametersInputFormLayout.addRow("A binary volume that inform the lesion load of the patient's FLAIR image", self.inputLesionLoad)

    #
    # output label selector
    #
    self.outputLesionLoad = slicer.qMRMLNodeComboBox()
    self.outputLesionLoad.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.outputLesionLoad.selectNodeUponCreation = True
    self.outputLesionLoad.addEnabled = True
    self.outputLesionLoad.renameEnabled = True
    self.outputLesionLoad.removeEnabled = True
    self.outputLesionLoad.noneEnabled = False
    self.outputLesionLoad.showHidden = False
    self.outputLesionLoad.showChildNodeTypes = False
    self.outputLesionLoad.setMRMLScene(slicer.mrmlScene)
    self.outputLesionLoad.setToolTip(
      "Output lesion load with spatial organization.")
    parametersInputFormLayout.addRow("The same lesion load inserted, but with the labels changed regarding the localization option.", self.outputLesionLoad)

    #
    # Lesion Location Type
    #
    self.setThresholdLFMethodBooleanWidget = ctk.ctkComboBox()
    self.setThresholdLFMethodBooleanWidget.addItem("IJP")
    self.setThresholdLFMethodBooleanWidget.setToolTip(
      "Choose the lesion location type that will organize the lesion load into different brain parts. Options: IJP=Infratentorial, juxtacortical white matter and periventricular regions.")
    parametersSegmentationFormLayout.addRow("Threshold Method ", self.setThresholdLFMethodBooleanWidget)

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
    # MNI152 space?
    #
    self.setMNISpaceWidget = ctk.ctkCheckBox()
    self.setMNISpaceWidget.setChecked(False)
    self.setMNISpaceWidget.setToolTip(
      "Is the input data already registered to MNI152 space?")
    parametersInputFormLayout.addRow("MNI152 space?",
                                     self.setMNISpaceWidget)

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
    # Lesion Threshold
    #
    self.setLesionThresholdWidget = ctk.ctkSliderWidget()
    self.setLesionThresholdWidget.singleStep = 0.01
    self.setLesionThresholdWidget.minimum = 0.05
    self.setLesionThresholdWidget.maximum = 0.99
    self.setLesionThresholdWidget.value = 0.95
    self.setLesionThresholdWidget.setToolTip(
      "Define the lesion threshold used in the probability map, i.e. the percentage of voxels that do not belongs to the MS lesion region."
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
    self.setWMMatchWidget.setToolTip(
      "Set the local neighborhood searching for label refinement step. This metric defines the percentage of white matter"
      " tissue surrounding the hyperintense lesions. Large values defines a conservative segmentation, i.e. in order to define a true MS lesion"
      "it must be close to certain percentage of white matter area.")
    parametersSegmentationFormLayout.addRow("White Matter Matching ", self.setWMMatchWidget)

    #
    # Minimum Lesion Size
    #
    self.setMinimumLesionWidget = qt.QSpinBox()
    self.setMinimumLesionWidget.setMinimum(1)
    self.setMinimumLesionWidget.setMaximum(5000)
    self.setMinimumLesionWidget.setValue(50)
    self.setMinimumLesionWidget.setToolTip(
      "Set the minimum lesion size adopted as a true lesion in the final lesion map. Units given in number of voxels.")
    parametersSegmentationFormLayout.addRow("Minimum Lesion Size ", self.setMinimumLesionWidget)

    #
    # Lesions Map Iterative Updates
    #
    self.setLesionMapUpdatesWidget = ctk.ctkSliderWidget()
    self.setLesionMapUpdatesWidget.singleStep = 1
    self.setLesionMapUpdatesWidget.minimum = 1
    self.setLesionMapUpdatesWidget.maximum = 10
    self.setLesionMapUpdatesWidget.value = 3
    self.setLesionMapUpdatesWidget.setToolTip(
      "Set the number of updates that will be applied over the lesion probability map. Usually 4 iterations result "
      "in a reasonbale lesion segmentation, but if the lesions are subtle you may increase this parameter.")
    parametersSegmentationFormLayout.addRow("Lesion Map Iterative Updates", self.setLesionMapUpdatesWidget)

    #
    # Threshold Method Area
    #
    self.setThresholdLFMethodBooleanWidget = ctk.ctkComboBox()
    self.setThresholdLFMethodBooleanWidget.addItem("MaximumEntropy")
    self.setThresholdLFMethodBooleanWidget.addItem("Otsu")
    self.setThresholdLFMethodBooleanWidget.addItem("Moments")
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

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputFLAIRSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputLesionLoad.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputLesionLoad.currentNode() and self.outputLesionLoad.currentNode()

  def onApplyButton(self):
    logic = LSLesionLocalizerLogic()
    logic.run(self.inputFLAIRSelector.currentNode()
              ,self.outputSelector.currentNode()
              ,self.setIsBETWidget.isChecked()
              ,self.setMNISpaceWidget.isChecked()
              ,self.setPercSamplingQWidget.value
              ,self.setInitiationRegistrationBooleanWidget.currentText
              ,self.setInterpolationMethodBooleanWidget.currentText
              ,self.setWMMatchWidget.value
              ,self.setMinimumLesionWidget.value
              ,self.setLesionMapUpdatesWidget.value
              ,self.setThresholdLFMethodBooleanWidget.currentText
              ,self.setNumberOfBinsWidget.value
              ,self.setLesionThresholdWidget.value)

#
# LSLesionLocalizerLogic
#

class LSLesionLocalizerLogic(ScriptedLoadableModuleLogic):
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

  def run(self, inputFLAIRVolume, outputLabel, isBET, isMNISpace, sampling, initiation, interpolation,
          wmMatch, minimumSize, lUpdate, thrMethod, numBins, lThr):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputFLAIRVolume, outputLabel):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')
    slicer.util.showStatusMessage("Processing started")

    # Creating FLAIR image copy for processing pipeline
    inputFLAIRVolume_tmp = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(inputFLAIRVolume_tmp)
    # volumesLogic = slicer.modules.volumes.logic()
    # inputFLAIRVolume_tmp = volumesLogic.CloneVolume(slicer.mrmlScene, inputFLAIRVolume, inputFLAIRVolume.GetName())
    #################################################################################################################
    #                                              Image Processing                                                 #
    #################################################################################################################

    # #################################################################################################################
    # #                                       T2-FLAIR Noise Attenuation                                              #
    # #################################################################################################################
    # slicer.util.showStatusMessage("Step 2: Decreasing image noise level...")
    #
    # regParams = {}
    # regParams["inputVolume"] = inputFLAIRVolume_tmp.GetID()
    # regParams["outputVolume"] = inputFLAIRVolume_tmp.GetID()
    # regParams["conductance"] = 10.0
    # regParams["useAutoConductance"] = True
    # regParams["optFunction"] = "Canny"
    # regParams["iterations"] = 5
    # regParams["q"] = 1.25
    #
    # slicer.cli.run(slicer.modules.aadimagefilter, None, regParams, wait_for_completion=True)

    # Get the path to files
    path2files = os.path.dirname(slicer.modules.lslesionlocalizer.path)
    if inputFLAIRVolume is not None:
      #################################################################################################################
      #                                    T2-FLAIR Bias Field Correction                                             #
      #################################################################################################################
      slicer.util.showStatusMessage("Bias field correction...")

      regParams = {}
      regParams["inputImageName"] = inputFLAIRVolume.GetID()
      regParams["outputImageName"] = inputFLAIRVolume_tmp.GetID()
      slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, regParams, wait_for_completion=True)

      #################################################################################################################
      #                                        Registration  - MNI to Native space                                    #
      #################################################################################################################
      if platform.system() is "Windows":
        if isBET:
          (read, MNITemplateNode) = slicer.util.loadVolume(
            path2files + '\\Resources\\templates\\MNI152_T1_1mm_brain.nii.gz',
            {}, True)
        else:
          (read, MNITemplateNode) = slicer.util.loadVolume(
            path2files + '\\Resources\\templates\\MNI152_T1_1mm.nii.gz', {},
            True)
      else:
        if isBET:
          (read, MNITemplateNode) = slicer.util.loadVolume(
            path2files + '/Resources/templates/MNI152_T1_1mm_brain.nii.gz', {},
            True)
        else:
          (read, MNITemplateNode) = slicer.util.loadVolume(
            path2files + '/Resources/templates/MNI152_T1_1mm.nii.gz', {}, True)

      #
      # Registering the MNI template to native space.
      #
      slicer.util.showStatusMessage("MNI152 to native space registration...")
      registrationMNI2NativeTransform = slicer.vtkMRMLLinearTransformNode()
      registrationMNI2NativeTransform.SetName("regMNI2Native_linear")
      slicer.mrmlScene.AddNode(registrationMNI2NativeTransform)

      regParams = {}
      regParams["fixedVolume"] = inputFLAIRVolume_tmp.GetID()
      regParams["movingVolume"] = MNITemplateNode.GetID()
      regParams["samplingPercentage"] = sampling
      regParams["splineGridSize"] = '8,8,8'
      regParams["linearTransform"] = registrationMNI2NativeTransform.GetID()
      regParams["initializeTransformMode"] = initiation
      regParams["useRigid"] = True
      regParams["useAffine"] = True
      regParams["interpolationMode"] = interpolation

      slicer.cli.run(slicer.modules.brainsfit, None, regParams, wait_for_completion=True)

      # if -- Colocar uma combo box para selecionar o tipo de padrao espacial - MS, ...

      if platform.system() is "Windows":
        (read, MNI_Infractentorial) = slicer.util.loadLabelVolume(
          path2files + '\\Resources\\standards-labels\\MS\\MNI_1mm_Infratentorial.nii.gz', {}, True)
        (read, MNI_Juxtacortical) = slicer.util.loadLabelVolume(
          path2files + '\\Resources\\standards-labels\\MS\\MNI_1mm_JuxtaCorticalWhiteMatter.nii.gz', {}, True)
        (read, MNI_Ventricules) = slicer.util.loadLabelVolume(
          path2files + '\\Resources\\standards-labels\\MS\\MNI_1mm_Ventricules_Dilated.nii.gz', {}, True)
      else:
        (read, MNI_Infractentorial) = slicer.util.loadLabelVolume(
          path2files + '/Resources/standards-labels/MS/MNI_1mm_Infratentorial.nii.gz', {}, True)
        (read, MNI_Juxtacortical) = slicer.util.loadLabelVolume(
          path2files + '/Resources/standards-labels/MS/MNI_1mm_JuxtaCorticalWhiteMatter.nii.gz', {}, True)
        (read, MNI_Ventricules) = slicer.util.loadLabelVolume(
          path2files + '/Resources/standards-labels/MS/MNI_1mm_Ventricules_Dilated.nii.gz', {}, True)

      infratentorial_native = slicer.vtkMRMLLabelMapVolumeNode()
      slicer.mrmlScene.AddNode(infratentorial_native)
      params = {}
      params["inputVolume"] = MNI_Infractentorial.GetID()
      params["referenceVolume"] = inputFLAIRVolume.GetID()
      params["outputVolume"] = infratentorial_native.GetID()
      params["warpTransform"] = registrationMNI2NativeTransform.GetID()
      params["inverseTransform"] = False
      params["interpolationMode"] = "NearestNeighbor"
      params["pixelType"] = "binary"

      slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)

      juxtacortical_native = slicer.vtkMRMLLabelMapVolumeNode()
      slicer.mrmlScene.AddNode(juxtacortical_native)
      params = {}
      params["inputVolume"] = MNI_Juxtacortical.GetID()
      params["referenceVolume"] = inputFLAIRVolume.GetID()
      params["outputVolume"] = juxtacortical_native.GetID()
      params["warpTransform"] = registrationMNI2NativeTransform.GetID()
      params["inverseTransform"] = False
      params["interpolationMode"] = "NearestNeighbor"
      params["pixelType"] = "binary"

      slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)

      ventricules_native = slicer.vtkMRMLLabelMapVolumeNode()
      slicer.mrmlScene.AddNode(ventricules_native)
      params = {}
      params["inputVolume"] = MNI_Ventricules.GetID()
      params["referenceVolume"] = inputFLAIRVolume.GetID()
      params["outputVolume"] = ventricules_native.GetID()
      params["warpTransform"] = registrationMNI2NativeTransform.GetID()
      params["inverseTransform"] = False
      params["interpolationMode"] = "NearestNeighbor"
      params["pixelType"] = "binary"

      slicer.cli.run(slicer.modules.brainsresample, None, params, wait_for_completion=True)

      #################################################################################################################
      #                                            Lesion localization                                                #
      #################################################################################################################
      slicer.util.showStatusMessage("Step 4: Localizing lesion in brain regions...")
      params = {}
      params["inputLesionLoad"] = inputLesionLoad.GetID()
      params["outputLesionLoad"] = outputVolume.GetID()
      params["inputLocationsFile"] = ventricules_native.GetID()

      slicer.cli.run(slicer.modules.lesionlocalizer, None, params, wait_for_completion=True)

      # lesionLoadUpdate = slicer.vtkMRMLLabelMapVolumeNode()
      # slicer.mrmlScene.AddNode(lesionLoadUpdate)
      # lUpdate = int(lUpdate)
      # for i in range(lUpdate):
      #   # Enhancing lesion contrast...
      #   regParams = {}
      #   regParams["inputVolume"] = inputFLAIRVolume_tmp.GetID()
      #   regParams["outputVolume"] = lesionUpdate.GetID()
      #   regParams["maskVolume"] = brainWM_thin_Label.GetID()
      #   regParams["numberOfBins"] = numBins
      #   regParams["flipObject"] = False
      #   regParams["thrType"] = thrMethod
      #
      #   slicer.cli.run(slicer.modules.logisticcontrastenhancement, None, regParams, wait_for_completion=True)
      #
      #   # Increasing FLAIR lesions contrast...
      #   regParams = {}
      #   regParams["inputVolume"] = inputFLAIRVolume_tmp.GetID()
      #   regParams["contrastMap"] = lesionUpdate.GetID()
      #   regParams["regionMask"] = brainWM_thin_Label.GetID()
      #   regParams["outputVolume"] = inputFLAIRVolume_tmp.GetID()
      #   regParams["weight"] = 0
      #   regParams["lesionThr"] = lThr
      #
      #   slicer.cli.run(slicer.modules.weightedenhancementimagefilter, None, regParams, wait_for_completion=True)

      # #
      # # Lesion Map Refinement
      # #
      # params = {}
      # params["lesionProbMap"] = lesionUpdate.GetID()
      # params["wmMask"] = brainWMLabel.GetID()
      # params["outputLesionMap"] = outputLabel.GetID()
      # params["lesionThr"] = lThr
      # params["wmMatch"] = wmMatch
      # params["minimumSize"] = minimumSize
      #
      # slicer.cli.run(slicer.modules.lesionmaprefinement, None, params, wait_for_completion=True)

      # Removing unnecessary nodes
      slicer.mrmlScene.RemoveNode(registrationMNI2NativeTransform)
      slicer.mrmlScene.RemoveNode(MNITemplateNode)
      slicer.mrmlScene.RemoveNode(MNIWM_thin_Label)
      slicer.mrmlScene.RemoveNode(MNIWMLabel)
      slicer.mrmlScene.RemoveNode(inputFLAIRVolume_tmp)
      slicer.mrmlScene.RemoveNode(brainWMLabel)
      slicer.mrmlScene.RemoveNode(brainWM_thin_Label)
      # slicer.mrmlScene.RemoveNode(lesionLoadUpdate)

      slicer.util.showStatusMessage("Processing completed")
      logging.info('Processing completed')


      return True
    else:
      # TODO Terminar de colocar quando a FLAIR nao eh inserida, ou seja, o lesion load ja esta no espaco MNI...
      slicer.util.showStatusMessage("Processing completed")
      logging.info('Processing completed')

      return True



class LSLesionLocalizerTest(ScriptedLoadableModuleTest):
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
    self.test_LSLesionLocalizer1()

  def test_LSLesionLocalizer1(self):
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
    logic = LSLesionLocalizerLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
