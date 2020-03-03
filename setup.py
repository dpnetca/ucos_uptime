import pkg_resources
from os.path import join, basename
from cx_Freeze import setup, Executable


def collect_dist_info(packages):
    """
    Recursively collects the path to the packages' dist-info.
    """
    if not isinstance(packages, list):
        packages = [packages]
    dirs = []
    for pkg in packages:
        distrib = pkg_resources.get_distribution(pkg)
        for req in distrib.requires():
            dirs.extend(collect_dist_info(req.key))
        dirs.append(
            (distrib.egg_info, join("lib", basename(distrib.egg_info)))
        )
    return dirs


include_files = collect_dist_info(["nornir"])
include_files.append(("yamls/config.yaml", "yamls/config.yaml"))
include_files.append(("yamls/hosts.yaml", "yamls/hosts.yaml"))
include_files.append(("yamls/groups.yaml", "yamls/groups.yaml"))
include_files.append(("yamls/defaults.yaml", "yamls/defaults.yaml"))

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(
    namespace_packages=[
        "ruamel.yaml",
        "cffi",
        "nornir.plugins.inventory.simple",
    ],
    packages=["os", "cffi", "idna"],
    include_files=include_files,
    excludes=[],
)


base = "Console"

executables = [Executable("uptime.py", base=base, targetName="ucos_uptime")]

setup(
    name="ucos_uptime",
    version="1.0",
    description="uptime for ucos servers",
    options=dict(build_exe=buildOptions),
    executables=executables,
)
