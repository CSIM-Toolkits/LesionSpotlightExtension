#include "itkImageFileWriter.h"

#include "itkThresholdImageFilter.h"
#include "itkConnectedComponentImageFilter.h"
#include "itkRelabelComponentImageFilter.h"
#include "itkBinaryThresholdImageFilter.h"

#include "itkPluginUtilities.h"

#include "LesionMapRefinementCLP.h"

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

  typedef itk::Image<InputPixelType,  3>      InputImageType;
  typedef itk::Image<MaskLabelPixelType, 3>   MaskImageType;

  typedef itk::ImageFileReader<InputImageType>    ReaderType;
  typedef itk::ImageFileReader<MaskImageType>     LabelReaderType;
  typedef itk::ImageFileWriter<MaskImageType>     WriterType;

  typename ReaderType::Pointer readerProbMap = ReaderType::New();
  typename LabelReaderType::Pointer readerWMMask = LabelReaderType::New();

  readerProbMap->SetFileName( lesionProbMap.c_str() );
  readerWMMask->SetFileName( wmMask.c_str() );
  readerProbMap->Update();
  readerWMMask->Update();

  typedef itk::BinaryThresholdImageFilter<InputImageType,MaskImageType>         BinaryImageType;
  typename BinaryImageType::Pointer flairLesions = BinaryImageType::New();
  flairLesions->SetInput(readerProbMap->GetOutput());
  flairLesions->SetLowerThreshold(lesionThr);
  flairLesions->SetInsideValue(1);
  flairLesions->Update();

  //Apply global lesion constraints
  MaskImageType::Pointer finalLesionMap = MaskImageType::New();
  finalLesionMap->CopyInformation(flairLesions->GetOutput());
  finalLesionMap->SetRegions(flairLesions->GetOutput()->GetBufferedRegion());
  finalLesionMap->Allocate();
  finalLesionMap->FillBuffer(0);
  typedef itk::NeighborhoodIterator<MaskImageType>                        NeighborhoodIterator;
  typedef itk::ImageRegionIterator<MaskImageType>                         MaskRegionIterator;
  NeighborhoodIterator::RadiusType radius = {1,1,1};
  NeighborhoodIterator        lesionMaskIt(radius,flairLesions->GetOutput(),flairLesions->GetOutput()->GetBufferedRegion());
  NeighborhoodIterator        wmMaskIt(radius,readerWMMask->GetOutput(),readerWMMask->GetOutput()->GetBufferedRegion());
  MaskRegionIterator          finalLesionIt(finalLesionMap,flairLesions->GetOutput()->GetBufferedRegion());

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

  //2: Apply a minimum lesion size
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
    itk::GetImageType(lesionProbMap, pixelType, componentType);

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
