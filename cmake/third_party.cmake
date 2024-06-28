if(NOT DEFINED CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

option(USE_CONAN "Use Conan to automatically manage dependencies" TRUE)

if(NOT DEFINED CONAN_INSTALL_ARGS)
    set(CONAN_INSTALL_ARGS
        --build=missing
        # Deploy the installed dependencies in the build dir for easier installation, if needed
        --deployer=${CMAKE_SOURCE_DIR}/cmake/merged_deploy.py "--deployer-folder=${CMAKE_BINARY_DIR}"
        # Set cppstd without relying on CMAKE_CXX_STANDARD
        --settings compiler.cppstd=14
    )
    if(WIN32)
        list(APPEND CONAN_INSTALL_ARGS -c tools.deployer:symlinks=False)
    endif()
    set(CONAN_INSTALL_ARGS "${CONAN_INSTALL_ARGS}" CACHE INTERNAL "" FORCE)
endif()

if(USE_CONAN AND NOT DEFINED VCPKG_TOOLCHAIN AND NOT CMAKE_TOOLCHAIN_FILE MATCHES "conan_toolchain.cmake")
    if(CMAKE_VERSION GREATER_EQUAL 3.24)
        list(APPEND CMAKE_PROJECT_TOP_LEVEL_INCLUDES ${CMAKE_CURRENT_LIST_DIR}/conan_provider.cmake)
    else()
        message(WARNING
            "CMake 3.24 or greater is required to install Conan dependencies automatically. "
            "You will have to run 'conan install . ${CONAN_INSTALL_ARGS}' manually in the source directory instead."
        )
    endif()
endif()

set(CONAN_DEPLOYER_DIR "${CMAKE_BINARY_DIR}/merged_deploy")
list(PREPEND CMAKE_PROGRAM_PATH "${CONAN_DEPLOYER_DIR}/build/bin")
