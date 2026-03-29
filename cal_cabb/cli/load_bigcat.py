import logging
import os
from pathlib import Path
from typing import Optional

import click
import numpy as np
from dstools.casa import exportuvfits, flagdata, mstransform
from dstools.logger import setupLogger
from dstools.ms import MeasurementSet

logger = logging.getLogger(__name__)


def split_targets(uvout: Path, startfreq: str, out_prefix: Optional[str]):
    # Set up temporary directory to dump uvsplit files
    temp_dir = uvout.parent.absolute() / "temp_fileconv"
    os.system(f"mkdir -p {temp_dir}")
    os.system(f"mv {uvout} {temp_dir}/.")

    # Split miriad visibilities
    cwd = Path(".").absolute()
    os.chdir(temp_dir)
    os.system(f"uvsplit vis={uvout.name}")
    os.system(f"rm -r {uvout.name}")
    os.chdir(cwd)

    # Prepend out_prefix and move files into current directory
    out_prefix = f"{out_prefix}." if out_prefix is not None else ""
    for f in temp_dir.glob("*"):
        os.system(f"mv {f} {out_prefix}{f.name}")

    # Clean up
    os.system(f"rm -r {temp_dir}")

    return


def get_spw_ranges(mset: MeasurementSet) -> list[str]:
    spw_channels = mset.getcolumn("NUM_CHAN", subtable="SPECTRAL_WINDOW")
    spw_start_freqs = mset.getcolumn("CHAN_FREQ", subtable="SPECTRAL_WINDOW")[:, 0]

    nchannels = np.unique(spw_channels)
    if len(nchannels) > 1:
        logger.warning("SPWs do not contain equal channel numbers.")
        exit(1)

    nspws = len(spw_channels)
    nchan = nchannels[0] * nspws

    # Identify SPW indices where new IFs start (> 128 MHz apart)
    diff = np.diff(spw_start_freqs)
    spw_width = 128e6
    if_starts = np.where(np.abs(diff) > spw_width)[0] + 1

    n_ifs = len(if_starts) + 1
    logger.debug(
        f"Located {nspws} SPWs ({nchannels[0]} channels each) in {n_ifs} IFs. Total channels: {nchan}"
    )

    # Add boundaries
    bounds = np.concatenate(([0], if_starts, [len(spw_start_freqs)]))

    # Build CASA-style ranges
    spwranges = [f"{start}~{end - 1}" for start, end in zip(bounds[:-1], bounds[1:])]
    startfreqs = [spw_start_freqs[i] / 1e6 for i in np.append([0], if_starts)]

    return startfreqs, spwranges


@click.command(context_settings={"show_default": True})
@click.option(
    "-o",
    "--out-prefix",
    default=None,
    type=str,
    help="Name to prepend to generated miriad files.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging",
)
@click.argument("ms", type=Path)
def main(ms, out_prefix, verbose):
    setupLogger(verbose=verbose)

    ms_temp = ms.with_suffix(".mir.ms")

    logger.debug("Loading MS")
    mset = MeasurementSet(ms)

    startfreqs, spwranges = get_spw_ranges(mset)
    print(startfreqs)
    print(spwranges)

    for startfreq, spwrange in zip(startfreqs, spwranges):
        logger.info(f"Processing {startfreq} IF")
        mir_ms = ms_temp.with_suffix(f".{startfreq}.ms")
        print(spwrange)

        # Combine spectral windows
        logger.debug("Combining SPWs")
        mstransform(
            vis=str(ms),
            combinespws=True,
            datacolumn="all",
            spw=spwrange,
            outputvis=str(mir_ms),
        )

        # Flag autocorrelations
        logger.debug("Flagging Autos")
        flagdata(
            vis=str(mir_ms),
            mode="manual",
            autocorr=True,
        )

        # Export to UVfits
        logger.debug("Converting to MIRIAD uv")
        fitsfile = mir_ms.with_suffix(".uv.fits")
        exportuvfits(
            vis=str(mir_ms),
            fitsfile=str(fitsfile),
            combinespw=True,
        )

        # Convert to UV
        uvout = fitsfile.with_suffix("")
        os.system(f"fits in={fitsfile} out={uvout} op=uvin")

        # Split targets
        split_targets(uvout, startfreq, out_prefix)

        # Clean up
        os.system(f"rm -r {fitsfile} {mir_ms} {mir_ms}.flagversions")

    return


if __name__ == "__main__":
    main()
