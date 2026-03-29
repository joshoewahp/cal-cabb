import logging

import astropy.units as u
import click
import numpy as np
from astropy.coordinates import SkyCoord
from dstools.logger import setupLogger
from dstools.ms import MeasurementSet

logger = logging.getLogger(__name__)


@click.command()
@click.argument("ms-path")
@click.argument("target-name")
@click.argument("target-ra")
@click.argument("target-dec")
def main(ms_path, target_name, target_ra, target_dec):
    ms = MeasurementSet(ms_path)

    setupLogger(verbose=True)

    # Create new field
    # ----------------
    logger.info(f"Creating new FIELD entry for {target_name}.")

    with ms.open_table(subtable="FIELD", readonly=False) as t:
        # Add one new field
        target_field_id = t.nrows()
        t.addrows(1)

        # Copy columns from first field into new
        for col in t.colnames():
            val = t.getcell(col, 0)
            t.putcell(col, target_field_id, val)

        # Update name
        t.putcell("NAME", target_field_id, target_name)

        # Set target position
        coord = SkyCoord(ra=target_ra, dec=target_dec, unit="hourangle,deg")
        dir_rad = np.array(
            [
                [
                    coord.ra.to(u.rad).value,
                    coord.dec.to(u.rad).value,
                ]
            ]
        )
        t.putcell("PHASE_DIR", target_field_id, dir_rad)
        t.putcell("DELAY_DIR", target_field_id, dir_rad)
        t.putcell("REFERENCE_DIR", target_field_id, dir_rad)

        print(t.getcol("NAME"))

    # Reassign target scans to new field ID
    with ms.open_table(readonly=False) as t:
        # Get target scan rows, should have more than 10k rows in a scan
        scans = t.getcol("SCAN_NUMBER")
        unique_scans, counts = np.unique(scans, return_counts=True)
        target_scans = unique_scans[counts > 20000]
        target_rows = np.isin(scans, target_scans)
        logger.info(f"Assigning scans in rows {target_rows} to {target_name} field.")

        # Reassign field IDs
        field_ids = t.getcol("FIELD_ID")
        field_ids[target_rows] = target_field_id
        t.putcol("FIELD_ID", field_ids)

    # Diagnostic
    with ms.open_table() as t:
        scans = t.getcol("SCAN_NUMBER")
        field_ids = t.getcol("FIELD_ID")

        for s in np.unique(scans):
            mask = scans == s
            fids = np.unique(field_ids[mask])
            print(f"Scan {s}: rows={mask.sum()}, FIELD_ID={fids}")

    return


if __name__ == "__main__":
    main()
