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

#include "itkBayesianClassifierInitializationImageFilter.h"
#include "itkBayesianClassifierImageFilter.h"
#include "itkThresholdImageFilter.h"
#include "itkMaskNegatedImageFilter.h"
#include "itkConnectedComponentImageFilter.h"
#include "itkRelabelComponentImageFilter.h"
#include "itkBinaryThresholdImageFilter.h"

#include "itkPluginUtilities.h"

#include "LabelRefinementCLP.h"

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

    typedef    T                       InputPixelType;
    typedef    unsigned int           OutputPixelType;

    typedef itk::Image<InputPixelType,  3> InputImageType;
    typedef itk::Image<OutputPixelType, 3> OutputImageType;

    typedef itk::ImageFileReader<InputImageType>    ReaderType;
    typedef itk::ImageFileReader<OutputImageType>   MaskReaderType;
    typedef itk::ImageFileWriter<OutputImageType>   WriterType;

    typename ReaderType::Pointer reader = ReaderType::New();
    typename MaskReaderType::Pointer maskReader = MaskReaderType::New();

    reader->SetFileName( inputVolume.c_str() );
    maskReader->SetFileName( GMMask.c_str() );
    reader->Update();
    maskReader->Update();

    //Bayesian Segmentation Approach
    typedef itk::BayesianClassifierInitializationImageFilter< InputImageType >         BayesianInitializerType;
    typename BayesianInitializerType::Pointer bayesianInitializer = BayesianInitializerType::New();

    bayesianInitializer->SetInput( reader->GetOutput() );
    bayesianInitializer->SetNumberOfClasses( numClass );// Background, WM, GM, CSF, perilesional area and lesions
    bayesianInitializer->Update();

    //    typedef unsigned char  LabelType;
    typedef float          PriorType;
    typedef float          PosteriorType;

    typedef itk::VectorImage< float, 3 > VectorInputImageType;
    typedef itk::BayesianClassifierImageFilter< VectorInputImageType,OutputPixelType, PosteriorType,PriorType >   ClassifierFilterType;
    typename ClassifierFilterType::Pointer bayesClassifier = ClassifierFilterType::New();

    bayesClassifier->SetInput( bayesianInitializer->GetOutput() );

    unsigned char tissueValue=numClass - 1;
    typedef itk::ThresholdImageFilter<OutputImageType> ThresholdType;
    typename ThresholdType::Pointer thresholder = ThresholdType::New();
    thresholder->SetInput(bayesClassifier->GetOutput());
    thresholder->ThresholdOutside(tissueValue, tissueValue);
    thresholder->SetOutsideValue(0);

    //Reduce false positive lesions in Gray Matter tissue
    typedef itk::MaskNegatedImageFilter< OutputImageType, OutputImageType > MaskNegatedImageFilterType;
    MaskNegatedImageFilterType::Pointer refinedLesions = MaskNegatedImageFilterType::New();
    refinedLesions->SetInput(thresholder->GetOutput());
    refinedLesions->SetMaskImage(maskReader->GetOutput());
    refinedLesions->Update();

    //Label treatment - Removing and organizing the lesion database
    //Spliting labels
    typedef itk::ConnectedComponentImageFilter<OutputImageType, OutputImageType> ConnectedLabelType;
    typename ConnectedLabelType::Pointer connLabel = ConnectedLabelType::New();
    connLabel->SetInput(refinedLesions->GetOutput());
    connLabel->Update();

    cout<<"Number of connected lesions: "<<connLabel->GetObjectCount()<<endl;

    //Cleaning areas lower than 3 mm3 of volume
    typedef itk::RelabelComponentImageFilter<OutputImageType, OutputImageType>      RelabelerType;
    typename RelabelerType::Pointer relabel = RelabelerType::New();
    relabel->SetInput(connLabel->GetOutput());
    relabel->SetSortByObjectSize(true);
    relabel->SetMinimumObjectSize(lesionMinSize);
    relabel->Update();

    int nLesion = relabel->GetNumberOfObjects();
    cout<<"Number of considered lesions: "<<nLesion<<endl;
    cout<<"Size of the lesions: "<<endl;
    double lesionLoad=0.0;
    for (unsigned int size = 0; size < nLesion; ++size) {
        cout<<"Lesion("<<size<<")="<<relabel->GetSizeOfObjectInPixels(size)*reader->GetOutput()->GetSpacing()[0]+
              relabel->GetSizeOfObjectInPixels(size)*reader->GetOutput()->GetSpacing()[1]+
                relabel->GetSizeOfObjectInPixels(size)*reader->GetOutput()->GetSpacing()[2]<<" mm3"<<endl;
        lesionLoad+=relabel->GetSizeOfObjectInPixels(size)*reader->GetOutput()->GetSpacing()[0]+
                relabel->GetSizeOfObjectInPixels(size)*reader->GetOutput()->GetSpacing()[1]+
                relabel->GetSizeOfObjectInPixels(size)*reader->GetOutput()->GetSpacing()[2];
    }
    cout<<"Lesion load: "<<lesionLoad<<" mm3 ("<<lesionLoad/1000<<" mL)"<<endl;

    typedef itk::BinaryThresholdImageFilter<OutputImageType, OutputImageType>     BinaryType;
    typename BinaryType::Pointer binary = BinaryType::New();
    binary->SetInput(relabel->GetOutput());
    binary->SetOutsideValue(0);
    binary->SetInsideValue(1);
    binary->SetLowerThreshold(1);
    binary->SetUpperThreshold(relabel->GetNumberOfObjects());


    typename WriterType::Pointer writer = WriterType::New();
    writer->SetFileName( outputVolume.c_str() );
    writer->SetInput( binary->GetOutput() );
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
