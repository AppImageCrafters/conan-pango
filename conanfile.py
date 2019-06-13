from conans import ConanFile, AutoToolsBuildEnvironment, tools
from shutil import copyfile
import os


class PangoConan(ConanFile):
    name = "pango"
    version = "1.40.6"
    license = "GPLv2"
    author = "Alexis Lopez Zubieta <contact@azubieta.net>"
    url = "https://github.com/appimage-conan-community/conan-pango/issues"
    description = "Pango is a library for layout and rendering of text"
    topics = ("pango", "text", "rendering")
    settings = "os", "compiler", "build_type", "arch"
    requires = ("glib/2.40.0@appimage-conan-community/stable", "cairo/1.17.2@appimage-conan-community/stable",
                "freetype/2.9.1@appimage-conan-community/stable", "fontconfig/2.13.1@conan/stable",
                "libpng/1.6.36@bincrafters/stable", "harfbuzz/2.4.0@appimage-conan-community/stable")
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {'shared': False, 'fPIC': True}

    generators = "pkg_config"

    def source(self):
        self.run("git clone https://gitlab.gnome.org/GNOME/pango.git -b %s" % self.version)

    def conanArchToSystem(self, conan_arch):
        if conan_arch == "x86":
            return "i386"
        if conan_arch == "x86_64":
            return "amd64"

    def system_requirements(self):
        pkgs_name = None
        system_arch = self.conanArchToSystem(self.settings.arch)
        if tools.os_info.linux_distro == "ubuntu":
            pkgs_name = [
                "make:%s" % system_arch,
                "automake:%s" % system_arch,
                "autoconf:%s" % system_arch,
                "libtool:%s" % system_arch,
                "gettext:%s" % system_arch,
                "libfribidi-dev:%s" % system_arch
            ]

        if pkgs_name:
            installer = tools.SystemPackageTool()
            for pkg_name in pkgs_name:
                installer.install(pkg_name)

    def import_pkg_config_files(self, pkg, pkgconfig_path):
        for root, dirs, files in os.walk(self.deps_cpp_info[pkg].rootpath):
            for file in files:
                if file.endswith("pc"):
                    source_path = os.path.join(root, file)
                    target_path = os.path.join(pkgconfig_path, file)
                    print("Importing pkg_config file: %s" % target_path)
                    copyfile(source_path, target_path)
                    tools.replace_prefix_in_pc_file(target_path, self.deps_cpp_info[pkg].rootpath)

    def build(self):
        for lib in self.deps_cpp_info.deps:
            self.import_pkg_config_files(lib, self.build_folder)

        autotools = AutoToolsBuildEnvironment(self)
        env = autotools.vars
        env["PATH"] = os.getenv("PATH") + ":" + os.path.join(self.deps_cpp_info["glib"].rootpath, "bin")
        env["PKG_CONFIG_PATH"] = env.get("PKG_CONFIG_PATH", "") + ":" + self.build_folder

        configure_args = ['--disable-gtk-doc']
        if self.options.shared:
            configure_args.extend(['--disable-static', '--enable-shared'])
        else:
            configure_args.extend(['--enable-static', '--disable-shared'])

        with tools.environment_append(env):
            os.chdir("%s/pango" % self.build_folder)
            self.run("NOCONFIGURE=1 ./autogen.sh --disable-gtk-doc")
            autotools.pic = self.options.fPIC
            autotools.include_paths.extend(os.path.join(s, "harfbuzz") for s in
                                           self.deps_cpp_info["harfbuzz"].include_paths)

            autotools.configure(args=configure_args, pkg_config_paths=[self.build_folder])
            autotools.make()
            autotools.install()

    def package_info(self):
        self.libdirs = ["lib"]
        self.builddirs = ["lib/pkgconfig"]
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.libs = ["pango-1.0", "pangocairo-1.0"]

        self.cpp_info.includedirs = ["include/pango-1.0"]
