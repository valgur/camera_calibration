from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMakeToolchain, CMakeDeps, CMake
from conan.tools.env import VirtualBuildEnv, Environment
from conan.tools.gnu import PkgConfigDeps
from conan.tools.system.package_manager import Apt


class PuzzlepaintCameraCalibrationPackage(ConanFile):
    name = "puzzlepaint-camera_calibration"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "system_qt5": [True, False],
        "system_xorg": [True, False],
    }
    default_options = {
        "system_qt5": True,
        "system_xorg": True,
        "*/*:shared": False,
        "qt/*:shared": True,  # must be shared for plugins to work
    }

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("eigen/3.4.0")
        self.requires("sophus/1.22.10")
        self.requires("apriltag/3.4.2")
        self.requires("opengv/cci.20200806")
        self.requires("libv4l/1.28.1")
        self.requires("boost/1.86.0")
        self.requires("loguru/cci.20230406", options={"enable_streams": True, "replace_glog": True})
        self.requires("rapidjson/cci.20230929")
        self.requires("yaml-cpp/0.8.0")
        self.requires("tinyxml2/10.0.0")
        self.requires("libpng/[>=1.6 <2]")
        self.requires("glew/2.2.0")
        self.requires("opengl/system")
        self.requires("vulkan-loader/1.3.290.0")
        if not self.options.system_qt5:
            self.requires("qt/[~5.15]", options={"qtx11extras": True})
        if self.options.system_xorg:
            self.requires("xorg/system", force=True)
        else:
            self.requires("libx11/1.8.10", force=True)

    def system_requirements(self):
        if self.options.system_qt5:
            Apt(self).install(["qtbase5-dev", "libqt5opengl5-dev", "libqt5x11extras5-dev"], check=True)

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("glslang/1.3.290.0")
        self.test_requires("gtest/1.15.0")

    def generate(self):
        VirtualBuildEnv(self).generate()

        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        deps = PkgConfigDeps(self)
        deps.generate()

        if not self.options.get_safe("system_qt5") and self.settings.os in ["Linux", "FreeBSD"]:
            # Qt fails to find system fonts otherwise
            env = Environment()
            env.define_path("FONTCONFIG_PATH", "/etc/fonts")
            env.define_path("FONTCONFIG_FILE", "/etc/fonts/fonts.conf")
            env.define_path("XLOCALDIR", "/usr/share/X11/locale")
            env.vars(self, scope="run").save_script("conanrun_use_system_fonts")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
