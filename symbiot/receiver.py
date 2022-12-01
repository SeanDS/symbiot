import abc
import logging
import warnings

LOGGER = logging.getLogger(__name__)


# Mapping of names to receiver types.
_RECEIVERS = dict()


def get(name):
    """Fetch receiver type by name."""
    try:
        return _RECEIVERS[name]
    except KeyError:
        raise ValueError(f"Receiver {repr(name)} not found")


def register(cls):
    name = cls.__name__.casefold()

    if name in _RECEIVERS:
        warnings.warn(f"Overwriting registered receiver {_RECEIVERS[name]} with {cls}")

    _RECEIVERS[name] = cls


class Receiver(metaclass=abc.ABCMeta):
    """Base asynchronous receiver interface."""

    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        register(cls)

    @abc.abstractmethod
    async def run(self):
        raise NotImplementedError
