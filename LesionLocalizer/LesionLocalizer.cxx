#include "itkImageFileWriter.h"

#include "itkImageRegionIterator.h"
#include "itkConnectedComponentImageFilter.h"

#include "itkPluginUtilities.h"

#include "LesionLocalizerCLP.h"

// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
namespace
{

template <typename TPixel>
int DoIt( int argc, char * argv[], TPixel )
{
    PARSE_ARGS;

    typedef unsigned int InputPixelType;
    typedef unsigned int OutputPixelType;

    const unsigned int Dimension = 3;

    typedef itk::Image<InputPixelType,  Dimension> InputImageType;
    typedef itk::Image<OutputPixelType, Dimension> OutputImageType;

    typedef itk::ImageFileReader<InputImageType>  ReaderType;

    typename ReaderType::Pointer inputReader = ReaderType::New();

    inputReader->SetFileName( inputLesionLoad.c_str() ); //read the input mask that is already in MNI space
    try
    {
        inputReader->Update();
    }
    catch ( itk::ExceptionObject &err)
    {
        std::cerr << "ExceptionObject caught !" << std::endl;
        std::cerr << err << std::endl;
        return -1;
    }

    //Output label
    typename InputImageType::Pointer output = InputImageType::New();
    output->CopyInformation( inputReader->GetOutput() );
    output->SetBufferedRegion( inputReader->GetOutput()->GetBufferedRegion() );
    output->Allocate();
    output->FillBuffer(0);

    //load the brain regions in MNI space (MS: infratentorial, juxtacortical and periventricular)
//    std::vector<InputImageType::Pointer> brainRegions;
    std::vector<InputImageType::Pointer> inputPriors;

    if (!inputLocationsFile.empty()) {
            for (unsigned int prior = 0; prior < inputLocationsFile.size(); ++prior) {
                std::cout<<"Using brain regions ("<<(prior+1)<<") at location: "<<inputLocationsFile[prior].c_str()<<std::endl;

                typename ReaderType::Pointer priorsReader = ReaderType::New();
                priorsReader->SetFileName( inputLocationsFile[prior].c_str() );
                priorsReader->Update();
                inputPriors.push_back(priorsReader->GetOutput());
            }
    }else{
        std::cout<<"STOP: No brain region was passed."<<std::endl;
        return EXIT_SUCCESS; // If no brain region is passed, the algorithm stops.
    }

    //separate the lesion on each MNI brain regions (regarding label value)
    typedef itk::ConnectedComponentImageFilter<InputImageType, InputImageType> ConnectedLabelType;
    typename ConnectedLabelType::Pointer connLabel = ConnectedLabelType::New();
    connLabel->SetInput(inputReader->GetOutput());
    connLabel->Update();

    typedef itk::ImageRegionIterator< InputImageType > IteratorType;
    for (unsigned int region = 0; region < inputPriors.size(); ++region) {
        std::cout<<"Spliting label "<<(region+1)<<": "<<inputLocationsFile[region].c_str()<<std::endl;
        std::cout<<"    ->Total number of lesions: "<<connLabel->GetObjectCount()<<"\n       -> Calculating lesion: ";
        for (unsigned int l = 1; l <= connLabel->GetObjectCount(); ++l) {
            std::cout<<(l)<<", ";
            std::cout<<std::flush;
            IteratorType regionIt(inputPriors[region], inputPriors[region]->GetBufferedRegion());
            IteratorType chosenLesionIt(connLabel->GetOutput(), connLabel->GetOutput()->GetBufferedRegion());
            IteratorType lesionIt(connLabel->GetOutput(), connLabel->GetOutput()->GetBufferedRegion());
            IteratorType outLabelIt(output, output->GetBufferedRegion());
            regionIt.GoToBegin();
            lesionIt.GoToBegin();
            while (!regionIt.IsAtEnd()) {
                if (lesionIt.Get()==l && regionIt.Get()>0) {
                    //If the lesion is inside the brain region, then the entire lesion is copied to the output label.
                    outLabelIt.GoToBegin();
                    chosenLesionIt.GoToBegin();
                    while (!chosenLesionIt.IsAtEnd()) {
                        if (chosenLesionIt.Get()==l && outLabelIt.Get()==0) {
                            outLabelIt.Set((chosenLesionIt.Get()/l)+region);
                        }
                        ++outLabelIt;
                        ++chosenLesionIt;
                    }
                    break;
                }
                ++lesionIt;
                ++regionIt;
            }
        }
        std::cout<<std::endl;
    }

    typedef itk::ImageFileWriter<OutputImageType> WriterType;
    typename WriterType::Pointer writer = WriterType::New();
    writer->SetFileName( outputLesionLoad.c_str() );
    writer->SetInput( output );
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
        itk::GetImageType(inputLesionLoad, pixelType, componentType);

        // This filter handles all types on input, but only produces
        // signed types
        switch( componentType )
        {
        case itk::ImageIOBase::UCHAR:
            return DoIt( argc, argv, static_cast<unsigned char>(0) );
            break;
        case itk::ImageIOBase::CHAR:
            return DoIt( argc, argv, static_cast<signed char>(0) );
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
            std::cerr << "Unknown input image pixel component type: ";
            std::cerr << itk::ImageIOBase::GetComponentTypeAsString( componentType );
            std::cerr << std::endl;
            return EXIT_FAILURE;
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
