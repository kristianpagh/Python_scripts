#!/usr/bin/python3

import math
import os
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

infile=sys.argv[1]
outfile=sys.argv[2]
with (
      open(infile, "rb") as f_in, 
      open(outfile,"wb") as f_out
     ):
    while True:
        # Load the next GRIB message/field
        field_id = codes_grib_new_from_file(f_in)
        if field_id is None:
            break
        shortName = codes_get(field_id, "shortName")
        if not 'u' in locals():
            if shortName == "10u" or shortName == "u" or shortName == "avg10u":
                nx = codes_get(field_id, "Ni")
                ny = codes_get(field_id, "Nj")
                grid_boxes = codes_get(field_id, "numberOfPoints")
                long = codes_get_array(field_id, "longitudes").reshape(ny, nx)
                lat = codes_get_array(field_id, "latitudes").reshape(ny, nx)
                u = codes_get_values(field_id)
        if not 'v' in locals():
            if shortName == "10v" or shortName == "v" or shortName == "avg10v":
                v = codes_get_values(field_id)
        # The code only reads the first available set of u and v!
        if 'u' in locals() and 'v' in locals():
            break

    wdir=[0]*grid_boxes
    for jy in range(0,ny):
        for jx in range(0,nx-1):
            j=jy*nx+jx
            # Compute the apparent wind direction relative to the grid:
            wdir[j] = 180.0/math.pi*math.atan2(u[j],v[j])+180.0
            dlong=long[jy,jx+1]-long[jy,jx]
            if dlong <= -180.0:
                dlong=dlong+360.0
            if dlong > 180.0:
                dlong=dlong-360.0
            dlat=lat[jy,jx+1]-lat[jy,jx]
            if 'rotation' in locals():
                protation=rotation
            # The grid rotation is positive in the clockwise direction:
            rotation=-math.atan2(dlat,dlong)/math.pi*180.0
            # Correct for the grid rotation:
            wdir[j]=wdir[j]-rotation 
            if wdir[j] < 0.0:
                wdir[j]=wdir[j]+360.0
            if wdir[j] > 360.0:
                wdir[j]=wdir[j]-360.0
        # Extrapolate the grid rotation for jx=nx:
        j=jy*nx+nx-1
        tmprotation=rotation+rotation-protation
        if tmprotation <= -180.0:
            tmprotation=tmprotation+360.0
        if tmprotation > 180.0:
            tmprotation=tmprotation-360.0
        # Correct for the grid rotation of jx=nx:
        wdir[j]=wdir[j]-tmprotation 
        if wdir[j] < 0.0:
            wdir[j]=wdir[j]+360.0
        if wdir[j] >= 360.0:
            wdir[j]=wdir[j]-360.0

    codes_set_values(field_id, wdir)
    codes_set(field_id, "shortName", "10wdir")
    codes_write(field_id, f_out)
    codes_release(field_id)
