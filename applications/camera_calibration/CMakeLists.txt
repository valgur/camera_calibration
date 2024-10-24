if (CMAKE_CUDA_COMPILER)
  # Make CMake find the Find<Package>.cmake files in the cmake subdirectory.
  set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

  find_package(apriltag REQUIRED)
  find_package(yaml-cpp REQUIRED)

  # Find external library librealsense2 for live RealSense camera support
  find_package(realsense2 QUIET)
  if (realsense2_FOUND)
    add_definitions(-DHAVE_REALSENSE)
  endif()
  
  # Find external library Structure SDK for live Structure Core camera support
  find_package(Structure QUIET)
  
  # Find external library OpenGV
  find_package(opengv REQUIRED)

  find_package(X11 REQUIRED)

  # Find libv4l2 via PkgConfig
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(libv4l2 REQUIRED IMPORTED_TARGET libv4l2)

  # Base library for both the main executable and the unit test executable
  # file(GLOB CAMERA_CALIBRATION_SRC
  #   "src/*.h"
  #   "src/*.cc"
  #   "src/*.cu"
  #   "src/*.cuh"
  # )
  set(CAMERA_CALIBRATION_SRC
    src/camera_calibration/bundle_adjustment/ba_state.cc
    src/camera_calibration/bundle_adjustment/ba_state.h
    src/camera_calibration/bundle_adjustment/cuda_joint_optimization.cc
    src/camera_calibration/bundle_adjustment/cuda_joint_optimization.cu
    src/camera_calibration/bundle_adjustment/cuda_joint_optimization.cuh
    src/camera_calibration/bundle_adjustment/cuda_joint_optimization.h
    src/camera_calibration/bundle_adjustment/joint_optimization.cc
    src/camera_calibration/bundle_adjustment/joint_optimization.h
    src/camera_calibration/bundle_adjustment/joint_optimization_jacobians.h
    
    src/camera_calibration/calibration_initialization/dense_initialization.cc
    src/camera_calibration/calibration_initialization/dense_initialization.h
    
    src/camera_calibration/cuda/cuda_matrix.cuh
    src/camera_calibration/cuda/cuda_util.cuh
    
    src/camera_calibration/feature_detection/cpu_refinement_by_matching.h
    src/camera_calibration/feature_detection/cpu_refinement_by_symmetry.h
    src/camera_calibration/feature_detection/cuda_refinement_by_matching.cc
    src/camera_calibration/feature_detection/cuda_refinement_by_matching.cu
    src/camera_calibration/feature_detection/cuda_refinement_by_matching.cuh
    src/camera_calibration/feature_detection/cuda_refinement_by_matching.h
    src/camera_calibration/feature_detection/cuda_refinement_by_symmetry.cc
    src/camera_calibration/feature_detection/cuda_refinement_by_symmetry.cu
    src/camera_calibration/feature_detection/cuda_refinement_by_symmetry.cuh
    src/camera_calibration/feature_detection/cuda_refinement_by_symmetry.h
    src/camera_calibration/feature_detection/cuda_util.cu
    src/camera_calibration/feature_detection/cuda_util.cuh
    src/camera_calibration/feature_detection/feature_detector.h
    src/camera_calibration/feature_detection/feature_detector_tagged_pattern.cc
    src/camera_calibration/feature_detection/feature_detector_tagged_pattern.h
    
    src/camera_calibration/image_input/image_input.cc
    src/camera_calibration/image_input/image_input.h
    src/camera_calibration/image_input/image_input_realsense.cc
    src/camera_calibration/image_input/image_input_realsense.h
    src/camera_calibration/image_input/image_input_structure.cc
    src/camera_calibration/image_input/image_input_structure.h
    src/camera_calibration/image_input/image_input_v4l2.cc
    src/camera_calibration/image_input/image_input_v4l2.h
    
    src/camera_calibration/io/calibration_io.cc
    src/camera_calibration/io/calibration_io.h
    
    src/camera_calibration/local_parametrizations/direction_parametrization.h
    src/camera_calibration/local_parametrizations/line_parametrization.h
    src/camera_calibration/local_parametrizations/quaternion_parametrization.h
    
    src/camera_calibration/models/camera_model.h
    src/camera_calibration/models/central_generic.cc
    src/camera_calibration/models/central_generic.h
    src/camera_calibration/models/central_opencv.cc
    src/camera_calibration/models/central_opencv.h
    src/camera_calibration/models/central_radial.cc
    src/camera_calibration/models/central_radial.h
    src/camera_calibration/models/central_thin_prism_fisheye.cc
    src/camera_calibration/models/central_thin_prism_fisheye.h
    src/camera_calibration/models/noncentral_generic.cc
    src/camera_calibration/models/noncentral_generic.h
    src/camera_calibration/models/parametric.cc
    src/camera_calibration/models/parametric.h
    
    src/camera_calibration/relative_pose_initialization/algorithms.h
    src/camera_calibration/relative_pose_initialization/central_camera_3d_target.cc
    src/camera_calibration/relative_pose_initialization/central_camera_planar_target.cc
    src/camera_calibration/relative_pose_initialization/noncentral_camera_3d_target.cc
    src/camera_calibration/relative_pose_initialization/noncentral_camera_planar_target.cc
    
    src/camera_calibration/tools/bundle_adjustment.cc
    src/camera_calibration/tools/compare_calibrations.cc
    src/camera_calibration/tools/compare_point_clouds.cc
    src/camera_calibration/tools/convert_dataset.cc
    src/camera_calibration/tools/create_legends.cc
    src/camera_calibration/tools/intersect_datasets.cc
    src/camera_calibration/tools/localization_accuracy_test.cc
    src/camera_calibration/tools/render_synthetic_dataset.cc
    src/camera_calibration/tools/stereo_depth_estimation.cc
    src/camera_calibration/tools/tools.h
    src/camera_calibration/tools/visualize_calibration.cc
    
    src/camera_calibration/ui/calibration_window.cc
    src/camera_calibration/ui/calibration_window.h
    src/camera_calibration/ui/live_image_consumer.cc
    src/camera_calibration/ui/live_image_consumer.h
    src/camera_calibration/ui/main_window.cc
    src/camera_calibration/ui/main_window.h
    src/camera_calibration/ui/pattern_display.cc
    src/camera_calibration/ui/pattern_display.h
    src/camera_calibration/ui/settings_window.cc
    src/camera_calibration/ui/settings_window.h
    
    src/camera_calibration/b_spline.h
    src/camera_calibration/calibration.cc
    src/camera_calibration/calibration.h
    src/camera_calibration/calibration_report.cc
    src/camera_calibration/calibration_report.h
    src/camera_calibration/dataset.cc
    src/camera_calibration/dataset.h
    src/camera_calibration/fitting_report.h
    src/camera_calibration/hash_vec2i.h
    src/camera_calibration/util.cc
    src/camera_calibration/util.h
  )
  add_library(camera_calibration_baselib SHARED
    ${CAMERA_CALIBRATION_SRC}
  )
  set_target_properties(camera_calibration_baselib PROPERTIES POSITION_INDEPENDENT_CODE ON)
  target_compile_options(camera_calibration_baselib
    PUBLIC
      "${LIBVIS_WARNING_OPTIONS}"
      # NOTE: The -march=native was required to be able to use opengv, otherwise
      #       it would just crash when calling an opengv function. I suspect
      #       that it might be because the Eigen objects passed to opengv might
      #       be compiled to have different layouts then.
      $<$<COMPILE_LANGUAGE:CXX>:-march=native>
#       $<$<COMPILE_LANGUAGE:CUDA>:-use_fast_math>
      $<$<COMPILE_LANGUAGE:CUDA>:--expt-relaxed-constexpr>
  )
  target_include_directories(camera_calibration_baselib PRIVATE
    src
    ${realsense_INCLUDE_DIR}
  )
  target_link_libraries(camera_calibration_baselib PUBLIC
    libvis
    libvis_cuda
    libvis_external_io
    CUDA::cublas
    opengv
    apriltag::apriltag
    yaml-cpp::yaml-cpp
    ${realsense2_LIBRARY}
    Qt5::Widgets
    Boost::headers
    Boost::filesystem
    X11::X11
    PkgConfig::libv4l2
  )

  if (TARGET StructurePrebuilt)
    target_link_libraries(camera_calibration_baselib PUBLIC
      StructurePrebuilt
    )
    target_compile_definitions(camera_calibration_baselib PUBLIC HAVE_STRUCTURE)
  endif()
  
  # # For cuda-memcheck
  # target_compile_options(camera_calibration_baselib
  #   PUBLIC
  #     $<$<COMPILE_LANGUAGE:CUDA>:-Xcompiler -rdynamic>
  #     $<$<COMPILE_LANGUAGE:CUDA>:-lineinfo>
  # )
  
  
  # Main executable
  add_executable(camera_calibration
    src/camera_calibration/main.cc
  )
  target_include_directories(camera_calibration PRIVATE
    src
  )
  target_link_libraries(camera_calibration PRIVATE
    camera_calibration_baselib
    Boost::headers
    yaml-cpp::yaml-cpp
    libvis_external_io
  )
  set_target_properties(camera_calibration PROPERTIES
    POSITION_INDEPENDENT_CODE ON
  )
  
  
  # Resource files for unit tests
  ADD_CUSTOM_TARGET(camera_calibration_test_resources ALL
    COMMAND ${CMAKE_COMMAND} -E create_symlink
    ${CMAKE_CURRENT_SOURCE_DIR}/test_data
    ${CMAKE_CURRENT_BINARY_DIR}/test_data
  )
  
  # Unit tests
  add_executable(camera_calibration_test
    src/camera_calibration/test/b_spline_test.cc
    src/camera_calibration/test/camera_unique_representation_test.cc
    src/camera_calibration/test/central_generic_test.cc
    src/camera_calibration/test/central_opencv_test.cc
    src/camera_calibration/test/central_radial_test.cc
    src/camera_calibration/test/central_thin_prism_fisheye_test.cc
    src/camera_calibration/test/dummy_cuda_file.cu
    src/camera_calibration/test/feature_detection_test.cc
    src/camera_calibration/test/io_test.cc
    src/camera_calibration/test/main.cc
    src/camera_calibration/test/noncentral_generic_test.cc
    src/camera_calibration/test/opengv_test.cc
    src/camera_calibration/test/optimization_test.cc
    src/camera_calibration/test/relative_pose_initialization_test.cc
    src/camera_calibration/test/util_test.cc
  )
  add_dependencies(camera_calibration_test camera_calibration_test_resources)
  target_link_libraries(camera_calibration_test
    camera_calibration_baselib
    GTest::gtest
    pthread
    yaml-cpp::yaml-cpp
  )
  target_include_directories(camera_calibration_test PRIVATE
    src
  )
  add_test(camera_calibration_test
    camera_calibration_test
  )
endif()
