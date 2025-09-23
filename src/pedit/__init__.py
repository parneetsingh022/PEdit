from importlib.metadata import version, metadata

__version__ = version("pedit")
__project__ = metadata("pedit")["Name"]
