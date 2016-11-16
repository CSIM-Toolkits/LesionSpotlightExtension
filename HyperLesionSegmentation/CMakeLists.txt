#-----------------------------------------------------------------------------
set(MODULE_NAME HyperLesionSegmentation)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

if (WIN32)
file(MAKE_DIRECTORY %userprofile%\\HyperLesion-Data)
endif (WIN32)
if (UNIX)
file(MAKE_DIRECTORY ~/HyperLesion-Data)
endif (UNIX)

if (WIN32)
file(MAKE_DIRECTORY %userprofile%\\HyperLesion-Data)
endif (WIN32)
if (UNIX)
file(INSTALL ${CMAKE_CURRENT_SOURCE_DIR}/HyperLesion-Data/MNI152_T1_1mm_brain.nii.gz DESTINATION $ENV{HOME}/HyperLesion-Data/)
endif (UNIX)

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
