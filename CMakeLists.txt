cmake_minimum_required(VERSION 2.8.9)

project(LesionSpotlight)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LesionSpotlight")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_DEPENDS AnomalousFiltersExtension)
set(EXTENSION_CONTRIBUTORS "Antonio Carlos da Silva Senra Filho (University of Sao Paulo), Luiz Otavio Murta Junior (University of Sao Paulo)")
set(EXTENSION_DESCRIPTION "This extension provides an recent image segmentation and enhancement approaches in order to highlight abnormal white matter voxels in magnetic resonance images. At moment, there are available the LS Segmenter module (specific for hyperintense Multiple Sclerosis lesion segmentation on T2-FLAIR images) and LS Contrast Enhancement Module (specific to increase the contrast of abnormal voxels of the same T2-FLAIR images). The LS Segmenter module implements a hyperintense T2-FLAIR lesion segmentation based on a hybrid segmentation algorithm, published by Senra Filho, A.C. (http://dx.doi.org/10.1007/s11517-017-1747-2). In addition, a simple implementation of another recent MS lesion segmentation algorithm is provided, being the method described in Cabezas M. et al. (http://dx.doi.org/10.1016/j.cmpb.2014.04.006)")
set(EXTENSION_ICONURL "https://www.slicer.org/w/images/7/71/LesionSpotlight-logo.png")
set(EXTENSION_SCREENSHOTURLS "https://www.slicer.org/w/images/9/9b/T2FLAIR_patient.png https://www.slicer.org/w/images/b/b4/T2FLAIR_patient_lesionLabel.png https://www.slicer.org/w/images/7/7a/Lesion3DRender.png https://www.slicer.org/w/images/5/52/T2FLAIR_beforeContrast.png https://www.slicer.org/w/images/0/04/T2FLAIR_afterContrast.png https://www.slicer.org/w/images/c/c8/T2FLAIR_patient_AFT.png https://www.slicer.org/w/images/1/1c/T2FLAIR_patient_lesionLabel_AFT.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(LSSegmenter)
add_subdirectory(LogisticContrastEnhancement)
add_subdirectory(LSContrastEnhancer)
add_subdirectory(WeightedEnhancementImageFilter)
add_subdirectory(AutomaticFLAIRThreshold)
add_subdirectory(LesionMapRefinement)
add_subdirectory(AFTSegmenter)
add_subdirectory(LesionLocalizer)
add_subdirectory(LSLesionLocalizer)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
