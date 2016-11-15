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

#if (WIN32)
#    add_custom_target(build-time-HyperLesion-directory ALL
#        COMMAND ${CMAKE_COMMAND} -E make_directory %userprofile%\\HyperLesion-Data)
#endif (WIN32)
#if (UNIX)
#    add_custom_target(build-time-HyperLesion-directory ALL
#        COMMAND ${CMAKE_COMMAND} -E make_directory ~/HyperLesion-Data)
#endif (UNIX)

## we don't want to copy if we're building in the source dir
#if (NOT CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_CURRENT_BINARY_DIR)

#    # list of files for which we add a copy rule
#    if (WIN32)
#        set(INPUTS
#   	    HyperLesion-Data\\MNI152_T1_1mm_brain.nii.gz
#            )
#    endif (WIN32)
#    if (UNIX)
#        set(INPUTS
#   	    HyperLesion-Data/MNI152_T1_1mm_brain.nii.gz
#           )
#   endif (UNIX)


#    foreach(item IN LISTS INPUTS)
#        message(STATUS ${item})
#        if (WIN32)
#            add_custom_command(
#                #                TARGET ${MODULE_NAME} PRE_BUILD
#                OUTPUT "%userprofile%\\HyperLesion-Data\\${item}"
#                COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}\\${item}" "%userprofile%\\HyperLesion-Data\\${item}"
#                DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}\\${item}"
#                )
#        endif (WIN32)
#        if (UNIX)
#            add_custom_command(
#               #                TARGET ${MODULE_NAME} PRE_BUILD
#               OUTPUT "~/HyperLesion-Data/${item}"
#               COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/${item}" "~/HyperLesion-Data/${item}"
#               DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/${item}"
#               )
#       endif (UNIX)
#   endforeach()
#endif()

#if (WIN32)
#    add_custom_target(templates ALL DEPENDS
#        "%userprofile%\\HyperLesion-Data\\MNI152_T1_1mm_brain.nii.gz"
#        )
#endif (WIN32)
#if (UNIX)
#    add_custom_target(templates ALL DEPENDS
#        "~/HyperLesion-Data/MNI152_T1_1mm_brain.nii.gz"
#        )
#endif (UNIX)

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
