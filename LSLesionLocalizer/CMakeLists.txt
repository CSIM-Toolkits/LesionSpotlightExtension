#-----------------------------------------------------------------------------
set(MODULE_NAME LSLesionLocalizer)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

file(GLOB LSLesionLocalizer_Standards_MS RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "Resources/standards-labels/MS/*.nii.gz")
file(GLOB LSLesionLocalizer_Templates RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "Resources/templates/*.nii.gz")
set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  ${LSLesionLocalizer_Standards_MS}
  ${LSLesionLocalizer_Templates}
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
