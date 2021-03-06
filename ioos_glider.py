# 2013 derrick.snowden@noaa.gov: initial version of python script for creating
#   IOOS glider NetCDF template.
# 2013-07-19 kerfoot@marine.rutgers.edu: modified script to adhere to most
#   recent version of CDL template:
#     - creation of variables and addition of recommended variable attributes
#     - variable attributes are added as dictionary items so that they can be
#       sorted and added alphabetically.
# 2013-07-22 dsnowden: modified script to include github issues where appropriate 
#   and to resolve several issues.
# 2013-07-30 kerfoot: mods to trajectory variable, moved accuracy, precision,
#   resolution attributes from the instrument_ctd variable to the appropriate
#   data variables.
# 2013-08-02 kerfoot: added lat_uv, lon_uv variables, 'sensor_name' attribute
#   to applicable variables.  Added 'reference' and
#   'coordinate_reference_frame' attributes to lat & lon per GROOM spec.
#   Added 'flag_meanings' and 'flag_values' attribute values per GROOM spec.
# 2013-08-06 kerfoot: removed 'flag_meanings' attribute from lat_uv & lon_uv.
#   Added 'coordinates' attribute and values to lat_uv & lon_uv.
#
# Script to create example glider trajectory file.
# DIMENSIONS (SIZE):
#   trajectory: (1)
#   time: (unlim)
#   time_uv: (1)
# REQUIRED Variables
#   trajectory(trajectory): int
#   time(time): double
#   time_uv(time): double
#   segment_id(time): int
#   profile_id(time): int
#   depth(time): double
#   depth_qc(time): byte
#   lat(time): double
#   lat_qc(time): byte
#   lon(time): double
#   lon_qc(time): byte
#   pressure(time): double
#   pressure_qc(time): byte
#   conductivity(time): double
#   conductivity_qc(time): byte
#   salinity(time): double
#   salinity_qc(time): byte
#   density(time): double
#   density(time): byte
#   temperature(time): double
#   temperature_qc(time): byte
#   lat_uv(time_uv): double
#   lon_uv(time_uv): double
#   u(time_uv): double
#   u_qc(time_uv): byte
#   v(time_uv): double
#   v_qc(time_uv): byte
#   lat_uv(time_uv): double
#   lon_uv(time_uv): double
#   platform(nodim)
#   instrument_ctd(nodim)
#
# This template is used to generate an empty (no data values) .nc file.  The
# .nc file may then be dumped to .cdl and .ncml.  A generic filename is used
# for the destination file.  Files containing actual glider data should follow
# the file naming conventions at:
# https://github.com/IOOSProfilingGliders/Real-Time-File-Format/wiki/Real-Time-File-Description#file-naming-convention

import numpy as np
from datetime import datetime, timedelta
from netCDF4 import default_fillvals as NC_FILL_VALUES
from netCDF4 import num2date, date2num
from netCDF4 import Dataset
import time as t
from flask import Flask, Response, request
import geojson as gj
from getncattrs import __call__ as getncattrs
app = Flask(__name__)
app.debug = True

# NetCDF4 compression level (1 seems to be optimal, in terms of effort and
# result)
COMP_LEVEL = 1

def romssim_read(filename):
    with Dataset(filename) as nc:
        vars = nc.variables
        lon = vars["lon"][:]
        lat = vars["lat"][:]
        depth = vars["depth"][:]
        dens = vars["rho"][:]
        temp = vars["temp"][:]
        salt = vars["salt"][:]
        time = vars["ocean_time"][:]
        datetime = num2date(time, units=vars["ocean_time"].units)
    response = {"lon":lon, "lat":lat, "depth":depth,
                "dens":dens, "temp":temp, "salt":salt,
                "time":time, "datetime":datetime}
    return response

def romssim_write(filename, output, ver="0.0"):
    processing_level = ""
    source = ""
    roms = romssim_read(filename)
    if ver=="0.0":
        dummy = np.ones_like(roms["lon"]) * np.nan
        dummyuv = np.ones((1,roms["lon"].shape[1])) * np.nan
        dummytimeuv = np.ndarray((1,), dtype=type(roms["datetime"][0]))
        dummytimeuv[:] = roms["datetime"][0]
        traj = np.arange(roms["lon"].shape[1])
        writer_0_0(output, roms["datetime"], dummytimeuv, traj, dummy, dummy, roms["depth"], roms["lat"], roms["lon"], dummy, dummy, roms["dens"], roms["salt"], roms["temp"], dummyuv, dummyuv, dummyuv, dummyuv, processing_level=processing_level, source=source)

def writer_0_0(filename, timedata, time_uvdata, trajectorydata, segment_iddata,
               profile_iddata, depthdata, latdata, londata, pressuredata, 
               conductivitydata, densitydata, salinitydata, temperaturedata, udata, vdata, 
               lat_uvdata, lon_uvdata, time_qcdata=None, u_qcdata=None, v_qcdata=None,
               depth_qcdata=None, lat_qcdata=None, lon_qcdata=None, pressure_qcdata=None,
               conductivity_qcdata=None, density_qcdata=None, salinity_qcdata=None,
               temperature_qcdata=None, **kwargs):
    # Name of output file (leave v.0.0 pending release of accepted spec):
    # kerfoot@marine.rutgers.edu
    nc = Dataset(filename,
                 'w',
                 format='NETCDF4_CLASSIC')

    now = t.ctime(t.time())

    # Required vars list
    req_time_vars = [depthdata, latdata, londata, pressuredata, conductivitydata, densitydata, salinitydata, temperaturedata,]
    req_uv_vars = [udata, vdata, lat_uvdata, lon_uvdata]
    #req_traj_vars = req_time_vars + req_uv_vars
    quality_vars = [depth_qcdata, lat_qcdata, lon_qcdata, pressure_qcdata, conductivity_qcdata, density_qcdata, salinity_qcdata, temperature_qcdata]
    for var in quality_vars:
        if var != None:
            req_time_vars.append(var)
            #req_traj_vars.append(var)

    # Dimensions
    time_size = len(timedata)
    trajectory_size = len(trajectorydata)
    time_uv_size = len(time_uvdata)
    for var in req_time_vars:
        assert time_size == var.shape[0]
    #for var in req_traj_vars:
    #    assert trajectory_size == var.shape[1]
    for var in req_uv_vars:
        assert time_uv_size == var.shape[0] 
    time = nc.createDimension('time', time_size)
    trajectory = nc.createDimension('trajectory', trajectory_size)
    time_uv = nc.createDimension('time_uv', time_uv_size)
    dim_tuple = ('time',)
    uv_tuple = ('time_uv',)
    if len(trajectorydata) > 1:
        dim_tuple = ('time', 'trajectory',)
        uv_tuple = ('time_uv', 'trajectory',)

    # Global Attributes
    # 2013-07-22 kerfoot@marine.rutgers.edu: sync'd with github wiki global
    # attribute list.  Didn't resolve any DS comments/TODOs
    global_attributes = {
      'Conventions' : 'CF-1.6',
      'Metadata_Conventions' : 'Unidata Dataset Discovery v1.0', # TODO: A change has been proposed to ACDD.  Use this for now.
      'acknowledgment' : 'This deployment partially supported by ...', #
      'cdm_data_type' : 'Trajectory',
      'comment' : 'This file is intended to be used as a template only.  Data is not to be used for scientific purposes.',
      'contributor_name' : 'Scott Glenn, Oscar Schofield, John Kerfoot',
      'contributor_role' : 'Principal Investigator, Principal Investigator, Data Manager',
      'creator_email' : 'kerfoot@marine.rutgers.edu',
      'creator_name' : 'John Kerfoot',
      'creator_url' : 'http://marine.rutgers.edu/cool/auvs',
      'date_created' : now,
      'date_issued' : now,
      'date_modified' : now,
      'featureType' : 'trajectory',
      'format_version' : 'IOOS_Glider_NetCDF_Trajectory_Template_v0.0', # NOTE: Changed from file_version for conformance with GROOM.
      'geospatial_lat_max' : latdata.max(),
      'geospatial_lat_min' : latdata.min(),
      'geospatial_lat_resolution' : 'point',
      'geospatial_lat_units' : 'degrees_north',
      'geospatial_lon_max' : londata.max(),
      'geospatial_lon_min' : londata.min(),
      'geospatial_lon_resolution' : 'point',
      'geospatial_lon_units' : 'degrees_east',
      'geospatial_vertical_max' : depthdata.max(),
      'geospatial_vertical_min' : depthdata.min(),
      'geospatial_vertical_positive' : 'down',  
      'geospatial_vertical_resolution' : 'point',
      'geospatial_vertical_units' : 'meters',
      'history' : 'Created on ' + now,
      'id' : '',
      'institution' : 'Institute of Marine & Coastal Sciences, Rutgers University',
      'keywords' : 'Oceans > Ocean Pressure > Water Pressure, Oceans > Ocean Temperature > Water Temperature, Oceans > Salinity/Density > Conductivity, Oceans > Salinity/Density > Density, Oceans > Salinity/Density > Salinity',
      'keywords_vocabulary' : 'GCMD Science Keywords',
      'license' : 'This data may be redistributed and used without restriction.',
      'metadata_link' : '',
      'naming_authority' : 'edu.rutgers.marine',
      'processing_level' : 'Written to file from ioos_glider.writer_0_0()',
      'project' : 'Deployment not project based',
      'publisher_email' : 'kerfoot@marine.rutgers.edu',
      'publisher_name' : 'John Kerfoot',
      'publisher_url' : 'http://marine.rutgers.edu/cool/auvs',
      'references' : '',
      'sea_name' : '',
      'standard_name_vocabulary' : 'CF-v25', # TODO: Or, represent using URL e.g. http://cf-pcmdi.llnl.gov/documents/cf-standard-names/standard-name-table/25/
      'source' : 'Observational data from a profiling glider', 
      'summary' : 'The Rutgers University Coastal Ocean Observation Lab has deployed autonomous underwater gliders around the world since 1990. Gliders are small, free-swimming, unmanned vehicles that use changes in buoyancy to move vertically and horizontally through the water column in a saw-tooth pattern. They are deployed for days to several months and gather detailed information about the physical, chemical and biological processes of the world\'s The Slocum glider was designed and oceans. built by Teledyne Webb Research Corporation, Falmouth, MA, USA.',
      'time_coverage_end' : timedata[0].strftime('%Y-%m-%d %H:%M UTC'),
      'time_coverage_resolution' : 'point',
      'time_coverage_start' : timedata[-1].strftime('%Y-%m-%d %H:%M UTC'),
      'title' : 'Glider Dataset',
    }
    for key in kwargs.iterkeys():
        global_attributes[key] = kwargs[key]
    # Dictionary of global file attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    for k in sorted(global_attributes.keys()) :
        nc.setncattr(k, global_attributes[k])

    # Create array of unsigned 8-bit integers to use for _qc flag values
    QC_FLAGS = np.array(range(0,10), 'int8')
    # Meanings of QC_FLAGS
    QC_FLAG_MEANINGS = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed interpolated_value missing_value";

    # Variable Definitions

    # ----------------------------------------------------------------------------
    # TIME
    # time: no _Fill_Value since dimension
    time = nc.createVariable('time',
                             'f8',
                             ('time',),
                             zlib=True,
                             complevel=COMP_LEVEL)
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'axis' : "T",
            'calendar' : 'gregorian',
            'units' : 'seconds since 1970-01-01 00:00:00 UTC',
            'standard_name' : 'time',
            'long_name' : 'Time',
            'observation_type' : 'measured',
            'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        time.setncattr(k, atts[k])
    time[:] = date2num(timedata, units=atts['units'], calendar=atts['calendar'])

    # ----------------------------------------------------------------------------
    # TIME_QC
    # time_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    time_qc = nc.createVariable('time_qc',
                                'i1',
                                ('time',),
                                zlib=True,
                                complevel=COMP_LEVEL,
                                fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'time Quality Flag',
             'standard_name' : 'time status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        time_qc.setncattr(k, atts[k])
    if time_qcdata != None:
        time_qc[:] = time_qcdata
    # ----------------------------------------------------------------------------

    # time_uv: 64 bit float - no _Fill_Value since dimension
    time_uv = nc.createVariable('time_uv',
                                'f8',
                                ('time_uv',),
                                zlib=True,
                                complevel=COMP_LEVEL);
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'axis' : "T",
            'calendar' : 'gregorian',
            'units' : 'seconds since 1970-01-01 00:00:00 UTC',
            'standard_name' : 'time',
            'long_name' : 'Approximate time midpoint of each segment',
            'observation_type' : 'estimated',
    };
    for k in sorted(atts.keys()):
        time_uv.setncattr(k, atts[k])
    time_uv[:] = date2num(time_uvdata, units=atts['units'], calendar=atts['calendar'])
    # TODO: See [issue 2](https://github.com/IOOSProfilingGliders/Real-Time-File-Format/issues/2). 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # TRAJECTORY
    # trajectory: 2 byte integer - no _FillValue since dimension
    # TODO: See [issue 1](https://github.com/IOOSProfilingGliders/Real-Time-File-Format/issues/1). 
    # 2013-07-30 kerfoot: per discussion with dsnowden, we're going to go with
    # hard coding the value of this variable to the number 1 across all files.  
    # TODO: Create 2 sets of 2 files: the first file set contains trajectory = 1
    # in both files.  the second file set contains trajectory = 1 in the first
    # file and trajectory=2 in the second.  Test TDS aggregation.
    trajectory = nc.createVariable('trajectory',
                                   'i2',
                                   ('trajectory',),
                                   zlib=True,
                                   complevel=COMP_LEVEL)
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'cf_role' : 'trajectory_id',
            'long_name' : 'Unique identifier for each trajectory feature contained in the file',
            'comment' : 'A trajectory can span multiple data files each containing a single segment.',
    }
    for k in sorted(atts.keys()):
        trajectory.setncattr(k, atts[k])
    trajectory[:] = trajectorydata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # SEGMENT_ID
    # segment_id: 2 byte integer
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    segment_id = nc.createVariable('segment_id',
                                   'i2',
                                   dim_tuple,
                                   zlib=True,
                                   complevel=COMP_LEVEL,
                                   fill_value=NC_FILL_VALUES['i2'])
    atts = {'comment' : 'Sequential segment number within a trajectory/deployment. A segment corresponds to the set of data collected between 2 gps fixes obtained when the glider surfaces.',
            'long_name' : 'Segment ID',
            'valid_min' : 1,
            'valid_max' : 999,
            'observation_type' : 'calculated',
    }
    for k in sorted(atts.keys()):
        segment_id.setncattr(k, atts[k])
    segment_id[:] = segment_iddata
    # kerfoot@marine.rutgers.edu: Removed attributes: ancillary_variables, platform
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # PROFILE_ID
    # profile_id: 2 byte integer
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    profile_id = nc.createVariable('profile_id',
                                   'i2',
                                   dim_tuple,
                                   zlib=True,
                                   complevel=COMP_LEVEL,
                                   fill_value=NC_FILL_VALUES['i2'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'comment' : 'Sequential profile number within the current segment. A profile is defined as a single dive or climb', #  TODO: Revise definition'
            'long_name' : 'Profile ID',
            'valid_min' : 1,
            'valid_max' : 999,
            'observation_type' : 'calculated',
    }
    for k in sorted(atts.keys()):
        profile_id.setncattr(k, atts[k])
    profile_id[:] = profile_iddata
    # kerfoot@marine.rutgers.edu: Removed attributes: ancillary_variables, platform
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # DEPTH
    # depth: 64 bit float
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    depth = nc.createVariable('depth',
                              'f8',
                              dim_tuple,
                              zlib=True,
                              complevel=COMP_LEVEL,
                              fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'axis' : 'Z',
            'units' : 'meters',
            'standard_name' : 'depth',
            'valid_min' : 0,
            'valid_max' : 2000,
            'long_name' : 'Depth',
            'reference_datum' : 'sea-surface', # TODO: https://github.com/IOOSProfilingGliders/Real-Time-File-Format/issues/3
            'positive' : 'down', # Changed from vertical_positive to positive. http://cf-pcmdi.llnl.gov/documents/cf-conventions/1.6/cf-conventions.html#idp5784080
            'observation_type' : 'calculated',
            'ancillary_variables' : 'depth_qc',
            'platform' : 'platform',
            'instrument' : 'instrument_ctd',
            'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        depth.setncattr(k, atts[k])
    depth[:] = depthdata
    # kerfoot@marine.rutgers.edu: removed 'instrument_ctd' from # ancillary_variables
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # DEPTH_QC
    # depth_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    depth_qc = nc.createVariable('depth_qc',
                                 'i1',
                                 dim_tuple,
                                 zlib=True,
                                 complevel=COMP_LEVEL,
                                 fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'depth Quality Flag',
             'standard_name' : 'depth status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        depth_qc.setncattr(k, atts[k])
    if depth_qcdata != None:
        depth_qc[:] = depth_qcdata
    #depth_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # TODO: I don't think the ancillary_variable reference is intended to be bi-directional.
    # kerfoot@marine.rutgers.edu: removed 'ancillary_variable' attribute
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # LAT
    # lat: 64 bit float
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    lat = nc.createVariable('lat',
                            'f8',
                            dim_tuple,
                            zlib=True,
                            complevel=COMP_LEVEL,
                            fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'axis' : 'Y',
             'units' : 'degrees_north',
             'standard_name' : 'latitude',
             'long_name' : 'Latitude',
             'flag_meanings' : '',
             'valid_min' : -90.,
             'valid_max' : 90.,
             'observation_type' : 'measured',
             'ancillary_variables' : 'lat_qc',
             'platform' : 'platform',
             'comment' : 'Some values are linearly interpolated between measured coordinates.  See lat_qc', # kerfoot@marine.rutgers.edu: Should we interpolate missing values and add a comment ?  If so, what do do with 'observation_type' ?
             'sensor_name' : '',
             'reference' : 'WGS84', # GROOM manual, p16
             'coordinate_reference_frame' : 'urn:ogc:crs:EPSG::4326', # GROOM manual, p16
    }
    for k in sorted(atts.keys()):
        lat.setncattr(k, atts[k])
    lat[:] = latdata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # LAT_QC
    # lat_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    lat_qc = nc.createVariable('lat_qc',
                               'i1',
                               dim_tuple,
                               zlib=True,
                               complevel=COMP_LEVEL,
                               fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'lat Quality Flag',
             'standard_name' : 'lat status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        lat_qc.setncattr(k, atts[k])
    if lat_qcdata != None:
        lat_qc[:] = lat_qcdata
    #lat_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # LON
    # lon: 64 bit float
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    lon = nc.createVariable('lon',
                            'f8',
                            dim_tuple,
                            zlib=True,
                            complevel=COMP_LEVEL,
                            fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'axis' : 'X',
             'units' : 'degrees_east',
             'standard_name' : 'longitude',
             'long_name' : 'Longitude',
             'flag_meanings' : '',
             'valid_min' : -180.,
             'valid_max' : 180.,
             'observation_type' : 'measured',
             'ancillary_variables' : 'lon_qc',
             'platform' : 'platform',
             'comment' : 'Some values are linearly interpolated between measured coordinates.  See lon_qc', # kerfoot@marine.rutgers.edu: Should we interpolate missing values and add a comment ? If so, what to do with 'observation_type' ?
             'sensor_name' : '',
             'reference' : 'WGS84', # GROOM manual, p16
             'coordinate_reference_frame' : 'urn:ogc:crs:EPSG::4326', # GROOM manual, p16
    }
    for k in sorted(atts.keys()):
        lon.setncattr(k, atts[k])
    lon[:] = londata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # LON_QC
    # lon_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    lon_qc = nc.createVariable('lon_qc',
                               'i1',
                               dim_tuple,
                               zlib=True,
                               complevel=COMP_LEVEL,
                               fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'lon Quality Flag',
             'standard_name' : 'lon status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        lon_qc.setncattr(k, atts[k])
    if lon_qcdata != None:
        lon_qc[:] = lon_qcdata
    #lon_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # PRESSURE
    # pressure: 64 bit float
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    # 2013-07-30 kerfoot: added accuracy, resolution and precision attributes per
    # GROOM specification.
    pressure = nc.createVariable('pressure',
                                 'f8',
                                 dim_tuple,
                                 zlib=True,
                                 complevel=COMP_LEVEL,
                                 fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'axis' : 'Z',
            'units' : 'dbar',
            'standard_name' : 'pressure',
            'valid_min' : 0,
            'valid_max' : 2000,
            'long_name' : 'Pressure',
            'reference_datum' : 'sea-surface', 
            'positive' : 'down', 
            'observation_type' : 'calculated',
            'ancillary_variables' : 'pressure_qc',
            'platform' : 'platform',
            'instrument' : 'instrument_ctd',
            'accuracy' : '',
            'precision' : '',
            'resolution' : '',
            'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        pressure.setncattr(k, atts[k])
    pressure[:] = pressuredata
    # kerfoot@marine.rutgers.edu: removed 'instrument_ctd' from # ancillary_variables
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # PRESSURE_QC
    # pressure_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    pressure_qc = nc.createVariable('pressure_qc',
                                    'i1',
                                    dim_tuple,
                                    zlib=True,
                                    complevel=COMP_LEVEL,
                                    fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'pressure Quality Flag',
             'standard_name' : 'pressure status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        pressure_qc.setncattr(k, atts[k])
    if pressure_qcdata != None:
        pressure_qc[:] = pressure_qcdata
    #pressure_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # CONDUCTIVITY
    # 2013-07-30 kerfoot: added accuracy, resolution and precision attributes per
    # GROOM specification.
    # conductivity: 64 bit float
    conductivity = nc.createVariable('conductivity',
                                     'f8',
                                     dim_tuple,
                                     zlib=True,
                                     complevel=COMP_LEVEL,
                                     fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'units' : 'S m-1',
             'standard_name' : 'sea_water_electrical_conductivity',
             'valid_min' : 0.,
             'valid_max' : 10.,
             'long_name' : 'Conductivity',
             'observation_type' : 'measured',
             'ancillary_variables' : 'conductivity_qc',
             'platform' : 'platform',
             'instrument' : 'instrument_ctd',
             'coordinates' : 'lon lat depth time',
             'accuracy' : '',
             'precision' : '',
             'resolution' : '',
             'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        conductivity.setncattr(k, atts[k])
    conductivity[:] = conductivitydata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # CONDUCTIVITY_QC
    # conductivity_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    conductivity_qc = nc.createVariable('conductivity_qc',
                                        'i1',
                                        dim_tuple,
                                        zlib=True,
                                        complevel=COMP_LEVEL,
                                        fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'conductivity Quality Flag',
             'standard_name' : 'conductivity status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        conductivity_qc.setncattr(k, atts[k])
    if conductivity_qcdata != None:
        conductivity_qc[:] = conductivity_qcdata
    #conductivity_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # DENSITY
    # density: 64 bit float
    density = nc.createVariable('density',
                                'f8',
                                dim_tuple,
                                zlib=True,
                                complevel=COMP_LEVEL,
                                fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'units' : 'kg m-3',
             'standard_name' : 'sea_water_density',
             'valid_min' : 1015.,
             'valid_max' : 1040.,
             'long_name' : 'Density',
             'observation_type' : 'calculated',
             'ancillary_variables' : 'density_qc',
             'platform' : 'platform',
             'instrument' : 'instrument_ctd',
             'coordinates' : 'lon lat depth time',
             'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        density.setncattr(k, atts[k])
    density[:] = densitydata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # DENSITY_QC
    # density_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    density_qc = nc.createVariable('density_qc',
                                   'i1',
                                   dim_tuple,
                                   zlib=True,
                                   complevel=COMP_LEVEL,
                                   fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'density Quality Flag',
             'standard_name' : 'density status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        density_qc.setncattr(k, atts[k])
    if density_qcdata != None:
        density_qc[:] = density_qcdata
    #density_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # SALINITY
    # salinity: 64 bit float
    salinity = nc.createVariable('salinity',
                                 'f8',
                                 dim_tuple,
                                 zlib=True,
                                 complevel=COMP_LEVEL,
                                 fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'units' : '1e-3',
             'standard_name' : 'sea_water_salinity',
             'valid_min' : 0.,
             'valid_max' : 40.,
             'long_name' : 'Salinity',
             'observation_type' : 'calculated',
             'ancillary_variables' : 'salinity_qc',
             'platform' : 'platform',
             'instrument' : 'instrument_ctd',
             'coordinates' : 'lon lat depth time',
             'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        salinity.setncattr(k, atts[k])
    salinity[:] = salinitydata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # SALINITY_QC
    # salinity_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    salinity_qc = nc.createVariable('salinity_qc',
                                    'i1',
                                    dim_tuple,
                                    zlib=True,
                                    complevel=COMP_LEVEL,
                                    fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'salinity Quality Flag',
             'standard_name' : 'salinity status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        salinity_qc.setncattr(k, atts[k])
    if salinity_qcdata != None:
        salinity_qc[:] = salinity_qcdata
    #salinity_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # TEMPERATURE
    # 2013-07-30 kerfoot: added accuracy, resolution and precision attributes per
    # GROOM specification.
    # temperature: 64 bit float
    temperature = nc.createVariable('temperature',
                                    'f8',
                                    dim_tuple,
                                    zlib=True,
                                    complevel=COMP_LEVEL,
                                    fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'units' : 'Celsius',
             'standard_name' : 'sea_water_temperature',
             'valid_min' : -5.,
             'valid_max' : 40.,
             'long_name' : 'Temperature',
             'observation_type' : 'measured',
             'ancillary_variables' : 'temperature_qc',
             'platform' : 'platform',
             'instrument' : 'instrument_ctd',
             'coordinates' : 'lon lat depth time',
             'accuracy' : '',
             'precision' : '',
             'resolution' : '',
             'sensor_name' : '',
    }
    for k in sorted(atts.keys()):
        temperature.setncattr(k, atts[k])
    temperature[:] = temperaturedata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # TEMPERATURE_QC
    # temperature_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    temperature_qc = nc.createVariable('temperature_qc',
                                       'i1',
                                       dim_tuple,
                                       zlib=True,
                                       complevel=COMP_LEVEL,
                                       fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'temperature Quality Flag',
             'standard_name' : 'temperature status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        temperature_qc.setncattr(k, atts[k])
    if temperature_qcdata != None:
        temperature_qc[:] = temperature_qcdata
    #temperature_qc.flag_meanings = ""
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # LAT_UV
    # lat_uv: 64 bit float
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    lat_uv = nc.createVariable('lat_uv',
                               'f8',
                               uv_tuple,
                               zlib=True,
                               complevel=COMP_LEVEL,
                               fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'axis' : 'Y',
             'units' : 'degrees_north',
             'standard_name' : 'latitude',
             'long_name' : 'Center Latitude for Depth-Averaged Current',
             'valid_min' : -90.,
             'valid_max' : 90.,
             'observation_type' : 'calculated',
             'platform' : 'platform',
             'comment' : 'Values are interpolated to provide the center latitude of the segment',
    }
    for k in sorted(atts.keys()):
        lat_uv.setncattr(k, atts[k])
    lat_uv[:] = lat_uvdata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # LON_UV
    # lon_uv: 64 bit float
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    lon_uv = nc.createVariable('lon_uv',
                               'f8',
                               uv_tuple,
                               zlib=True,
                               complevel=COMP_LEVEL,
                               fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'axis' : 'X',
             'units' : 'degrees_east',
             'standard_name' : 'longitude',
             'long_name' : 'Center Longitude for Depth-Averaged Current',
             'valid_min' : -180.,
             'valid_max' : 180.,
             'observation_type' : 'calculated',
             'platform' : 'platform',
             'comment' : 'Values are interpolated to provide the center longitude of the segment',
    }
    for k in sorted(atts.keys()):
        lon_uv.setncattr(k, atts[k])
    lon_uv[:] = lon_uvdata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # U
    # u: 64 bit float
    u = nc.createVariable('u',
                          'f8',
                          uv_tuple,
                          zlib=True,
                          complevel=COMP_LEVEL,
                          fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'units' : 'm s-1',
            'standard_name' : 'eastward_sea_water_velocity',
            'valid_min' : -10.,
            'valid_max' : 10.,
            'long_name' : 'Eastward Sea Water Velocity',
            'observation_type' : 'calculated',
            'coordinates' : 'time_uv',
            'platform' : 'platform',
            'sensor_name' : '',
            'coordinates' : 'lon_uv lat_uv time_uv',
    }
    for k in sorted(atts.keys()):
        u.setncattr(k, atts[k])
    u[:] = udata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # U_QC
    # u_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    u_qc = nc.createVariable('u_qc',
                             'i1',
                             uv_tuple,
                             zlib=True,
                             complevel=COMP_LEVEL,
                             fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'u Quality Flag',
             'standard_name' : 'u status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        u_qc.setncattr(k, atts[k])
    if u_qcdata != None:
        u_qc[:] = u_qcdata
    #u_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # V
    # v: 64 bit float
    v = nc.createVariable('v',
                          'f8',
                          uv_tuple,
                          zlib=True,
                          complevel=COMP_LEVEL,
                          fill_value=NC_FILL_VALUES['f8'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'units' : 'm s-1',
            'standard_name' : 'northward_sea_water_velocity',
            'valid_min' : -10.,
            'valid_max' : 10.,
            'long_name' : 'Northward Sea Water Velocity',
            'observation_type' : 'calculated',
            'coordinates' : 'time_uv',
            'platform' : 'platform',
            'sensor_name' : '',
            'coordinates' : 'lon_uv lat_uv time_uv',
    }
    for k in sorted(atts.keys()):
        v.setncattr(k, atts[k])
    v[:] = vdata
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # V_QC
    # v_qc: 1 byte integer (ie: byte)
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    v_qc = nc.createVariable('v_qc',
                             'i1',
                             uv_tuple,
                             zlib=True,
                             complevel=COMP_LEVEL,
                             fill_value=NC_FILL_VALUES['i1'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'long_name' : 'v Quality Flag',
             'standard_name' : 'v status_flag',
             'flag_meanings' : QC_FLAG_MEANINGS,
             'valid_min' : QC_FLAGS[0],
             'valid_max' : QC_FLAGS[-1],
             'flag_values' : QC_FLAGS,
    }
    for k in sorted(atts.keys()):
        v_qc.setncattr(k, atts[k])
    if v_qcdata != None:
        v_qc[:] = v_qcdata
    #v_qc.flag_meanings = "" 
    # TODO: Choose QC Flag set for use in the representative case and inthe manual/wiki.  IODE flags? 
    # ----------------------------------------------------------------------------

    # Container Variables
    # ----------------------------------------------------------------------------
    # PLATFORM
    # platform: 1 byte integer, not dimensioned
    platform = nc.createVariable('platform',
                                 'i1');
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'type' : 'platform',
            'id' : 'ru29',
            'wmo_id' : 'ru29',
            'comment' : 'Slocum Glider ru29',
            'long_name' : 'Slocum Glider ru29',
            'instrument' : 'instrument_ctd',
    }
    for k in sorted(atts.keys()):
        platform.setncattr(k, atts[k])
    
    # ----------------------------------------------------------------------------

    # ----------------------------------------------------------------------------
    # INSTRUMENT
    # TODO: Determine the number of instrument variables needed.  https://github.com/IOOSProfilingGliders/Real-Time-File-Format/issues/4
    # 2013-07-30 kerfoot: moved accuracy, precision attributes to C,T and P
    # variables.  Deleted valid_range attribute.
    # instrument_ctd: 1 byte integer, not dimensioned
    instrument_ctd = nc.createVariable('instrument_ctd',
                                       'i1');
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = { 'serial_number' : '0098',
             'make_model' : 'Seabird SBE 41CP',
             'comment' : 'Slocum Glider ru29',
             'long_name' : 'Seabird SBD 41CP Conductivity, Temperature, Depth Sensor',
             'platform' : 'platform',
             'calibration_date' : '2000-01-01', # ISO 8601 date
             'factory_calibrated' : '',
             'user_calibrated' : '',
             'calibration_report' : '',
    }
    for k in sorted(atts.keys()):
        instrument_ctd.setncattr(k, atts[k])
    # ----------------------------------------------------------------------------

    nc.close()

def get_time_coverage(nc, stride):
    a, b, tname = None, None, None
    if "ocean_time" in nc.variables:
        tname = "ocean_time"
    if "time" in nc.variables:
        tname = "time"
    if tname != None:
        a = num2date(nc.variables[tname][::stride][0], units=nc.variables[tname].units).strftime('%Y-%m-%d %H:%M UTC')
        b = num2date(nc.variables[tname][::stride][-1], units=nc.variables[tname].units).strftime('%Y-%m-%d %H:%M UTC')
    return a, b

def get_stride(nc):
    if nc.variables["lon"].shape[0] > 1000:
        stride = 200
    else:
        stride = 1
    return stride

@app.route("/")
def index():
    response = \
'''
Here is what you do!!
'''
    return response

@app.route("/geojson-line/<path:dap>")
def geojson_line(dap):
    return geojson(dap)

@app.route("/geojson/<path:dap>")
def geojson(dap):
    callback = request.args.get('callback', None)
    response = "Problem"
    with Dataset(dap) as nc:
        stride = get_stride(nc)
        if len(nc.variables["lon"].shape) == 2:
            f = []
            for i in xrange(nc.variables["lon"].shape[1]):
                lon = nc.variables["lon"][::stride,i].flatten()
		mask = lon.mask == False
		lon = lon.data.astype(np.float64)
                lat = nc.variables["lat"][::stride,i].flatten().data.astype(np.float64)
                subbool = lon[mask]<1000
		coords = zip(lon[mask][subbool], lat[mask][subbool])
		#print coords
		#coords[0], coords[1] = coords[0][coords[0]<-.01], coords[1][coords[1]>.01]
                #coords = zip(np.ones((100,)), np.ones((100,)))
                n = gj.LineString( coords )
                s = getncattrs(nc)
                if (not "time_coverage_start" in s) or (not "time_coverage_end" in s):
                    s["time_coverage_start"], s["time_coverage_end"] = get_time_coverage(nc, stride)
                if "trajectory" in nc.variables:
                    f.append( gj.Feature(id=nc.variables["trajectory"][i], geometry=n, properties=s) )
                else:
                    f.append( gj.Feature(id=i, geometry=n, properties=s) )
            f = gj.FeatureCollection(f)
        else:
            lon = nc.variables["lon"][::stride].flatten().data.astype(np.float64)
            lat = nc.variables["lat"][::stride].flatten().data.astype(np.float64)
            coords = zip(lon[lon<1000], lat[lat<1000])
            #coords = zip(np.ones((100,)), np.ones((100,)))
            n = gj.LineString( coords )
            s = getncattrs(nc)
            if (not "time_coverage_start" in s) or (not "time_coverage_end" in s):
                s["time_coverage_start"], s["time_coverage_end"] = get_time_coverage(nc, stride)
            f = gj.Feature(id=s.get("id", None), geometry=n, properties=s)
        response = gj.dumps(f)
        if callback != None:
            response = callback + "(" + response + ")"
    return Response(response, mimetype='application/json')

if __name__ == '__main__':
    app.run()
    #app.run('0.0.0.0')
