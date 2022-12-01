"""MQTT bridge."""

import logging
import asyncio
from contextlib import AsyncExitStack
from asyncio_mqtt import Client as AsyncMQTTClient
from .receiver import get as get_receiver

LOGGER = logging.getLogger(__name__)


class Bridge:
    """MQTT bridge."""

    def __init__(self, **config):
        try:
            mqtt_options = config.pop("mqtt")
        except KeyError:
            raise ValueError(
                f"An 'mqtt' section is required in the configuration file."
            )

        self.mqtt_broker_host = mqtt_options["broker_host"]
        self.receiver_config = config

    @property
    def mqtt_client_id(self):
        """The client ID to use for communication with the MQTT broker."""
        return __package__

    async def main(self):
        """Run bridge."""
        host = self.mqtt_broker_host
        client_id = self.mqtt_client_id

        # Connect to the MQTT broker.
        async with AsyncMQTTClient(host, client_id=client_id) as mqtt_client:
            tasks = set()

            # Set up receivers as asynchronous tasks.
            for name, options in self.receiver_config.items():
                receivercls = get_receiver(name)
                receiver = receivercls(mqtt_client=mqtt_client, **options)

                # Create task.
                task = asyncio.create_task(receiver.run())
                tasks.add(task)

            # Run tasks.
            await asyncio.gather(*tasks)

        LOGGER.info("Finished bridge")
