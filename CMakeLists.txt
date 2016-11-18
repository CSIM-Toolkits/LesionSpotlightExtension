cmake_minimum_required(VERSION 2.8.9)

project(LesionSpotlight)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LesionSpotlight")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Antonio Carlos Senra Filho (University of Sao Paulo), Luiz Otavio Murta Junior (University of Sao Paulo)")
set(EXTENSION_DESCRIPTION "This extension aims to provide segmentation and image enhancement approaches in order to increase the define abnormal white matter voxels in magnetic resonance images. At moment, there are available the LS Segmenter Module (specific for hyperintense Multiple Sclerosis lesion segmentation on T2-FLAIR images) and LS Contrast Enhancement Module (specific to increase the contrast of abnormal voxels of the same T2-FLAIR images). The LS Contrast Enhancement Module could be an image enhancement pre-processing step before a future lesion segmentation algorithm (which could be used any other approach, such as LesionTOADS, OASIS or LST). The LS Segmenter Module implements the algorithm published in the paper "". More details could be found in the wiki page. 

NOTE: The LogisticContrastEnhancement and LabelRefinement Modules are supporting CLI methods added here to apply part of the other Modules. For this reason these Modules are not supposed to be used alone.")
set(EXTENSION_ICONURL "https://www.slicer.org/w/images/7/71/LesionSpotlight-logo.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/LesionSpotlight/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(LSSegmenter)
add_subdirectory(LogisticContrastEnhancement)
add_subdirectory(LabelRefinement)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
