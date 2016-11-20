#include "itkImageFileWriter.h"

#include "itkMaskImageFilter.h"
#include "itkThresholdImageFilter.h"
#include "itkSubtractImageFilter.h"
#include "itkMultiplyImageFilter.h"
#include "itkAddImageFilter.h"
#include "itkStatisticsImageFilter.h"
#include "itkRescaleIntensityImageFilter.h"

#include "itkImageRegionIterator.h"

#include "itkPluginUtilities.h"

#include "WeightedEnhancementImageFilterCLP.h"

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

    typedef    T                              InputPixelType;
    typedef    T                              OutputPixelType;
    typedef    unsigned char                  LabelPixelType;

    typedef itk::Image<InputPixelType,  3>    InputImageType;
    typedef itk::Image<OutputPixelType, 3>    OutputImageType;
    typedef itk::Image<LabelPixelType, 3>     LabelImageType;

    typedef itk::ImageFileReader<InputImageType>      ReaderType;
    typedef itk::ImageFileReader<LabelImageType>      LabelReaderType;
    typedef itk::ImageFileWriter<OutputImageType>     WriterType;

    typename ReaderType::Pointer inputReader = ReaderType::New();
    typename ReaderType::Pointer contrastMapReader = ReaderType::New();
    typename LabelReaderType::Pointer regionMaskReader = LabelReaderType::New();

    inputReader->SetFileName( inputVolume.c_str() );
    contrastMapReader->SetFileName( contrastMap.c_str() );
    regionMaskReader->SetFileName( regionMask.c_str() );

    //Split background and lesion regions
    //Lesion image:
    typedef itk::ThresholdImageFilter<InputImageType>  ThresholderType;
    typename ThresholderType::Pointer lesionImage = ThresholderType::New();
    lesionImage->SetInput(contrastMapReader->GetOutput());
    lesionImage->ThresholdBelow(static_cast<InputPixelType>(lesionThr));
    //Background image:
    typedef itk::SubtractImageFilter<InputImageType>  SubtractType;
    typename SubtractType::Pointer backgroundImage = SubtractType::New();
    backgroundImage->SetInput1(contrastMapReader->GetOutput());
    backgroundImage->SetInput2(lesionImage->GetOutput());

    //Apply region mask over the contrast map
    typedef itk::MaskImageFilter<InputImageType, LabelImageType>  MaskFilterType;
    typename MaskFilterType::Pointer maskedImage = MaskFilterType::New();
    maskedImage->SetInput(backgroundImage->GetOutput());
    maskedImage->SetMaskImage(regionMaskReader->GetOutput());
    maskedImage->Update();

    //Calculating baseline contrast
    InputPixelType baselineValue = 0;
    typedef itk::ImageRegionIterator< InputImageType >              IteratorType;
    IteratorType contrastIt(maskedImage->GetOutput(), maskedImage->GetOutput()->GetBufferedRegion());

    contrastIt.GoToBegin();
    int N=0;
    while (!contrastIt.IsAtEnd()) {
        //        std::cout<<contrastIt.Get()<<std::endl;
        if (contrastIt.Get()!=static_cast<InputPixelType>(0)) {
            baselineValue=baselineValue+contrastIt.Get();
            ++contrastIt;
            N++;
        }
        ++contrastIt;
    }
    baselineValue/=static_cast<InputPixelType>(N);
    std::cout<<"Region mean contrast: "<<baselineValue<<std::endl;

    typename SubtractType::Pointer baselineContrast = SubtractType::New();
    baselineContrast->SetInput1(contrastMapReader->GetOutput());
    baselineContrast->SetConstant2(baselineValue);

    typename ThresholderType::Pointer finalContrasMap = ThresholderType::New();
    finalContrasMap->SetInput(baselineContrast->GetOutput());
    finalContrasMap->ThresholdBelow(0.0);

    typedef itk::RescaleIntensityImageFilter<InputImageType,InputImageType> RescalerType;
    typename RescalerType::Pointer rescaledContrastMap = RescalerType::New();
    rescaledContrastMap->SetInput(finalContrasMap->GetOutput());
    rescaledContrastMap->SetOutputMaximum(1.0);
    rescaledContrastMap->SetOutputMinimum(0.0);

    //Applying contrast weighting on the input image
    InputPixelType contrastPercentage = static_cast<InputPixelType>(weight)/100+static_cast<InputPixelType>(1);
    typedef itk::MultiplyImageFilter< InputImageType >      MultiplyType;
    typename MultiplyType::Pointer rescaledBoost = MultiplyType::New();
    rescaledBoost->SetInput1(rescaledContrastMap->GetOutput());
    rescaledBoost->SetConstant2(contrastPercentage);

    typedef itk::AddImageFilter<InputImageType>             AddType;
    typename AddType::Pointer boostWeight = AddType::New();
    boostWeight->SetInput1(rescaledBoost->GetOutput());
    boostWeight->SetConstant2(static_cast<InputPixelType>(1));
    boostWeight->Update();

    typename MultiplyType::Pointer inputEnhanced = MultiplyType::New();
    inputEnhanced->SetInput1(inputReader->GetOutput());
    inputEnhanced->SetInput2(boostWeight->GetOutput());
    inputEnhanced->Update();

    //Info: Mean lesion contrast enhancement
    IteratorType enhancedIt(inputEnhanced->GetOutput(), inputEnhanced->GetOutput()->GetBufferedRegion());
    IteratorType origIt(inputReader->GetOutput(),inputReader->GetOutput()->GetBufferedRegion());

    enhancedIt.GoToBegin();
    origIt.GoToBegin();
    InputPixelType meanBoost=0;
    int M=0;
    while (!enhancedIt.IsAtEnd()) {
        if (enhancedIt.Get()!=static_cast<InputPixelType>(0)) {
            meanBoost+=(enhancedIt.Get()/origIt.Get())-static_cast<InputPixelType>(1);
            M++;
            ++origIt;
            ++enhancedIt;
        }
        ++origIt;
        ++enhancedIt;

    }
    meanBoost/=static_cast<InputPixelType>(M);
    std::cout<<"Mean image contrast enhancement estimated in "<<(meanBoost)*static_cast<InputPixelType>(100)<<"% in comparison with the original image."<<std::endl;

    typename WriterType::Pointer writer = WriterType::New();
    writer->SetFileName( outputVolume.c_str() );
    writer->SetInput( inputEnhanced->GetOutput() );
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
        itk::GetImageType(inputVolume, pixelType, componentType);

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
