import sys
from functools import partial
import logging
import click
import tomli
import asyncio
from . import __version__, PROGRAM


# Configure logging to stderr.
logging.basicConfig()


class _CLIState:
    """Manages CLI verbosity."""

    def __init__(self):
        self.debug = None
        self._verbosity = logging.WARNING

    @property
    def logpath(self):
        # Use the root logger if debugging is enabled.
        return None if self.debug else __package__

    @property
    def verbosity(self):
        """Verbosity on stdout."""
        return self._verbosity

    @verbosity.setter
    def verbosity(self, verbosity):
        verbosity = self._verbosity - 10 * int(verbosity)
        verbosity = min(max(verbosity, logging.DEBUG), logging.CRITICAL)
        self._verbosity = verbosity
        # Set the logger's level.
        logging.getLogger(self.logpath).setLevel(self._verbosity)

    @property
    def verbose(self):
        """Verbose output enabled.

        Returns
        -------
        True if the verbosity is enough for WARNING (and lower) messages to be displayed; False
        otherwise.
        """
        return self.verbosity <= logging.WARNING

    def _echo(self, *args, err=False, exit_=False, **kwargs):
        click.echo(*args, err=err, **kwargs)

        if exit_:
            code = 1 if err else 0
            sys.exit(code)

    def echo(self, *args, **kwargs):
        if self.verbosity > logging.WARNING:
            return

        self._echo(*args, **kwargs)

    def echo_info(self, msg, *args, **kwargs):
        if self.verbosity > logging.INFO:
            return

        msg = click.style(msg, fg="blue")
        self._echo(msg, *args, **kwargs)

    def echo_error(self, msg, *args, **kwargs):
        if self.verbosity > logging.ERROR and not self.debug:
            return

        msg = click.style(msg, fg="red")
        self._echo(msg, *args, err=True, **kwargs)

    def echo_exception(self, exception, *args, **kwargs):
        if not self.debug:
            # Just echo the error string, not the traceback.
            return self.echo_error(str(exception), *args, **kwargs)

        import traceback

        should_exit = kwargs.pop("exit_", False)

        tb = "".join(traceback.format_tb(exception.__traceback__))
        self._echo(tb, *args, err=True, exit_=False, **kwargs)
        msg = click.style(str(exception), fg="red")
        self._echo(msg, *args, err=True, exit_=should_exit, **kwargs)

    def echo_warning(self, msg, *args, **kwargs):
        if self.verbosity > logging.WARNING:
            return

        msg = click.style(msg, fg="yellow")
        self._echo(msg, *args, **kwargs)

    def echo_debug(self, *args, **kwargs):
        if self.verbosity > logging.DEBUG:
            return

        self._echo(*args, **kwargs)

    def echo_key(self, key, separator=True, nl=True):
        key = click.style(key, fg="green")
        if separator:
            key = f"{key}: "
        self.echo(key, nl=nl)

    def echo_key_value(self, key, value):
        self.echo_key(key, separator=True, nl=False)
        self.echo(value)


def _set_state_flag(ctx, _, value, *, flag):
    """Set state flag."""
    state = ctx.ensure_object(_CLIState)
    setattr(state, flag, value)


def _set_verbosity(ctx, param, value):
    """Set state verbosity."""
    state = ctx.ensure_object(_CLIState)

    # Quiet verbosity is negative.
    if param.name == "quiet":
        value = -value

    state.verbosity = value


verbose_option = click.option(
    "-v",
    "--verbose",
    count=True,
    callback=_set_verbosity,
    expose_value=False,
    is_eager=True,
    help="Increase verbosity (can be specified multiple times).",
)
quiet_option = click.option(
    "-q",
    "--quiet",
    count=True,
    callback=_set_verbosity,
    expose_value=False,
    help="Decrease verbosity (can be specified multiple times).",
)
debug_option = click.option(
    "--debug",
    is_flag=True,
    default=False,
    callback=partial(_set_state_flag, flag="debug"),
    expose_value=False,
    is_eager=True,
    help=(
        f"Show full exceptions when errors are encountered, and display all (not just those of "
        f"{PROGRAM}) logs when -v is specified."
    ),
)
version_option = click.version_option(version=__version__, prog_name=PROGRAM)


@click.command()
@click.argument("config_file", type=click.File(mode="rb"))
@verbose_option
@quiet_option
@debug_option
@version_option
@click.pass_context
def bridge(ctx, config_file):
    """MQTT topic provider for IoT projects."""
    from .bridge import Bridge

    state = ctx.ensure_object(_CLIState)

    try:
        config = tomli.load(config_file)
    except tomli.TOMLDecodeError as err:
        state.echo_exception(err, exit_=True)

    # Run the bridge.
    state.echo_info("Starting bridge")
    try:
        bridgeobj = Bridge(**config)
        asyncio.run(bridgeobj.main())
    except Exception as err:
        state.echo_exception(err, exit_=True)
    finally:
        state.echo_info("Bridge stopped")


if __name__ == "__main__":
    bridge()
