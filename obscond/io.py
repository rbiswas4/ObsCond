
__all__=['stripLeadingPoundFromHeaders']

def stripLeadingPoundFromHeaders(df):
    """
    on using `pandas.read_csv` on csv files with the header commented out with
    a '#', The '#' is often added to the name of the the first column. This
    function removes this pound in place.

    Parameters
    ----------
    df : `pandas.dataFrame`

    Returns
    -------
    None
    """
    df.rename(columns={df.columns[0]:df.columns[0][1:]}, inplace=True)
