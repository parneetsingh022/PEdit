from importlib.metadata import version, metadata

__version__ = version("image_editor")
__project__ = metadata("image_editor")["Name"]
