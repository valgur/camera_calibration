cmake_minimum_required(VERSION 3.18)
include(cmake/third_party.cmake)
project(libvis LANGUAGES C CXX)

# Enable C++14 globally
set(CMAKE_CXX_STANDARD 14)

# Support IDEs: https://cliutils.gitlab.io/modern-cmake/chapters/features/ides.html
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
set_property(GLOBAL PROPERTY PREDEFINED_TARGETS_FOLDER "cmake-default-targets")

if(MSVC)
  # Fixes DLL generation with MSVC.
  # See http://gernotklingler.com/blog/creating-using-shared-libraries-different-compilers-different-operating-systems/
  # and also https://stackoverflow.com/questions/37128555/getting-cmake-to-build-shared-library-for-msvc
  set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS YES CACHE BOOL "Export all symbols in Visual Studio")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /MP")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP")
endif()

include(CheckLanguage)


################################################################################
# Dependencies.

# CUDA (external)
# NOTE: The user of this CMake file should set the CUDA arch when invoking
#       CMake, for example with: -DCMAKE_CUDA_FLAGS="-arch=sm_61"
#       Common settings are either the 'native' arch for which the binary will
#       be known to run on exclusively, or a broader set of PTX architectures
#       in case the binary is intended for distribution.
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
  set(CMAKE_CUDA_ARCHITECTURES native)
endif()
check_language(CUDA)
if (CMAKE_CUDA_COMPILER)
  enable_language(CUDA)
  
  # Enable C++14 globally for CUDA code
  if(NOT DEFINED CMAKE_CUDA_STANDARD)
    set(CMAKE_CUDA_STANDARD 14)
    set(CMAKE_CUDA_STANDARD_REQUIRED ON)
  endif()
  
  # Find CUDA libraries (in particular: cublas)
  find_package(CUDAToolkit REQUIRED)
  
  # It is very important that CUDA's nvcc uses exactly the same gcc version and
  # flags as is used for other C++ code. Otherwise, it can happen that classes
  # have different layouts as seen by code compiled by nvcc's gcc and by the
  # other used gcc, which leads to memory-corruption type bugs. See e.g.:
  # https://devtalk.nvidia.com/default/topic/1024953/linking-problem-due-to-different-size-of-std-string/
  # ccbin must be set to the full path, otherwise there is the possibility that
  # nvcc searches in the wrong location first according to the linked forum
  # posts above.
  if (NOT MSVC)
    set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -ccbin=${CMAKE_CXX_COMPILER}")
  else()
    set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS}")
  endif()
else()
  message(FATAL_ERROR "CMake does not find the CUDA SDK, which is required to build this application (even in case CUDA itself will not or cannot be used).")
endif()

# Cross-platform threading. See:
# https://cmake.org/cmake/help/latest/module/FindThreads.html
find_package(Threads REQUIRED)
find_package(OpenGL REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Boost REQUIRED COMPONENTS serialization filesystem system)
find_package(loguru REQUIRED)
find_package(GLEW REQUIRED)
find_package(PNG REQUIRED)
find_package(Sophus REQUIRED)
find_package(RapidJSON REQUIRED)

find_package(GTest REQUIRED)
enable_testing()

find_package(VulkanLoader REQUIRED)
find_program(GLSLANG_VALIDATOR glslangValidator REQUIRED)
set(VULKAN_FOUND TRUE)

# Qt5 (external, required)
# TODO: Qt should be an optional dependency but is required currently.
# Find includes in corresponding build directories.
set(CMAKE_INCLUDE_CURRENT_DIR ON)

# Instruct CMake to run moc automatically when needed.
set(CMAKE_AUTOMOC ON)

# Instruct CMake to run rcc (resource compiler) automatically when needed.
set(CMAKE_AUTORCC ON)

find_package(Qt5 5.8 REQUIRED COMPONENTS Core OpenGL Widgets X11Extras)

# Settings.
if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_GNUXX)
  set(LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-Wall>")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-Wextra>")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-O2>")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-msse2>")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-msse3>")
  
  # TODO: It seems gcc cannot disable this locally, therefore added it here as a
  #       workaround.
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-Wno-unknown-pragmas>")
  
  # NOTE: Disabled this since it triggered in a lot of places, including external headers, creating a lot of warning spam.
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-Wno-sign-compare>")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:-Wno-missing-field-initializers>")
elseif(MSVC)
  #  set(LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/O2")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/MP >")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/W4>")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/wd4068 >")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/wd4127 >") # https://docs.microsoft.com/en-us/cpp/error-messages/compiler-warnings/compiler-warning-level-4-c4127?view=vs-2019
  
  # NOTE: Disabled this since it triggered in a lot of places, including external headers, creating a lot of warning spam.
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/wd4244 >")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/wd4267 >")
  list(APPEND LIBVIS_WARNING_OPTIONS "$<$<COMPILE_LANGUAGE:CXX>:/wd4389 >")
endif()


################################################################################
# Helper application bin2c required for building libvis.

add_executable(bin2c
  ./libvis/src/bin2c/main.cc
)
set_property(TARGET bin2c PROPERTY FOLDER "libvis")

target_compile_options(bin2c PRIVATE
  "${LIBVIS_WARNING_OPTIONS}"
)
target_link_libraries(bin2c
  Boost::headers
  Boost::filesystem
)

################################################################################
# Function for generating headers with SPIR-V bytecode from GLSL code.

# Sets up compile and header-conversion commands for Vulkan shaders. The
# resulting header file paths are appended to the variable whose name is passed
# in for _GENERATED_HEADERS. These headers must be specified in a target to
# trigger the shader build steps.
# NOTE: _GENERATED_HEADERS must differ from the variable name being passed in,
#       otherwise the dereferencing returns the wrong variable.
function(add_vulkan_shader TARGETNAME INPUT_FILEPATH _GENERATED_HEADERS)
  get_filename_component(INPUT_FILENAME ${INPUT_FILEPATH} NAME)
  
  # Vertex shader.
  add_custom_command (
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.vert.h
    COMMAND ${GLSLANG_VALIDATOR} -V -S vert -o ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.vert ${CMAKE_CURRENT_SOURCE_DIR}/${INPUT_FILEPATH}.vert
    COMMAND bin2c -n vis -H ${CMAKE_CURRENT_SOURCE_DIR}/libvis/src/libvis/shaders/license_header.h ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.vert
    DEPENDS bin2c ${CMAKE_CURRENT_SOURCE_DIR}/${INPUT_FILEPATH}.vert
    )
  
  # Fragment shader.
  add_custom_command (
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.frag.h
    COMMAND ${GLSLANG_VALIDATOR} -V -S frag -o ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.frag ${CMAKE_CURRENT_SOURCE_DIR}/${INPUT_FILEPATH}.frag
    COMMAND bin2c -n vis -H ${CMAKE_CURRENT_SOURCE_DIR}/libvis/src/libvis/shaders/license_header.h ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.frag
    DEPENDS bin2c ${CMAKE_CURRENT_SOURCE_DIR}/${INPUT_FILEPATH}.frag
    )
  
  # Return generated headers in the variable named ${_GENERATED_HEADERS} in the
  # parent scope.
  set(${_GENERATED_HEADERS}
    ${${_GENERATED_HEADERS}}
    ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.vert.h
    ${CMAKE_CURRENT_BINARY_DIR}/${INPUT_FILENAME}.frag.h
    PARENT_SCOPE
  )
endfunction()


################################################################################
# libvis.

if(VULKAN_FOUND)
  add_vulkan_shader(libvis
    libvis/src/libvis/shaders/shader
    GENERATED_HEADERS
  )
endif()

set(LIBVIS_FILES
  libvis/src/libvis/camera.h
  libvis/src/libvis/camera_frustum_opengl.h
  libvis/src/libvis/command_line_parser.cc
  libvis/src/libvis/command_line_parser.h
  libvis/src/libvis/dlt.h
  libvis/src/libvis/eigen.h
  libvis/src/libvis/geometry.h
  libvis/src/libvis/glew.cc
  libvis/src/libvis/glew.h
  libvis/src/libvis/image.cc
  libvis/src/libvis/image.h
  libvis/src/libvis/image_cache.h
  libvis/src/libvis/image_display.cc
  libvis/src/libvis/image_display.h
  libvis/src/libvis/image_display_qt_widget.cc
  libvis/src/libvis/image_display_qt_widget.h
  libvis/src/libvis/image_display_qt_window.cc
  libvis/src/libvis/image_display_qt_window.h
  libvis/src/libvis/image_frame.h
  libvis/src/libvis/image_io.cc
  libvis/src/libvis/image_io.h
  libvis/src/libvis/image_io_libpng.cc
  libvis/src/libvis/image_io_libpng.h
  libvis/src/libvis/image_io_netpbm.cc
  libvis/src/libvis/image_io_netpbm.h
  libvis/src/libvis/image_io_qt.cc
  libvis/src/libvis/image_io_qt.h
  libvis/src/libvis/libvis.cc
  libvis/src/libvis/libvis.h
  libvis/src/libvis/lm_optimizer.h
  libvis/src/libvis/lm_optimizer_impl.h
  libvis/src/libvis/lm_optimizer_update_accumulator.h
  libvis/src/libvis/loss_functions.h
  libvis/src/libvis/mesh.h
  libvis/src/libvis/mesh_opengl.h
  libvis/src/libvis/opengl.cc
  libvis/src/libvis/opengl.h
  libvis/src/libvis/opengl_context.cc
  libvis/src/libvis/opengl_context.h
  libvis/src/libvis/opengl_context_glx.cc
  libvis/src/libvis/opengl_context_glx.h
  libvis/src/libvis/opengl_context_qt.cc
  libvis/src/libvis/opengl_context_qt.h
  libvis/src/libvis/patch_match_stereo.cc
  libvis/src/libvis/patch_match_stereo.h
  libvis/src/libvis/point_cloud.h
  libvis/src/libvis/point_cloud_opengl.h
  libvis/src/libvis/qt_thread.cc
  libvis/src/libvis/qt_thread.h
  libvis/src/libvis/render_display.cc
  libvis/src/libvis/render_display.h
  libvis/src/libvis/render_window.cc
  libvis/src/libvis/render_window.h
  libvis/src/libvis/render_window_qt.cc
  libvis/src/libvis/render_window_qt.h
  libvis/src/libvis/render_window_qt_opengl.cc
  libvis/src/libvis/render_window_qt_opengl.h
  libvis/src/libvis/renderer.cc
  libvis/src/libvis/renderer.h
  libvis/src/libvis/rgbd_video.h
  libvis/src/libvis/rgbd_video_io_tum_dataset.h
  libvis/src/libvis/shader_program_opengl.cc
  libvis/src/libvis/shader_program_opengl.h
  libvis/src/libvis/sophus.h
  libvis/src/libvis/statistics.h
  libvis/src/libvis/timing.cc
  libvis/src/libvis/timing.h
  libvis/src/libvis/util.h
  
  ${GENERATED_HEADERS}
  libvis/resources/resources.qrc
)
if(VULKAN_FOUND)
  set(LIBVIS_FILES
    libvis/src/libvis/render_window_qt_vulkan.cc
    libvis/src/libvis/render_window_qt_vulkan.h
    libvis/src/libvis/vulkan.cc
    libvis/src/libvis/vulkan.h
    ${LIBVIS_FILES}
  )
endif()

add_library(libvis SHARED
  ${LIBVIS_FILES}
)
set_property(TARGET libvis PROPERTY FOLDER "libvis")

target_compile_options(libvis PRIVATE
  "${LIBVIS_WARNING_OPTIONS}"
  $<$<COMPILE_LANGUAGE:CXX>:-march=native>
)

if (VULKAN_FOUND)
  target_compile_options(libvis PUBLIC -DLIBVIS_HAVE_VULKAN)
endif()
target_compile_options(libvis PUBLIC -DLIBVIS_HAVE_QT)
target_compile_options(libvis PUBLIC -DLIBVIS_HAVE_CUDA)

target_include_directories(libvis
  PUBLIC
    ./libvis/src
  PRIVATE
    ${CMAKE_CURRENT_BINARY_DIR}
)
target_link_libraries(libvis
  PUBLIC
    CUDA::cusolver
    Eigen3::Eigen
    loguru::loguru
    Qt5::Core
    Qt5::OpenGL
    Qt5::Widgets
    rapidjson
    Sophus::Sophus
  PRIVATE
    Boost::headers
    GLEW::GLEW
    OpenGL::GL
    PNG::PNG
    Qt5::X11Extras
    Threads::Threads
)
if(VULKAN_FOUND)
  target_link_libraries(libvis PRIVATE
      Vulkan::Loader
  )
endif()


# libvis optional library: libvis_external_io.
# Contains I/O functions for less common external formats such as MeshLab
# project files.
add_library(libvis_external_io SHARED
  libvis/src/libvis/external_io/colmap_model.cc
  libvis/src/libvis/external_io/colmap_model.h
  libvis/src/libvis/external_io/meshlab_project.cc
  libvis/src/libvis/external_io/meshlab_project.h
)
find_package(tinyxml2 REQUIRED CONFIG)
target_link_libraries(libvis_external_io PUBLIC tinyxml2::tinyxml2)
set_property(TARGET libvis_external_io PROPERTY FOLDER "libvis")
target_compile_options(libvis_external_io PRIVATE
  "${LIBVIS_WARNING_OPTIONS}"
  $<$<COMPILE_LANGUAGE:CXX>:-march=native>
)
target_link_libraries(libvis_external_io PUBLIC
  Boost::headers
  libvis
)

# libvis optional library: libvis_cuda.
# Contains CUDA functionality, which is only useful with NVIDIA graphics cards.
if (CMAKE_CUDA_COMPILER)
  add_library(libvis_cuda SHARED
    libvis/src/libvis/cuda/cuda_auto_tuner.h
    libvis/src/libvis/cuda/cuda_buffer.cu
    libvis/src/libvis/cuda/cuda_buffer.cuh
    libvis/src/libvis/cuda/cuda_buffer.h
    libvis/src/libvis/cuda/cuda_buffer_inl.h
    libvis/src/libvis/cuda/cuda_matrix.cuh
    libvis/src/libvis/cuda/cuda_unprojection_lookup.cuh
    libvis/src/libvis/cuda/cuda_unprojection_lookup.h
    libvis/src/libvis/cuda/cuda_util.h
    libvis/src/libvis/cuda/patch_match_stereo.cc
    libvis/src/libvis/cuda/patch_match_stereo.cu
    libvis/src/libvis/cuda/patch_match_stereo.cuh
    libvis/src/libvis/cuda/patch_match_stereo.h
    libvis/src/libvis/cuda/patch_match_stereo_cost.cuh
    libvis/src/libvis/cuda/patch_match_stereo_kernel_consistency.cu
    libvis/src/libvis/cuda/patch_match_stereo_kernel_init.cu
    libvis/src/libvis/cuda/patch_match_stereo_kernel_mutation.cu
    libvis/src/libvis/cuda/patch_match_stereo_kernel_optimize.cu
    libvis/src/libvis/cuda/patch_match_stereo_kernel_outliers.cu
    libvis/src/libvis/cuda/patch_match_stereo_kernel_propagation.cu
    libvis/src/libvis/cuda/patch_match_stereo_kernel_refinement.cu
    libvis/src/libvis/cuda/patch_match_stereo_samples.cuh
    libvis/src/libvis/cuda/patch_match_stereo_samples.cu
    libvis/src/libvis/cuda/patch_match_stereo_util.cuh
    libvis/src/libvis/cuda/pixel_corner_projector.cuh
    libvis/src/libvis/cuda/pixel_corner_projector.h
  )
  set_property(TARGET libvis_cuda PROPERTY FOLDER "libvis")
  target_compile_options(libvis_cuda PRIVATE
    "${LIBVIS_WARNING_OPTIONS}"
    $<$<COMPILE_LANGUAGE:CXX>:-march=native>
  )
  target_link_libraries(libvis_cuda PUBLIC
    libvis
  )
  target_compile_options(libvis_cuda PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:-use_fast_math>
    $<$<COMPILE_LANGUAGE:CUDA>:--expt-relaxed-constexpr>
  )
  # Turn on separable compilation. This is required to have extern __constant__ variables in headers.
  set_target_properties(libvis_cuda
    PROPERTIES CUDA_SEPARABLE_COMPILATION ON
  )
  
  add_executable(libvis_cuda_test
    libvis/src/libvis/cuda/test/cholesky_solver.cc
    libvis/src/libvis/cuda/test/cholesky_solver.cu
    libvis/src/libvis/cuda/test/cholesky_solver.cuh
    libvis/src/libvis/cuda/test/main.cc
  )
  target_link_libraries(libvis_cuda_test PRIVATE
    GTest::gtest_main
    Threads::Threads
    libvis_cuda
    CUDA::cublas  # TODO: currently required because of lm_optimizer.h. That should not be necessary.
    GLEW::GLEW
  )
  add_test(libvis_cuda_test
    libvis_cuda_test
  )
endif()


################################################################################
# Applications.

add_subdirectory(applications)


################################################################################
# Tests.

add_executable(libvis_test
  libvis/src/libvis/test/camera.cc
  libvis/src/libvis/test/dlt.cc
  libvis/src/libvis/test/geometry.cc
  libvis/src/libvis/test/image.cc
  libvis/src/libvis/test/image_cache.cc
  libvis/src/libvis/test/lm_optimizer.cc
  libvis/src/libvis/test/loss_functions.cc
  libvis/src/libvis/test/main.cc
  libvis/src/libvis/test/point_cloud.cc
  libvis/src/libvis/test/util.cc
)
set_property(TARGET libvis_test PROPERTY FOLDER "libvis")
target_link_libraries(libvis_test PRIVATE
  GTest::gtest
  Threads::Threads
  libvis
  CUDA::cublas  # TODO: currently required because of lm_optimizer.h. That should not be necessary.
  GLEW::GLEW
)
add_test(libvis_test
  libvis_test
)


################################################################################
# Include a global summary of found/not found pkgs. See:
# https://cmake.org/cmake/help/latest/module/FeatureSummary.html

include(FeatureSummary)
feature_summary(WHAT ALL)
