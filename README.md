# Lesion Spotlight

![Logo](https://github.com/CSIM-Toolkits/Slicer-LesionSpotlightExtension/blob/main/LesionSpotlight.png)

This extension implements modern image segmentation and enhancement approaches, allowing for the highlight of abnormal white matter voxels in magnetic resonance images. 

It provides the following modules:

* **LS Segmenter**: specific for hyperintense Multiple Sclerosis lesion segmentation on T2-FLAIR images. It implements a hyperintense T2-FLAIR lesion segmentation based on a hybrid segmentation algorithm, published by Senra Filho, A.C.
> da Silva Senra Filho, A.C. A hybrid approach based on logistic classification and iterative contrast enhancement algorithm for hyperintense multiple sclerosis lesion segmentation. Med Biol Eng Comput 56, 1063–1076 (2018). [DOI](https://doi.org/10.1007/s11517-017-1747-2)

* **LS Contrast Enhancement**: specific to increase the contrast of abnormal voxels of the same T2-FLAIR images). 

* **AFT Segmenter**: A simple implementation of another recent MS lesion segmentation algorithm based on the method described in Cabezas M. et al.
> Mariano Cabezas, Arnau Oliver, Eloy Roura, Jordi Freixenet, Joan C. Vilanova, Lluís Ramió-Torrentà, Àlex Rovira, Xavier Lladó, Automatic multiple sclerosis lesion detection in brain MRI by FLAIR thresholding, Computer Methods and Programs in Biomedicine, Volume 115, Issue 3, 2014, Pages 147-161, ISSN 0169-2607, [DOI](https://doi.org/10.1016/j.cmpb.2014.04.006). 

![Example](https://github.com/CSIM-Toolkits/Slicer-LesionSpotlightExtension/blob/main/docs/assets/Lesion3DRender.png)

![Example](https://github.com/CSIM-Toolkits/Slicer-LesionSpotlightExtension/blob/main/docs/assets/T2FLAIR_patient_lesionLabel_AFT.png)

# Documentation

[3D Slicer wiki - Lesion Spotlight](http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/LesionSpotlight)

# Contact

* Antonio Senra Filho: acsenrafilho@gmail.com

# Licenses

Please, note that this code is under the following license

 * Apache 2.0 - Read file: LICENSE
