/*
   Copyright 2016 Antonio Carlos da Silva Senra Filho

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
 */
#include "itkImageFileWriter.h"

//Gray matter quality control
#include "itkHistogramMatchingImageFilter.h"
#include "itkSubtractImageFilter.h"
#include "itkAbsImageFilter.h"
#include "itkRescaleIntensityImageFilter.h"

//Gray matter segmentation
#include "itkThresholdImageFilter.h"
#include "itkConnectedComponentImageFilter.h"
#include "itkRelabelComponentImageFilter.h"
#include "itkBinaryThresholdImageFilter.h"

//T2-FLAIR outlier detection
#include "itkMaskImageFilter.h"
#include "itkImageToHistogramFilter.h"
#include "itkImageRegionIterator.h"
#include "itkRescaleIntensityImageFilter.h"
#include "itkNeighborhoodIterator.h"
#include "itkImageRegionIterator.h"

#include "itkPluginUtilities.h"
#include "cmath"

#include "AutomaticFLAIRThresholdCLP.h"

using namespace std;

// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
namespace
{

template <class T>
int DoIt( int argc, char * argv[], T )
{
    PARSE_ARGS;

    typedef    T                InputPixelType;
    typedef    unsigned char     MaskLabelPixelType;

    unsigned char GMlabel = (unsigned char)gmMaskValue, WMlabel = (unsigned char)wmMaskValue;

    typedef itk::Image<InputPixelType,  3>      InputImageType;
    typedef itk::Image<MaskLabelPixelType, 3>   MaskImageType;

    typedef itk::ImageFileReader<InputImageType>    ReaderType;
    typedef itk::ImageFileReader<MaskImageType>     LabelReaderType;
    typedef itk::ImageFileWriter<MaskImageType>     WriterType;

    typename ReaderType::Pointer readerT1 = ReaderType::New();
    typename ReaderType::Pointer readerT2FLAIR = ReaderType::New();
    typename ReaderType::Pointer readerMNI = ReaderType::New();
    typename LabelReaderType::Pointer readerBrainLabels = LabelReaderType::New();

    readerT1->SetFileName( inputT1Volume.c_str() );
    readerT2FLAIR->SetFileName( inputT2FLAIRVolume.c_str() );
    readerMNI->SetFileName( inputMNIVolume.c_str() );
    readerBrainLabels->SetFileName( brainLabels.c_str() );
    readerT1->Update();
    readerT2FLAIR->Update();
    readerMNI->Update();
    readerBrainLabels->Update();

    typedef itk::ThresholdImageFilter <MaskImageType>     ThresholdMaskFilterType;
    typename  ThresholdMaskFilterType::Pointer gmMask  = ThresholdMaskFilterType::New();
    gmMask->SetInput(readerBrainLabels->GetOutput());
    gmMask->ThresholdOutside(GMlabel, GMlabel);
    gmMask->SetOutsideValue(0);

    //
    //Gray matter quality control
    //
    typedef itk::HistogramMatchingImageFilter<InputImageType, InputImageType>       HistogramMatchingFilterType;
    typename HistogramMatchingFilterType::Pointer histogramMatch = HistogramMatchingFilterType::New();
    histogramMatch->SetInput(readerMNI->GetOutput());
    histogramMatch->SetReferenceImage(readerT1->GetOutput());
    histogramMatch->SetNumberOfMatchPoints(10000);

    typedef itk::SubtractImageFilter<InputImageType>                                SubtractFilterType;
    typename SubtractFilterType::Pointer residual = SubtractFilterType::New();
    residual->SetInput1(histogramMatch->GetOutput());
    residual->SetInput2(readerT1->GetOutput());

    typedef itk::AbsImageFilter<InputImageType, InputImageType>                     AbsoluteFilterType;
    typename AbsoluteFilterType::Pointer absError = AbsoluteFilterType::New();
    absError->SetInput(residual->GetOutput());

    typedef itk::MaskImageFilter<InputImageType, MaskImageType>                     MaskInputFilterType;
    typename MaskInputFilterType::Pointer gmError = MaskInputFilterType::New();
    gmError->SetInput(absError->GetOutput());
    gmError->SetMaskImage(gmMask->GetOutput());

    //Absolute Error of Gray Matter alignment
    typedef itk::RescaleIntensityImageFilter<InputImageType>                        RescalerFilterType;
    typename RescalerFilterType::Pointer gmAbsErrorProbability = RescalerFilterType::New();
    gmAbsErrorProbability->SetInput(gmError->GetOutput());
    gmAbsErrorProbability->SetOutputMaximum(1.0);
    gmAbsErrorProbability->SetOutputMinimum(0.0);

    typedef itk::BinaryThresholdImageFilter<InputImageType, MaskImageType>          BinaryThresholdFilterType;
    typename BinaryThresholdFilterType::Pointer gmAbsErrorMask = BinaryThresholdFilterType::New();
    gmAbsErrorMask->SetInput(gmAbsErrorProbability->GetOutput());
    gmAbsErrorMask->SetInsideValue(1);
    gmAbsErrorMask->SetUpperThreshold(absErrorThreshold);
    gmAbsErrorMask->SetLowerThreshold(0.005);

    //
    //Calculate the T2-FLAIR gray matter voxel intensity distribution
    //
    typedef itk::MaskImageFilter<InputImageType,MaskImageType>   MaskingImage;
    typename MaskingImage::Pointer gmFLAIR = MaskingImage::New();
    gmFLAIR->SetInput(readerT2FLAIR->GetOutput());
    gmFLAIR->SetMaskImage(gmAbsErrorMask->GetOutput());
    gmFLAIR->Update();

    //Get T2-FLAIR gray matter distribution parameters
    //Calculating mean mu and standard deviation sigma
    double mu=0.0,sigma=0.0;
    int N=1;
    typedef itk::ImageRegionIterator<InputImageType>    RegionIterator;
    RegionIterator  imgIt(gmFLAIR->GetOutput(),gmFLAIR->GetOutput()->GetBufferedRegion());
    imgIt.GoToBegin();
    while (!imgIt.IsAtEnd()) {
        if (imgIt.Get()!=static_cast<InputPixelType>(0)) {
            mu+=imgIt.Get();
            N++;
            ++imgIt;
        }else{
            ++imgIt;
        }
    }
    mu/=N;
    imgIt.GoToBegin();
    while (!imgIt.IsAtEnd()) {
        if (imgIt.Get()!=static_cast<InputPixelType>(0)) {
            sigma+=(imgIt.Get()-mu)*(imgIt.Get()-mu);
            ++imgIt;
        }else{
            ++imgIt;
        }
    }
    sigma=sqrt(sigma/(N-1));

    cout<<"Gray matter voxel intensity distribution: G(mu="<<mu<<",sigma="<<sigma<<")"<<endl;

    //
    //Lesion label refinement
    //
    double lesionThr = mu + gamma * sigma;
    cout<<"Hyperintense lesions set to values higher than "<<lesionThr<<endl;
    typedef itk::BinaryThresholdImageFilter<InputImageType,MaskImageType>         BinaryImageType;
    typename BinaryImageType::Pointer flairLesions = BinaryImageType::New();
    flairLesions->SetInput(readerT2FLAIR->GetOutput());
    flairLesions->SetLowerThreshold(lesionThr);
    flairLesions->SetInsideValue(1);
    flairLesions->Update();

    //Apply global lesion constraints
    //1: Lesion are mostly close to white matter tissue.
    typename  ThresholdMaskFilterType::Pointer wmMask  = ThresholdMaskFilterType::New();
    wmMask->SetInput(readerBrainLabels->GetOutput());
    wmMask->ThresholdOutside(WMlabel, WMlabel);
    wmMask->SetOutsideValue(0);
    wmMask->Update();

    MaskImageType::Pointer finalLesionMap = MaskImageType::New();
    finalLesionMap->CopyInformation(readerT2FLAIR->GetOutput());
    finalLesionMap->SetRegions(readerT2FLAIR->GetOutput()->GetBufferedRegion());
    finalLesionMap->Allocate();
    finalLesionMap->FillBuffer(0);
    typedef itk::NeighborhoodIterator<MaskImageType>                        NeighborhoodIterator;
    typedef itk::ImageRegionIterator<MaskImageType>                         MaskRegionIterator;
    NeighborhoodIterator::RadiusType radius = {1,1,1};
    NeighborhoodIterator        lesionMaskIt(radius,flairLesions->GetOutput(),flairLesions->GetOutput()->GetBufferedRegion());
    NeighborhoodIterator        wmMaskIt(radius,wmMask->GetOutput(),wmMask->GetOutput()->GetBufferedRegion());
    MaskRegionIterator          finalLesionIt(finalLesionMap,wmMask->GetOutput()->GetBufferedRegion());

    int match=0;
    lesionMaskIt.GoToBegin();
    wmMaskIt.GoToBegin();
    finalLesionIt.GoToBegin();
    while (!lesionMaskIt.IsAtEnd()) {
        if (lesionMaskIt.GetCenterPixel()!=static_cast<MaskLabelPixelType>(0)) {
            match=0;
            for (int idx = 0; idx < 27; ++idx) {
                if (lesionMaskIt.GetPixel(idx)*wmMaskIt.GetPixel(idx)!=static_cast<MaskLabelPixelType>(0)) {
                    match++;
                }
            }
            if ((float)match/(float)27 >= wmMatch) {
                finalLesionIt.Set(1);
            }else{
                finalLesionIt.Set(0);
            }
            ++lesionMaskIt;
            ++wmMaskIt;
            ++finalLesionIt;
        }else{
            ++lesionMaskIt;
            ++wmMaskIt;
            ++finalLesionIt;
        }
    }

    //2: Remove areas between ventricules

    //3: Apply a minimum lesion size
    typedef unsigned int ConnectedVoxelType;
    typedef itk::Image<ConnectedVoxelType, 3>   ConnectedVoxelImageType;
    typedef itk::ConnectedComponentImageFilter<MaskImageType, ConnectedVoxelImageType> ConnectedLabelType;
    typename ConnectedLabelType::Pointer connLesionLabel = ConnectedLabelType::New();
    connLesionLabel->SetInput(finalLesionMap);
    connLesionLabel->Update();

    typedef itk::RelabelComponentImageFilter<ConnectedVoxelImageType, MaskImageType>      RelabelerType;
    typename RelabelerType::Pointer relabelLesionLabel = RelabelerType::New();
    relabelLesionLabel->SetInput(connLesionLabel->GetOutput());
    relabelLesionLabel->SetSortByObjectSize(true);
    relabelLesionLabel->SetMinimumObjectSize(minimumSize);
    relabelLesionLabel->Update();

    typedef itk::BinaryThresholdImageFilter<MaskImageType,MaskImageType>                BinaryLabelMap;
    typename BinaryLabelMap::Pointer hyperintenseLesions = BinaryLabelMap::New();
    hyperintenseLesions->SetInput(relabelLesionLabel->GetOutput());
    hyperintenseLesions->SetLowerThreshold(1);
    hyperintenseLesions->SetInsideValue(1);

    typename WriterType::Pointer writer = WriterType::New();
    writer->SetFileName( outputLesionMap.c_str() );
    writer->SetInput( hyperintenseLesions->GetOutput() );
    writer->SetUseCompression(1);
    writer->Update();
    return EXIT_SUCCESS;

}

} // end of anonymous namespace

int main( int argc, char * argv[] )
{
    PARSE_ARGS;

    itk::ImageIOBase::IOPixelType     pixelType;
    itk::ImageIOBase::IOComponentType componentType;

    try
    {
        itk::GetImageType(inputT1Volume, pixelType, componentType);

        // This filter handles all types on input, but only produces
        // signed types
        switch( componentType )
        {
        case itk::ImageIOBase::UCHAR:
            return DoIt( argc, argv, static_cast<unsigned char>(0) );
            break;
        case itk::ImageIOBase::CHAR:
            return DoIt( argc, argv, static_cast<char>(0) );
            break;
        case itk::ImageIOBase::USHORT:
            return DoIt( argc, argv, static_cast<unsigned short>(0) );
            break;
        case itk::ImageIOBase::SHORT:
            return DoIt( argc, argv, static_cast<short>(0) );
            break;
        case itk::ImageIOBase::UINT:
            return DoIt( argc, argv, static_cast<unsigned int>(0) );
            break;
        case itk::ImageIOBase::INT:
            return DoIt( argc, argv, static_cast<int>(0) );
            break;
        case itk::ImageIOBase::ULONG:
            return DoIt( argc, argv, static_cast<unsigned long>(0) );
            break;
        case itk::ImageIOBase::LONG:
            return DoIt( argc, argv, static_cast<long>(0) );
            break;
        case itk::ImageIOBase::FLOAT:
            return DoIt( argc, argv, static_cast<float>(0) );
            break;
        case itk::ImageIOBase::DOUBLE:
            return DoIt( argc, argv, static_cast<double>(0) );
            break;
        case itk::ImageIOBase::UNKNOWNCOMPONENTTYPE:
        default:
            std::cout << "unknown component type" << std::endl;
            break;
        }
    }

    catch( itk::ExceptionObject & excep )
    {
        std::cerr << argv[0] << ": exception caught !" << std::endl;
        std::cerr << excep << std::endl;
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}
