cmake_minimum_required(VERSION 2.8.9)

project(LesionSpotlight)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LesionSpotlight")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_DEPENDS AnomalousFiltersExtension BrainTissuesExtension)
set(EXTENSION_CONTRIBUTORS "Antonio Carlos da Silva Senra Filho (University of Sao Paulo), Luiz Otavio Murta Junior (University of Sao Paulo)")
set(EXTENSION_DESCRIPTION "This extension provides image segmentation and enhancement approaches in order to increase the abnormal white matter voxels in magnetic resonance images. At moment, there are available the LS Segmenter module (specific for hyperintense Multiple Sclerosis lesion segmentation on T2-FLAIR images) and LS Contrast Enhancement Module (specific to increase the contrast of abnormal voxels of the same T2-FLAIR images). The LS Contrast Enhancement module can be used as an image enhancement pre-processing step before a future lesion segmentation algorithm (which could be used any other approach, such as LesionTOADS, OASIS or LST). The LS Segmenter module implements a hyperintense T2-FLAIR lesion segmentation based on the algorithm published in the paper Cabezas, M. et al (2014) "Automatic multiple sclerosis lesion detection in brain MRI by FLAIR thresholding", Computer Methods and Programs in Biomedicine, DOI: 10.1016/j.cmpb.2014.04.006. More details could be found in the wiki page. NOTE: The Logistic Contrast Enhancement, Weighted Enhancement Image Filter and Automatic FLAIR Threshold modules are only supporting CLI methods added here to apply part of the other modules. For this reason these modules are not supposed to be used alone. Please, use the LS Contrast Enhancer or LS Segmenter modules only.")
set(EXTENSION_ICONURL "https://www.slicer.org/w/images/7/71/LesionSpotlight-logo.png")
set(EXTENSION_SCREENSHOTURLS "https://www.slicer.org/w/images/9/9b/T2FLAIR_patient.png https://www.slicer.org/w/images/b/b4/T2FLAIR_patient_lesionLabel.png https://www.slicer.org/w/images/7/7a/Lesion3DRender.png https://www.slicer.org/w/images/5/52/T2FLAIR_beforeContrast.png https://www.slicer.org/w/images/0/04/T2FLAIR_afterContrast.png https://www.slicer.org/w/images/4/44/Lssegmenter_gui.png https://www.slicer.org/w/images/9/9d/Lscontrastenhancer_gui.png")

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
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
