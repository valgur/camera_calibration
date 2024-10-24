option(USE_CONAN "Use Conan to automatically manage dependencies" TRUE)
if(NOT USE_CONAN OR DEFINED VCPKG_TOOLCHAIN OR CMAKE_TOOLCHAIN_FILE MATCHES "conan_toolchain.cmake")
    return()
endif()

if(NOT DEFINED CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

set(CONAN_HOME "${CMAKE_BINARY_DIR}/conan_home")
set(CUSTOM_REMOTE_PATH "${CMAKE_BINARY_DIR}/cci-valgur")
set(CCI_FORK_VERSION "613ddaa9e4258e8eabdda903fccc018479781cb8")  # 2024-10-23
include(FetchContent)
FetchContent_Declare(
    cci_valgur
    URL "https://github.com/valgur/conan-center-index/archive/${CCI_FORK_VERSION}.zip"
    SOURCE_DIR "${CUSTOM_REMOTE_PATH}"
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(cci_valgur)
file(WRITE "${CONAN_HOME}/remotes.json" "
{
 \"remotes\": [
  {
   \"name\": \"cci-valgur\",
   \"url\": \"${CUSTOM_REMOTE_PATH}\",
   \"verify_ssl\": true,
   \"remote_type\": \"local-recipes-index\"
  }
 ]
}
")
# Set some reasonable defaults
file(WRITE "${CONAN_HOME}/global.conf" "
core.download:download_cache=${CONAN_HOME}/dl_cache
core.sources:download_cache=${CONAN_HOME}/dl_cache
")

if(CMAKE_VERSION GREATER_EQUAL 3.24)
    list(APPEND CMAKE_PROJECT_TOP_LEVEL_INCLUDES ${CMAKE_CURRENT_LIST_DIR}/conan_provider.cmake)
else()
    message(WARNING
        "CMake 3.24 or greater is required to install Conan dependencies automatically. "
        "You will have to run 'conan install . ${CONAN_INSTALL_ARGS}' manually in the source directory instead."
    )
endif()
