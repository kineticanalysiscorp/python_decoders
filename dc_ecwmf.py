import sys
import os
import numpy as np
from eccodes import *
from datetime import datetime
import math

# Constants
MAX_STRSIZE = 200
NM2M = 1852.0  # Nautical miles to meters
MS2KTS = 1.94384  # m/s to knots conversion
CODES_MISSING_DOUBLE = 1.0e100
CODES_MISSING_LONG = 2147483647


# Path to your ECMWF BUFR tropical cyclone file
#bufr_file = "20240701120000-240h-oper-tf.bufr"


class ForecastTrack:
    def __init__(self):
        self.basin = 'XX'
        self.cyNum = 0
        self.DTG = ''
        self.jdnow = 0.0
        self.technum = 0
        self.tech = ''
        self.stormname = ''
        self.track = [{'tau': 0, 'lat': -999, 'lon': -999, 'mslp': -999, 'vmax': -999, 'mrd': -999, 'ty': '  '} for _ in range(36)]
        for j in range(36):
            self.track[j]['windrad'] = [{'code': 'AAA'} for _ in range(4)]

class ATCFDecoder:
    def __init__(self):
        self.num_fcst = 0
        self.fcst = []
        self.UnitAT = 10  # Arbitrary file unit number
        
    def clear_internal_atcf(self):
        """Reset the internal ATCF storage"""
        self.num_fcst = 0
        self.fcst = []
        
    def djuliana(self, month, day, year, hour):
        """Convert date to Julian day"""
        if month <= 2:
            year -= 1
            month += 12
        A = int(year / 100)
        B = 2 - A + int(A / 4)
        jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
        jd += hour / 24.0
        return jd
        
    def gcdist(self, lat1, lon1, lat2, lon2):
        """Calculate great circle distance between two points"""
        if lat1 == lat2 and lon1 == lon2:
            return 0.0, 0.0
        
        rad = math.pi / 180.0
        dlat = (lat2 - lat1) * rad
        dlon = (lon2 - lon1) * rad
        a = math.sin(dlat/2)**2 + math.cos(lat1*rad) * math.cos(lat2*rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = 6371.0 * c * 1000.0  # Distance in meters
        
        y = math.sin(dlon) * math.cos(lat2*rad)
        x = math.cos(lat1*rad)*math.sin(lat2*rad) - math.sin(lat1*rad)*math.cos(lat2*rad)*math.cos(dlon)
        angle = math.atan2(y, x) * (180.0/math.pi)
        angle = (angle + 360.0) % 360.0
        
        return dist, angle
        
    def match_atcf_id(self, fix_lat, fix_lon, yy, mm, dd, hh, inum, bchar):
        """Match storm with ATCF ID (simplified for Python)"""
        atcfid = 'XX999999'
        found = False
        
        # Ensure fix_lat and fix_lon are valid
        if abs(fix_lat) <= 90 and abs(fix_lon) <= 360:
            basin = 'XX'
            if bchar == 'L': basin = 'AL'
            if bchar == 'E': basin = 'EP'
            if bchar == 'W': basin = 'WP'
            if bchar == 'S': basin = 'SH'
            atcfid = f"{basin}{inum:02d}{yy:04d}"  # Use storm number and year from stormIdentifier
            found = True
        else:
            print(f"Invalid fix_lat ({fix_lat}) or fix_lon ({fix_lon}). Cannot generate ATCF ID.")

        # Debug: Log the generated ATCF ID and found status
        print(f"Generated ATCFID: {atcfid}, Found: {found}")

        return atcfid, found
        
    def get_atcf_records(self, atfile, tech_filter):
        """Read existing ATCF records (simplified for Python)"""
        # In the original Fortran, this would read an ATCF file
        # For Python, we'll just initialize an empty list
        pass
        
    def sort_fcst_records(self):
        """Sort forecast records (simplified for Python)"""
        # In the original Fortran, this would sort the forecasts
        pass
        
    def write_fcst_record(self, idx, atfile, infile):
        """Write forecast record to ATCF file, skipping lines with missing data (-999) or placeholder values (1e100, -1e100)"""
        fcst = self.fcst[idx]
        """Read the initial storm center from a BUFR file."""
        with open(infile, "rb") as f:
            # Read the first BUFR message
            bufr = codes_bufr_new_from_file(f)

            # Tell ecCodes to expand descriptors to get all data
            codes_set(bufr, "unpack", 1)

            # Extract storm center info (subset 1 = initial analysis)
            lat = codes_get_array(bufr, "latitude")[0]
            lon = codes_get_array(bufr, "longitude")[0]
            print(lat)
            print(lon)
            vmax = codes_get_array(bufr, "windSpeedAt10M")[0] * MS2KTS
            mslp = codes_get_array(bufr, "pressureReducedToMeanSeaLevel")[0] / 100

            storm_name = codes_get(bufr, "longStormName")  # Extract storm name
            print(f"Storm Name: {storm_name}")
            fcst.stormname = storm_name.strip()  # Assign storm name to ForecastTrack

            # Get date/time fields
            year = codes_get(bufr, "year")
            month = codes_get(bufr, "month")
            day = codes_get(bufr, "day")
            hour = codes_get(bufr, "hour")

            print("=== Initial Storm Center ===")
            print(f"Valid Time: {year}-{month:02d}-{day:02d} {hour:02d}:00 UTC")
            print(f"Latitude: {lat:.2f}")
            print(f"Longitude: {lon:.2f}")
            print(f"Max Sustained Wind (m/s): {vmax}")
            print(f"Central Pressure (hPa): {mslp}")

            f.close()

        with open(atfile, 'a') as f:
            # Format and write the record
            lat = f"{int(abs(lat) * 10):03d}{'N' if lat >= 0 else 'S'}"
            lon = f"{int(abs(lon) * 10):03d}{'E' if lon >= 0 else 'W'}"
            vmax = str(int(vmax))
            mslp = f"{int(mslp):4d}"  # Ensure mslp is 4 characters wide
            #mrd = f"{int(mrd):2d}"  # Ensure mrd is 2 characters wide
            tau = f"{int(0):3d}"  # Format tau as a 3-character wide field

            line = (f"{fcst.basin},  {int(fcst.cyNum)}, {fcst.DTG},  1, OFCL, "
                    f"{tau}, {lat},  {lon},  "
                    f"{vmax}, {mslp},    ,  , , ,  , , , , ,   , , , , , , {fcst.stormname}")
            f.write(line + '\n') 

            for j in range(36):  # Iterate over all 36 forecast periods
                track = fcst.track[j]
                
                # Skip records with missing or placeholder data
                if (track['lat'] == -999 or 
                    track['lon'] == -999 or 
                    track['vmax'] == -999 or 
                    track['mslp'] == -999 or 
                    abs(track['lat']) == 1e100 or 
                    abs(track['lon']) == 1e100):
                    continue
                
                # Format and write the record
                lat = f"{int(abs(track['lat']) * 10):03d}{'N' if track['lat'] >= 0 else 'S'}"
                lon = f"{int(abs(track['lon']) * 10):03d}{'E' if track['lon'] >= 0 else 'W'}"
                vmax = str(int(track['vmax']))
                mslp = f"{int(track['mslp']):4d}"  # Ensure mslp is 4 characters wide
                mrd = f"{int(track['mrd']):2d}"  # Ensure mrd is 2 characters wide
                tau = f"{int(track['tau']):3d}"  # Format tau as a 3-character wide field

                line =  (f"{fcst.basin},  {int(fcst.cyNum)}, {fcst.DTG},  1, OFCL, "
                        f"{tau}, {lat},  {lon},  "
                        f"{vmax}, {mslp}, "
                        f"   ,  , , ,  , , , , , {mrd}, , , , , , {fcst.stormname}")
                f.write(line + '\n')
    
    def decode_ecmf_bufr(self, infile, doform=False, source='ECMF'):
        """Main decoding function"""
        print("\nECMF BUFR4 format to ATCF")
        print("Copyright(c) 2020 Enki Holdings, LLC")
        print("All Rights Reserved\n")
        
        basin = 'XX'
        atcfid = 'XX999999'
        atfile = 'badfile.dat'
        
        # Check if input file exists
        if not os.path.exists(infile):
            print(f"*Error* {infile} does not exist!")
            return
            
        print(f"Reading {infile}")
        
        # Open BUFR file
        try:
            with open(infile, 'rb') as f:
                count = 1
                while True:
                    ibufr = None  # Initialize ibufr to ensure it is defined
                    try:
                        print('executing')
                        # Get next BUFR message
                        ibufr = codes_bufr_new_from_file(f)
                        if (ibufr is None):
                            break
                        
                        # Process the BUFR message
                        self.clear_internal_atcf()
                        fix_lat = -999
                        fix_lon = -999
                        
                        # Unpack the BUFR message
                        codes_set(ibufr, 'unpack', 1)

                        # Initialize rank positions
                        rankSignificance = 3
                        rankPosition = 3
                        rankPressure = 1
                        rankWind = 1

                        # Determine number of time periods
                        numberOfPeriods = 0
                        while True:
                            numberOfPeriods += 1
                            rankPeriodStr = str(numberOfPeriods)
                            try:
                                period_value = codes_get(ibufr, f'#{rankPeriodStr}#timePeriod')
                            except CodesInternalError:
                                print(f"Error accessing timePeriod for rank {rankPeriodStr}.")
                                break

                        print('initializing arrays')

                        # Initialize arrays for forecast fields
                        latitude = np.full((1, numberOfPeriods), CODES_MISSING_DOUBLE)
                        longitude = np.full((1, numberOfPeriods), CODES_MISSING_DOUBLE)
                        pressure = np.full((1, numberOfPeriods), CODES_MISSING_DOUBLE)
                        latitudeWind = np.full((1, numberOfPeriods), CODES_MISSING_DOUBLE)
                        longitudeWind = np.full((1, numberOfPeriods), CODES_MISSING_DOUBLE)
                        wind = np.full((1, numberOfPeriods), CODES_MISSING_DOUBLE)
                        period = [-1] * numberOfPeriods  # Default to -1 for uninitialized periods

                        # Process forecast periods
                        for i in range(0, numberOfPeriods):
                            rankPeriod = i
                            rankPeriodStr = str(rankPeriod)
                            
                            # Debug: Log rankPeriod
                            print(f"Processing rankPeriod: {rankPeriod}")

                            # Get time period
                            try:
                                ivalues = codes_get(ibufr, f'#{rankPeriodStr}#timePeriod')
                                if not isinstance(ivalues, list):
                                    ivalues = [ivalues]  # Ensure ivalues is a list
                                for k in range(len(ivalues)):
                                    if ivalues[k] != CODES_MISSING_LONG:
                                        period[i] = ivalues[k]  # Assign value to the list
                            except CodesInternalError as e:
                                print(f"Error accessing timePeriod for rank {rankPeriodStr}: {e}")
                                continue

                            # Extract storm location significance
                            rankSignificance += 1
                            rankSignificanceStr = str(rankSignificance)
                            try:
                                ivalues = codes_get(ibufr, f'#{rankSignificanceStr}#meteorologicalAttributeSignificance')
                                if not isinstance(ivalues, list):
                                    ivalues = [ivalues]  # Ensure ivalues is a list
                                for k in range(len(ivalues)):
                                    if ivalues[k] != CODES_MISSING_LONG:
                                        significance = ivalues[k]
                                        # Debug: Log the extracted significance value
                                        print(f"Extracted significance for rankSignificance={rankSignificance}: {significance}")
                            except CodesInternalError as e:
                                print(f"Error accessing meteorologicalAttributeSignificance for rank {rankSignificanceStr}: {e}")
                                significance = None

                            # Handle significance values
                            if significance == 1:
                                # Process storm center significance
                                rankPosition += 1
                                rankPositionStr = str(rankPosition)
                                latitude[0, i] = codes_get(ibufr, f'#{rankPositionStr}#latitude')
                                longitude[0, i] = codes_get(ibufr, f'#{rankPositionStr}#longitude')

                                # Debug: Log extracted latitude and longitude
                                print(f"Extracted storm center for period {i}: latitude={latitude[0, i]}, longitude={longitude[0, i]}")

                                rankPressure += 1
                                rankPressureStr = str(rankPressure)
                                pressure[0, i] = codes_get(ibufr, f'#{rankPressureStr}#pressureReducedToMeanSeaLevel')

                                if pressure[0, i] is None or pressure[0, i] == CODES_MISSING_DOUBLE:
                                    print("Central pressure data is missing. Assigning default value.")
                                    pressure[0, i] = -999  # Default value for missing data

                                print(f"Extracted pressure for period {i}: pressure={pressure[0, i]}")
                            elif significance == 3:
                                # Process maximum wind significance
                                rankPosition += 1
                                rankPositionStr = str(rankPosition)
                                latitudeWind[0, i] = codes_get(ibufr, f'#{rankPositionStr}#latitude')
                                longitudeWind[0, i] = codes_get(ibufr, f'#{rankPositionStr}#longitude')

                                # Debug: Log extracted latitudeWind and longitudeWind
                                print(f"Extracted max wind for period {i}: latitudeWind={latitudeWind[0, i]}, longitudeWind={longitudeWind[0, i]}")

                                rankWind += 1
                                rankWindStr = str(rankWind)
                                wind[0, i] = codes_get(ibufr, f'#{rankWindStr}#windSpeedAt10M')
                                print(f"Extracted wind for period {i}: windSpeed={wind[0, i]}")
                            else:
                                print(f"WARNING: unexpected meteorologicalAttributeSignificance={significance} for period {i}. Skipping this forecast period.")
                                continue

                        # Check if the BUFR message contains valid data for the main operational run
                        if not codes_is_defined(ibufr, 'ensembleForecastType'):
                            print("checking for valid data")
                            continue

                        # Get the forecast type and ensure it is the main operational run
                        try:
                            forecastType = codes_get(ibufr, 'ensembleForecastType')
                            print(forecastType)
                            if forecastType != 0:  # 0 indicates the main operational run
                                continue
                        except CodesInternalError:
                            continue

                        # Extract basic storm information
                        try:
                            year = codes_get(ibufr, 'year')
                            month = codes_get(ibufr, 'month')
                            day = codes_get(ibufr, 'day')
                            hour = codes_get(ibufr, 'hour')
                            minute = codes_get(ibufr, 'minute')
                            stormIdentifier = codes_get(ibufr, 'stormIdentifier')
                        except CodesInternalError as e:
                            print(f"Error extracting storm information: {e}")
                            return

                        # Extract storm number (inum) and basin character (bchar) from stormIdentifier
                        try:
                            inum = int(stormIdentifier[:2])  # Extract the storm number
                            bchar = stormIdentifier[2]       # Extract the basin character
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing stormIdentifier '{stormIdentifier}': {e}")
                            inum = -1  # Assign a default value or handle the error appropriately
                            bchar = 'X'

                        # Debug: Log extracted storm information
                        print(f"Extracted storm information: year={year}, month={month}, day={day}, hour={hour}, "
                              f"inum={inum}, bchar={bchar}, stormIdentifier={stormIdentifier}")

                        # Ensure these variables are defined before use
                        if year is None or month is None or day is None or hour is None or inum == -1:
                            print("Error: Missing or invalid storm information in BUFR message.")
                            return

                        # Correct ATCFID generation based on stormIdentifier
                        atcfid, found = self.match_atcf_id(fix_lat, fix_lon, year, month, day, hour, inum, bchar)

                        # Debug: Log the result of match_atcf_id
                        print(f"ATCFID: {atcfid}, Found: {found}")

                        if not found:
                            if not doform:
                                print("ATCF ID not found and doform is False. Skipping this message.")
                            basin = 'XX'
                            if bchar == 'L': basin = 'AL'
                            if bchar == 'E': basin = 'EP'
                            if bchar == 'W': basin = 'WP'
                            if bchar == 'S': basin = 'SH'
                            atcfid = f"{basin}{inum:02d}{year:04d}"  # Correctly use storm number and year
                            print(atcfid)
                        
                        basin = atcfid[:2]
                        
                        # Extract storm number (snum) from ATCF ID
                        try:
                            snum = int(atcfid[2:4])  # Extract storm number from ATCF ID
                        except ValueError:
                            print(f"Error extracting storm number from ATCFID: {atcfid}")
                            snum = -1  # Assign a default value or handle the error appropriately

                        # Debug: Log the extracted storm number
                        print(f"Storm number (snum): {snum}")

                        if basin == 'XX' and not doform:
                            continue
                            
                        atfile = f"A{atcfid}.DAT"

                        # Ensure snum is extracted again if atcfid is updated
                        if atcfid != 'XX999999':
                            try:
                                snum = int(atcfid[2:4])  # Extract storm number from updated ATCF ID
                            except ValueError:
                                print(f"Error extracting storm number from updated ATCFID: {atcfid}")
                                snum = -1  # Assign a default value or handle the error appropriately

                        # Debug: Log the extracted storm number after update
                        print(f"Updated storm number (snum): {snum}")

                        skipMember = 1
                        for j in range(len(period)):
                            if (latitude[0, j] != CODES_MISSING_DOUBLE or 
                                latitudeWind[0, j] != CODES_MISSING_DOUBLE):
                                skipMember = 0
                                break
                        
                        if skipMember != 1:
                            mytech = 'ECM '  # Main operational run identifier

                            # Create new forecast record
                            new_fcst = ForecastTrack()
                            new_fcst.basin = basin
                            new_fcst.cyNum = snum
                            new_fcst.DTG = f"{year:04d}{month:02d}{day:02d}{hour:02d}"
                            new_fcst.jdnow = 0
                            new_fcst.technum = 3
                            new_fcst.tech = mytech
                            new_fcst.stormname = ''

                            jnow = 0
                            for j in range(len(period)):  # Iterate over all periods, including tau = 0
                                if j == 0:  # Handle the analysis period (tau = 0)
                                    if latitude[0, j] != CODES_MISSING_DOUBLE and longitude[0, j] != CODES_MISSING_DOUBLE:
                                        # Process initial storm center data
                                        print(f"Processing initial storm center (tau = 0): latitude={latitude[0, j]}, longitude={longitude[0, j]}")
                                        print(aaa)
                                        fcst_lat = latitude[0, j]
                                        fcst_lon = longitude[0, j]
                                        fcst_mslp = pressure[0, j] / 100.0  # Convert pressure to hPa
                                        fcst_vmax = -999  # No max wind data for tau = 0
                                        fcst_mrd = -999  # No radius of max wind for tau = 0
                                    else:
                                        # Skip if initial storm center data is missing
                                        print("Skipping initial storm center (tau = 0) due to missing data.")
                                        continue
                                else:
                                    # Handle forecast periods (tau > 0)
                                    if latitude[0, j] != CODES_MISSING_DOUBLE and longitude[0, j] != CODES_MISSING_DOUBLE:
                                        # Process storm center data
                                        print(f"Processing storm center for period {j}: latitude={latitude[0, j]}, longitude={longitude[0, j]}")
                                        fcst_lat = latitude[0, j]
                                        fcst_lon = longitude[0, j]
                                        fcst_mslp = pressure[0, j] / 100.0  # Convert pressure to hPa
                                    else:
                                        # Skip if storm center data is missing
                                        print(f"Skipping period {j} due to missing storm center data.")
                                        continue

                                    # Check if the next period (even period) has max wind data
                                    if j + 1 < len(period) and latitudeWind[0, j + 1] != CODES_MISSING_DOUBLE and longitudeWind[0, j + 1] != CODES_MISSING_DOUBLE:
                                        # Process max wind data
                                        print(f"Processing max wind for period {j + 1}: latitudeWind={latitudeWind[0, j + 1]}, longitudeWind={longitudeWind[0, j + 1]}")
                                        fcst_vmax = wind[0, j + 1] * MS2KTS  # Convert wind speed to knots
                                        dist, angle = self.gcdist(
                                            latitude[0, j], longitude[0, j],
                                            latitudeWind[0, j + 1], longitudeWind[0, j + 1]
                                        )
                                        fcst_mrd = dist / NM2M  # Convert distance to nautical miles
                                        if fcst_mrd > 70:
                                            fcst_mrd = 70.0  # Limit to prevent superstorms
                                    else:
                                        # Default values if max wind data is missing
                                        print(f"Skipping period {j + 1} due to missing max wind data.")
                                        fcst_vmax = -999
                                        fcst_mrd = -999

                                # Increment track index
                                jnow += 1

                                # Store track data
                                new_fcst.track[jnow]['tau'] = period[j]
                                new_fcst.track[jnow]['lat'] = fcst_lat
                                new_fcst.track[jnow]['lon'] = fcst_lon
                                new_fcst.track[jnow]['mslp'] = fcst_mslp
                                new_fcst.track[jnow]['vmax'] = fcst_vmax
                                new_fcst.track[jnow]['mrd'] = fcst_mrd

                                print(f"Saved track data for period {j}: tau={period[j]}, lat={fcst_lat}, lon={fcst_lon}, "
                                      f"mslp={fcst_mslp}, vmax={fcst_vmax}, mrd={fcst_mrd}")

                            # Append the forecast record
                            self.fcst.append(new_fcst)
                            self.num_fcst += 1
                        else:
                            continue
                        
                        # Debug: Log the number of forecast records before writing to ATCF file
                        print(f"Total forecast records: {self.num_fcst}")
                        print(new_fcst)

                        # Write output to ATCF file
                        if self.num_fcst > 0:
                            print(f"Number of forecast records: {self.num_fcst}")  # Debug statement
                            print(f"ATCF file name: {atfile}")  # Debug statement
                            with open(atfile, 'w') as f:
                                self.sort_fcst_records()
                                for i in range(self.num_fcst):
                                    self.write_fcst_record(i, atfile, infile)  # Pass atfile as an argument
                            print(f"Wrote {self.num_fcst} forecasts to {atfile}.")
                        else:
                            print("No forecast records generated. Skipping ATCF file creation.")
                            print("Check if forecast data is valid and being appended to self.fcst.")
                    except CodesInternalError as e:
                        continue
                    except ValueError as e:
                        break
                    finally:
                        # Ensure BUFR message is released
                        if ibufr is not None:
                            codes_release(ibufr)
                    count += 1
        except OSError as e:
            print(f"File operation error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        print("end of mashed up code")

def main():
    if len(sys.argv) < 2:
        print("Usage: python dc_ecmf.py -in <input_file> [-source <source>] [-doform]")        
        return
        
    # Parse command line arguments
    infile = ''
    source = 'ECMF'
    doform = False
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-in":
            i += 1
            infile = sys.argv[i]
        elif sys.argv[i] == "-source":
            i += 1
            source = sys.argv[i]
        elif sys.argv[i] == "-doform":
            doform = True
        i += 1

    decoder = ATCFDecoder()
    decoder.decode_ecmf_bufr(infile, doform, source)

if __name__ == "__main__":
    main()
