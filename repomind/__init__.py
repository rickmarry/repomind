from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("repomind")
except PackageNotFoundError:
    __version__ = "unknown"