'''
This script load the json dump and insert the tuples into the alyxraw table.
'''

import datajoint as dj
import json
import logging
import math
import os.path as path
from ibl_pipeline.ingest import alyxraw, InsertBuffer
import sys


logger = logging.getLogger(__name__)

dir_name = path.dirname(__file__)


if len(sys.argv) < 2:  # no arguments given
    # if no argument given, assume a canonical file location and name
    filename = path.join(dir_name, '..', 'data', 'alyx_dump', 'alyxfull.json')
else:
    filename = path.join(dir_name, sys.argv[1])

with open(filename, 'r') as fid:
    keys = json.load(fid)

# use insert buffer to speed up the insersion process
ib_main = InsertBuffer(alyxraw.AlyxRaw)
ib_part = InsertBuffer(alyxraw.AlyxRaw.Field)

# insert into AlyxRaw table
for key in keys:
    ib_main.insert1(dict(uuid=key['pk'], model=key['model']))
    if ib_main.flush(skip_duplicates=True, chunksz=10000):
        logger.debug('Inserted 10000 raw tuples.')
    
if ib_main.flush(skip_duplicates=True):
    logger.debug('Inserted remaining raw tuples')

# insert into the part table AlyxRaw.Field
for key in keys:
    key_field = dict(uuid=key['pk'])
    for field_name, field_value in key['fields'].items():
        key_field = dict(key_field, fname=field_name)

        if field_name == 'json' and field_value is not None:
            key_field['value_idx'] = 0
            key_field['fvalue'] = json.dumps(field_value)
            ib_part.insert1(key_field)

        elif field_value == [] or field_value == '' or (type(field_value)==float and math.isnan(field_value)):
            key_field['value_idx'] = 0
            key_field['fvalue'] = 'None'
            ib_part.insert1(key_field)

        elif type(field_value) is list and (type(field_value[0]) is dict or type(field_value[0]) is str):
            for value_idx, value in enumerate(field_value):
                key_field['value_idx'] = value_idx
                key_field['fvalue'] = str(value)
                ib_part.insert1(key_field)   

        else:
            key_field['value_idx'] = 0
            key_field['fvalue'] = str(field_value)
            ib_part.insert1(key_field)

        if ib_part.flush(skip_duplicates=True, chunksz=10000):
            logger.debug('Inserted 10000 raw field tuples')

if ib_part.flush(skip_duplicates=True):
    logger.debug('Inserted all remaining raw field tuples')