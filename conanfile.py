from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMakeToolchain, CMakeDeps, CMake
from conan.tools.env import VirtualBuildEnv, Environment
from conan.tools.system.package_manager import Apt


class PuzzlepaintCameraCalibrationPackage(ConanFile):
    name = "puzzlepaint-camera_calibration"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "system_qt5": [True, False],
    }
    default_options = {
        "system_qt5": True,
        "*/*:shared": False,
        "qt/*:shared": True,  # must be shared for plugins to work
    }

    def config_options(self):
        if self.settings.os != "Linux":
            del self.options.system_qt5

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("apriltag/3.3.0")
        self.requires("boost/1.85.0")
        self.requires("eigen/3.4.0")
        self.requires("glew/2.2.0")
        self.requires("libpng/1.6.43", force=True)
        self.requires("loguru/cci.20230406", options={"enable_streams": True, "replace_glog": True})
        self.requires("opengl/system")
        self.requires("opengv/cci.20200806")
        self.requires("rapidjson/cci.20230929")
        self.requires("sophus/1.22.10")
        self.requires("tinyxml2/10.0.0")
        self.requires("vulkan-loader/1.3.268.0")
        self.requires("xorg/system")
        self.requires("yaml-cpp/0.8.0")
        self.requires("zlib/1.3.1")

        if not self.options.get_safe("system_qt5"):
            self.requires("qt/5.15.14", options={"essential_modules": False, "qtx11extras": True})

    def system_requirements(self):
        apt = Apt(self)
        apt.install(["libv4l-dev"], check=True)
        if self.options.get_safe("system_qt5"):
            apt.install(["qtbase5-dev", "libqt5opengl5-dev", "libqt5x11extras5-dev"], check=True)

    def build_requirements(self):
        self.test_requires("gtest/1.14.0")
        self.tool_requires("glslang/1.3.268.0")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        venv = VirtualBuildEnv(self)
        venv.generate()

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
