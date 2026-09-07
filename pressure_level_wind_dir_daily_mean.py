#!/usr/bin/python3

import os
import numpy as np
import sys
from eccodes import (
    codes_grib_new_from_file,
    codes_get,
    codes_get_array,
    codes_get_values,
    codes_set,
    codes_set_values,
    codes_write,
    codes_release,
)

date=sys.argv[1]
infile=sys.argv[2]
outfile=sys.argv[3]
levels=set()
hours=set()
with open(infile, "rb") as f_in:
    while True:
        # Load the next GRIB message/field
        field_id = codes_grib_new_from_file(f_in)
        if field_id is None:
            break
        shortName = codes_get(field_id, "shortName")
        int_date = codes_get(field_id, "validityDate")
        str_date = f'{int_date:8d}'
        level_type = codes_get(field_id, "typeOfLevel")
        if (
            shortName == "wdir" and 
            str_date == date and 
            level_type == "isobaricInhPa"
           ):
             grid_boxes = codes_get(field_id, "numberOfPoints")
             hour = codes_get(field_id, "validityTime")            
             hours.add(hour)
             level = codes_get(field_id, "level")            
             levels.add(level)
        codes_release(field_id)

hours = sorted(hours)
levels = sorted(levels)

u = np.zeros((len(levels), grid_boxes))
v = np.zeros((len(levels), grid_boxes))
avg_wdir = np.zeros(grid_boxes))
count_check=0
with (
      open(infile, "rb") as f_in, 
      open(outfile, "wb") as f_out
     ):
    while True:
        # Load the next GRIB message/field
        field_id = codes_grib_new_from_file(f_in)
        if field_id is None:
            break
        shortName = codes_get(field_id, "shortName")
        int_date = codes_get(field_id, "validityDate")
        str_date = f'{int_date:8d}'
        level_type = codes_get(field_id, "typeOfLevel")
        if (
            shortName == "wdir" and 
            str_date == date and 
            level_type == "isobaricInhPa"
           ): 
            count_check += 1
            level = codes_get(field_id, "level")            
            idx = levels.index(level) 
            wdir = codes_get_values(field_id)
            u[idx,:] = u[idx,:] - np.sin(wdir[:]/180.0*np.pi)
            v[idx,:] = v[idx,:] - np.cos(wdir[:]/180.0*np.pi)
        if (count_check == len(hours)*len(levels)):
            for l in range(0,len(levels)):
                avg_wdir = 180.0/np.pi*np.arctan2(u[l,:],v[l,:])+180.0
                codes_set_values(field_id, avg_wdir)
                codes_set(field_id, "level", levels[l])
                codes_write(field_id, f_out)
        codes_release(field_id)
    if (count_check != len(hours)*len(levels)):
        print('Incorrect number of pressure level fields for this day!')
        print('Number of hours'+len(hours))
        print('Number of pressure levels'+len(levels))
        print('Number of fields'+count_check)
