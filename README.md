# Lesion Spotlight

This extension implements modern image segmentation and enhancement approaches allowing to highlight abnormal white matter voxels in magnetic resonance images. 

It provides the following modules:

* **LS Segmenter**: specific for hyperintense Multiple Sclerosis lesion segmentation on T2-FLAIR images. It implements a hyperintense T2-FLAIR lesion segmentation based on a hybrid segmentation algorithm, published by Senra Filho, A.C. See http://dx.doi.org/10.1007/s11517-017-1747-2

* **LS Contrast Enhancement**: specific to increase the contrast of abnormal voxels of the same T2-FLAIR images). 

* **AFT Segmenter**: A simple implementation of another recent MS lesion segmentation algorithm based on the method described in Cabezas M. et al. See http://dx.doi.org/10.1016/j.cmpb.2014.04.006

# Documentation

[3D Slicer wiki - Lesion Spotlight](http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LesionSpotlight)

# Licenses

Please, note that this code is under the following license

 * Apache 2.0 - Read file: LICENSE
