#include "itkImageFileWriter.h"

#include "itkBinaryThresholdImageFilter.h"
#include "itkConnectedComponentImageFilter.h"
#include "itkRelabelComponentImageFilter.h"

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

    typedef itk::ImageFileReader<InputImageType>  ReaderType;
    typedef itk::ImageFileWriter<OutputImageType> WriterType;

    typedef itk::BinaryThresholdImageFilter<InputImageType, OutputImageType>     ThresholderType;
    typename ThresholderType::Pointer thresholder = ThresholderType::New();

    typename ReaderType::Pointer reader = ReaderType::New();

    reader->SetFileName( inputVolume.c_str() );

    thresholder->SetInput(reader->GetOutput());
    thresholder->SetOutsideValue(0);
    thresholder->SetInsideValue(1);
    thresholder->SetLowerThreshold(threshold);
    thresholder->SetUpperThreshold(1.0);

    //Label treatment - Removing and organizing the lesion database
    //Spliting labels
    typedef itk::ConnectedComponentImageFilter<OutputImageType, OutputImageType> ConnectedLabelType;
    typename ConnectedLabelType::Pointer connLabel = ConnectedLabelType::New();
    connLabel->SetInput(thresholder->GetOutput());
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
