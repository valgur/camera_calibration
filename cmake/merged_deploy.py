# source: https://gist.github.com/valgur/27175e6095096b5db1113542eabe7bb0

import os
import shutil

from conan.api.output import ConanOutput
from conans.errors import ConanException
from conans.util.files import rmdir, mkdir


def deploy(graph, output_folder):
    """
    Merge all dependency package folders into a single <deploy-folder>/merged_deploy/<build/host> folder.
    """
    conanfile = graph.root.conanfile
    output = ConanOutput(scope="merged_deploy")
    output_folder = os.path.join(output_folder, "merged_deploy")
    rmdir(output_folder)
    mkdir(output_folder)
    ignored = shutil.ignore_patterns("licenses", "conaninfo.txt", "conanmanifest.txt")
    for context, deps in [("build", conanfile.dependencies.build), ("host", conanfile.dependencies.host)]:
        subdir = os.path.join(output_folder, context)
        mkdir(subdir)
        for _, dep in deps.items():
            if dep.package_folder is None:
                output.error(f"{dep.ref} does not have a package folder, skipping")
                continue
            _copytree(dep.package_folder, subdir,
                      conanfile, dep, output, dirs_exist_ok=True, ignore=ignored)
            if os.path.exists(os.path.join(dep.package_folder, "licenses")):
                _copytree(os.path.join(dep.package_folder, "licenses"),
                          os.path.join(subdir, "licenses", dep.ref.name),
                          conanfile, dep, output, dirs_exist_ok=True)
            dep.set_deploy_folder(subdir)
    conanfile.output.success(f"Deployed dependencies to: {output_folder}")


def _copytree(src, dst, conanfile, dep, output, **kwargs):
    symlinks = conanfile.conf.get("tools.deployer:symlinks", check_type=bool, default=True)
    try:
        shutil.copytree(src, dst, symlinks=symlinks, **kwargs)
    except Exception as e:
        if "WinError 1314" in str(e):
            output.error("Symlinks on Windows require admin privileges or 'Developer mode = ON'",
                         error_type="exception")
        err = f"{output.scope}: Copying of '{dep}' files failed: {e}."
        if symlinks:
            err += "\nYou can use 'tools.deployer:symlinks' conf to disable symlinks"
        raise ConanException(err)
