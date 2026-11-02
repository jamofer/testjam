"""Import every module of the installed packages to catch syntax or typing
features newer than the oldest supported Python."""
import importlib
import pkgutil
import sys

PACKAGES = ("testjam_client", "testjam_listener")


def main() -> int:
    failures = [
        (name, error)
        for package_name in PACKAGES
        for name in _module_names(package_name)
        if (error := _import_error(name)) is not None
    ]
    for name, error in failures:
        print(f"{name}: {error!r}", file=sys.stderr)
    return 1 if failures else 0


def _module_names(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)
    return [package_name] + [
        module.name for module in pkgutil.walk_packages(package.__path__, f"{package_name}.")
    ]


def _import_error(name: str) -> Exception | None:
    try:
        importlib.import_module(name)
    except Exception as error:
        return error
    return None


if __name__ == "__main__":
    sys.exit(main())
