#!/usr/bin/env python
"""
script to take the hdf file created by recalculating quantities in the OpSim database using the sims_skybrightness model and copy the new quantities into a sqlite database with the exact schema that OpSim databases have.The output is thus a recalculated opsim database  

Here is an example command used in running this

>>> nohup python joinValues.py /local/lsst/rbiswas/data/LSST/OpSimData/minion_1016_sqlite.db newOpSim.hdf > joinvalues.log 2>&1
"""
import numpy as np
import pandas as pd
from opsimsummary import OpSimOutput
import argparse
import os
import sys
import shutil
from sqlalchemy import create_engine
import time

def copy2EmptyOpSim(givenOpSim, newOpSim):
    """
    create the target opsim database by copying and deleting all the rows of
    the table named `Summary`

    ..note : adding columns in sqlite is painful
    """
    shutil.copyfile(givenOpSim, newOpSim)
    engine = create_engine('sqlite:///' + newOpSim)
    connection = engine.connect()
    res = connection.execute('DELETE FROM Summary')
    return None

def createJoinedTable(opsimSummary, results):
    """
    """
    tstart = time.time()
    result = opsimSummary.join(results, lsuffix='_old')
    cols = list(col for col in result.columns if not col.endswith('_old'))
    tend = time.time()
    return result[cols], tend - tstart

def write2EmptyTable(targetOpSim, results, tableName='Summary'):
    """
    """
    tstart = time.time()

    # Write to the database 
    engine = create_engine('sqlite:///' + targetOpSim)
    results.to_sql(name='Summary', con=engine, if_exists='append')
    tend = time.time()
    print('time taken to write table to database is {} seconds \n'.format(tend - tstart))
    return None

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='script to create new opsim output with new skybrightnesses')
    parser.add_argument('opsimDB', help='absolute path to opsim database')
    parser.add_argument('results', help='absolute path to hdf file with results for skybrightness and fiveSigmaDepths')
    parser.add_argument('--newopsim', type=str, default='minion_1016_recalc.db', help='absolute path to new database')
    args = parser.parse_args()
    sys.stdout.flush()
    
    # create the target opsim database by copying and deleting all the rows of the table 
    # (Adding cols seems slow in sqlite)
    tstart = time.time()
    copy2EmptyOpSim(args.opsimDB, newOpSim=args.newopsim)
    tend = time.time()
    print('time taken to copy opsim tables and create empty table is {} sec\n'.format(tend - tstart))
    
    # Obtain the result from the hdf file and filter the nans
    results  = pd.read_hdf(args.results)
    
    # Obtain all the records from OpSim
    tstart = time.time()
    opsimSummary = OpSimOutput.fromOpSimDB(args.opsimDB, subset='_all').summary
    tend = time.time()
    print('time taken to read opsim data is {} sec\n'.format(tend - tstart))

    # Obtain the correctly joined dataframe
    res, timetaken = createJoinedTable(opsimSummary, results) 
    print('time taken to join the data is {} sec\n'.format(timetaken))

    # Write to the database
    write2EmptyTable(targetOpSim=args.newopsim,
                     results=res,
                     tableName='Summary')
