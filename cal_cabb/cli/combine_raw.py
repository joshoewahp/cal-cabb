import logging
from pathlib import Path

import click
from dstools.casa import concat
from dstools.logger import setupLogger
from dstools.ms import MeasurementSet

logger = logging.getLogger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging",
)
@click.argument("ms", type=MeasurementSet, nargs=-1)
@click.argument("out", type=Path)
def main(ms, out, verbose):
    setupLogger(verbose=verbose)

    vis = [str(mset) for mset in ms]

    concat(
        vis=vis,
        concatvis=str(out),
    )

    return


if __name__ == "__main__":
    main()
