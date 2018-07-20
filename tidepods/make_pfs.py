import os
import subprocess
import sys

from . import generate_pts as gp


def generatepfs(infile, date, mikepath, tempdir):
    """Generates a pfs file using DHI.PFS

    Parameters
    ----------
    infile : str
        Path to AOI polygon.

    date : datetime.datetime
        Image acqusition date and time

    mikepath : str
        Path to MIKE installation directory

    tempdir : str
        Path to temporary directory

    Returns
    -------
    temppfs :  str
        Path to the generate pfs file within the tempdir

    """

    temppfs = os.path.join(tempdir, 'temp.pfs')

    sdkpath = os.path.join(mikepath, r'MIKE SDK\bin')
    constituents_path = os.path.join(mikepath,
                                     r'MIKE Zero\Application Data\Tide_Constituents\global_tide_constituents_0.125deg.dfs2')
    prepack_path = os.path.join(mikepath,
                                r'MIKE Zero\Application Data\Tide_Constituents\prepack.dat')

    import clr

    clr.AddReference('System')

    import System

    try:
        sys.path.insert(0, sdkpath)

    except System.IO.FileNotFoundException as exception:
        msg = "Reference not found. Is the path to the sdk correct: '{0}'?".format(sdkpath)
        raise ValueError(msg) from exception

    clr.AddReference(r'DHI.PFS')

    import DHI.PFS

    sys.path.pop(0)

    plist = gp.generate_pts(infile)

    # Begin PFS Generation Parameters using DHI.PFS.PFSBuilder

    pfsbuilder = DHI.PFS.PFSBuilder()

    pfsbuilder.AddTarget('TidePredictor')  # First Section

    pfsbuilder.AddKeyword('Name')
    pfsbuilder.AddString(str(infile))
    pfsbuilder.AddKeyword('constituent_file_name')
    pfsbuilder.AddString(str(constituents_path))
    pfsbuilder.AddKeyword('prepack_file_name')
    pfsbuilder.AddString(str(prepack_path))
    pfsbuilder.AddKeyword('start_date')
    DHI.PFS.PFSExtensions.AddDate(pfsbuilder, System.DateTime(date.year, 1, 1))
    pfsbuilder.AddKeyword('end_date')
    DHI.PFS.PFSExtensions.AddDate(pfsbuilder, System.DateTime(date.year, 12, 31))
    pfsbuilder.AddKeyword('timestep')
    pfsbuilder.AddDouble(0.5)
    pfsbuilder.AddKeyword('number_of_files')
    pfsbuilder.AddInt(1)
    pfsbuilder.AddKeyword('ShowGeographic')
    pfsbuilder.AddInt(1)

    pfsbuilder.AddSection('File_1')  # File Section
    pfsbuilder.AddKeyword('format')
    pfsbuilder.AddInt(0)
    pfsbuilder.AddKeyword('file_name')
    pfsbuilder.AddFileName(temppfs.replace('.pfs', '.dfs0'))
    pfsbuilder.AddKeyword('description')
    pfsbuilder.AddString('Predicted Tide Level')
    pfsbuilder.AddKeyword('number_of_points')
    pfsbuilder.AddInt(len(plist))

    # Points section enumerated for each point generated within shapefile

    for pid, p in enumerate(plist, 1):
        pfsbuilder.AddSection('Point_' + str(pid))
        pfsbuilder.AddKeyword('description')
        pfsbuilder.AddInt(pid)
        pfsbuilder.AddKeyword('y')
        pfsbuilder.AddDouble(p.coords[0][1])
        pfsbuilder.AddKeyword('x')
        pfsbuilder.AddDouble(p.coords[0][0])
        pfsbuilder.EndSection()

    pfsbuilder.EndSection()
    pfsbuilder.EndSection()
    pfsbuilder.Write(temppfs)

    return temppfs


def make_dfs0(infile, date, mikepath, tempdir):
    """Generates a dfs0 file from the above PFS

    Parameters
    ----------
    infile : str
        Path to AOI polygon.

    date : datetime.datetime
        Image acqusition date and time

    mikepath : str
        Path to MIKE installation directory

    tempdir : str
        Path to temporary directory

    Returns
    -------
    dfsfile :  str
        Path to the generate dfs0 file within the tempdir

    """

    pfsfile = generatepfs(infile, date, mikepath, tempdir)
    tidepredictor = os.path.join(mikepath, 'bin/x64/TidePredictor.exe')
    cmd = tidepredictor + ' ' + pfsfile

    subprocess.check_call(cmd)

    dfsfile = pfsfile.replace('.pfs', '.dfs0')

    return dfsfile
