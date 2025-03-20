import casatasks

from cal_cabb.logger import filter_stdout


@filter_stdout(
    "XYZHAND keyword not found in AN table.",
    "No systemic velocity",
    "No rest frequency",
)
def importuvfits(*args, **kwargs):
    return casatasks.importuvfits(*args, **kwargs)


def listobs(*args, **kwargs):
    return casatasks.listobs(*args, **kwargs)
