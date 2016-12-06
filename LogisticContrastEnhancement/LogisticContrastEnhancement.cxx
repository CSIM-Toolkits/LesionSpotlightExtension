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

#include "itkLogisticContrastEnhancementImageFilter.h"
#include "itkSigmoidImageFilter.h"
#include "itkMaskImageFilter.h"

#include "itkPluginUtilities.h"

#include "LogisticContrastEnhancementCLP.h"

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

    typedef    T              InputPixelType;
    typedef    T              OutputPixelType;
    typedef    unsigned char  LabelPixelType;

    typedef itk::Image<InputPixelType,  3>    InputImageType;
    typedef itk::Image<OutputPixelType, 3>    OutputImageType;
    typedef itk::Image<LabelPixelType, 3>     LabelImageType;

    typedef itk::ImageFileReader<InputImageType>  ReaderType;
    typedef itk::ImageFileReader<LabelImageType>  LabelReaderType;
    typedef itk::ImageFileWriter<OutputImageType> WriterType;

    typedef itk::LogisticContrastEnhancementImageFilter<InputImageType, InputImageType> LogisticEnhancementType;
    typename LogisticEnhancementType::Pointer enhParameters = LogisticEnhancementType::New();

    typedef itk::MaskImageFilter<InputImageType, LabelImageType>      MaskType;
    typename MaskType::Pointer mask = MaskType::New();

    typedef itk::SigmoidImageFilter<InputImageType, OutputImageType>  SigmoidType;
    typename SigmoidType::Pointer sigmoid = SigmoidType::New();

    typename ReaderType::Pointer reader = ReaderType::New();
    typename LabelReaderType::Pointer labelReader = LabelReaderType::New();

    reader->SetFileName( inputVolume.c_str() );

    labelReader->SetFileName( maskVolume.c_str() );

    mask->SetInput(reader->GetOutput());
    mask->SetMaskImage(labelReader->GetOutput());

    enhParameters->SetInput(mask->GetOutput());
    enhParameters->SetMaximumOutput(1.0);
    enhParameters->SetMinimumOutput(0.0);
    enhParameters->SetNumberOfBins(numberOfBins);
    enhParameters->SetFlipObjectArea(flipObject);

    if (thrType=="MaximumEntropy") {
        enhParameters->SetThresholdMethod(LogisticEnhancementType::MAXENTROPY);
    }else if (thrType=="Otsu") {
        enhParameters->SetThresholdMethod(LogisticEnhancementType::OTSU);
    }else if (thrType=="Renyi"){
        enhParameters->SetThresholdMethod(LogisticEnhancementType::RENYI);
    }else if (thrType=="Moments"){
        enhParameters->SetThresholdMethod(LogisticEnhancementType::MOMENTS);
    }else if (thrType=="Yen"){
        enhParameters->SetThresholdMethod(LogisticEnhancementType::YEN);
    }else if (thrType=="IsoData"){
        enhParameters->SetThresholdMethod(LogisticEnhancementType::ISODATA);
    }else if (thrType=="Intermodes"){
        enhParameters->SetThresholdMethod(LogisticEnhancementType::INTERMODES);
    }

    enhParameters->Update();
    std::cout<<"Beta: "<<enhParameters->GetBeta()<<" - Alpha: "<<enhParameters->GetAlpha()<<std::endl;

    sigmoid->SetInput(reader->GetOutput());
    sigmoid->SetBeta(enhParameters->GetBeta());
    sigmoid->SetAlpha(enhParameters->GetAlpha());
    sigmoid->SetOutputMinimum(0.0);
    sigmoid->SetOutputMaximum(1.0);

    typename WriterType::Pointer writer = WriterType::New();
    writer->SetFileName( outputVolume.c_str() );
    writer->SetInput( sigmoid->GetOutput() );
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
