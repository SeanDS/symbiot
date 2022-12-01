# flake8: noqa

"""MQTT topic provider for IoT projects."""

from importlib.metadata import entry_points

PROGRAM = __name__

# Set version.
try:
    from ._version import version as __version__
except ImportError:
    raise Exception("Could not find version.py. Ensure you have run setup.")


# Load receiver plugins registered via entry points (i.e. in other packages).
for entry_point in entry_points().get("symbiot.receiver", {}):
    entry_point.load()
