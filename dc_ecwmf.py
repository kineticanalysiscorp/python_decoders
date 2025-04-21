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
        
    def match_atcf_id(self, fix_lat, fix_lon, yy, mm, dd, hh):
        """Match storm with ATCF ID (simplified for Python)"""
        # In the original Fortran, this would read tcvitals data
        # For Python, we'll return a dummy value
        atcfid = 'XX999999'
        found = False
        
        # Simple logic to create an ATCF ID based on position and date
        if abs(fix_lat) <= 90 and abs(fix_lon) <= 360:
            basin = 'XX'
            if fix_lon < 100 or fix_lon > 180:  # Very simplified basin detection
                basin = 'AL'
            atcfid = f"{basin}{yy%100:02d}{yy:04d}"
            found = True
            
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
        
    def write_fcst_record(self, idx):
        """Write forecast record to ATCF file (simplified for Python)"""
        fcst = self.fcst[idx]
        with open(atfile, 'a') as f:
            for j in range(36):
                track = fcst.track[j]
                if track['lat'] != -999:
                    line = (f"{fcst.basin}, {fcst.cyNum:02d}, {fcst.DTG}, "
                            f"{track['tau']:03d}, {track['lat']:05.1f}{'N' if track['lat'] >= 0 else 'S'}, "
                            f"{track['lon']:06.1f}{'E' if track['lon'] >= 0 else 'W'}, "
                            f"{track['vmax']:03d}, {track['mslp']:04d}, "
                            f"{fcst.tech}, {fcst.technum:02d}, {fcst.stormname}, "
                            f"{track['mrd']:03d}")
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
        with open(infile, 'rb') as f:
            count = 1
            while True:
                # Get next BUFR message
                ibufr = codes_bufr_new_from_file(f)
                if ibufr is None:
                    break
                    
                print(f"**************** MESSAGE: {count} *****************")
                self.clear_internal_atcf()
                fix_lat = -999
                fix_lon = -999
                
                # Unpack the BUFR message
                codes_set(ibufr, 'unpack', 1)
                
                # Get basic storm information
                year = codes_get(ibufr, 'year')
                month = codes_get(ibufr, 'month')
                day = codes_get(ibufr, 'day')
                hour = codes_get(ibufr, 'hour')
                minute = codes_get(ibufr, 'minute')
                
                stormIdentifier = codes_get(ibufr, 'stormIdentifier')
                inum = int(stormIdentifier[:2])
                bchar = stormIdentifier[2]
                
                jdmsg = self.djuliana(month, day, year, hour)
                
                longStormName = codes_get(ibufr, 'longStormName')
                sname = longStormName.split()[0]
                
                # Determine number of time periods
                numberOfPeriods = 0
                while True:
                    numberOfPeriods += 1
                    rankPeriodStr = str(numberOfPeriods)
                    try:
                        period = codes_get(ibufr, f'#{rankPeriodStr}#timePeriod')
                    except CodesInternalError:
                        break
                        
                # Get ensemble member numbers
                memberNumber = codes_get(ibufr, 'ensembleMemberNumber')
                d1 = len(memberNumber)
                
                # Initialize arrays
                latitude = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                longitude = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                pressure = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                latitudeWind = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                longitudeWind = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                wind = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                RadMaxWind = np.full((d1, numberOfPeriods), CODES_MISSING_DOUBLE)
                period = np.zeros(numberOfPeriods, dtype=int)
                
                # Get ensemble forecast types
                etypearray = codes_get(ibufr, 'ensembleForecastType')
                
                # Analysis period is 0
                period[0] = 0
                
                # Get observed storm center
                significance = codes_get(ibufr, '#1#meteorologicalAttributeSignificance')
                latitudeCentre = codes_get(ibufr, '#1#latitude')
                longitudeCentre = codes_get(ibufr, '#1#longitude')
                
                if significance != 1:
                    print("ERROR: unexpected #1#meteorologicalAttributeSignificance")
                    return
                    
                if (latitudeCentre == CODES_MISSING_DOUBLE and 
                    longitudeCentre == CODES_MISSING_DOUBLE):
                    print("Observed storm centre position missing")
                else:
                    print(f"Observed storm centre: latitude={latitudeCentre:.2f} longitude={longitudeCentre:.2f}")
                
                # Get perturbed analysis positions
                sigarray = codes_get(ibufr, '#2#meteorologicalAttributeSignificance')
                latitudeAnalysis = codes_get(ibufr, '#2#latitude')
                longitudeAnalysis = codes_get(ibufr, '#2#longitude')
                pressureAnalysis = codes_get(ibufr, '#1#pressureReducedToMeanSeaLevel')
                
                # Get location of maximum wind
                significance = codes_get(ibufr, '#3#meteorologicalAttributeSignificance')
                latitudeMaxWind0 = codes_get(ibufr, '#3#latitude')
                longitudeMaxWind0 = codes_get(ibufr, '#3#longitude')
                
                if significance != 3:
                    print(f"ERROR: unexpected #3#meteorologicalAttributeSignificance={significance}")
                    return
                    
                windMaxWind0 = codes_get(ibufr, '#1#windSpeedAt10M')
                
                # Fill arrays with analysis data
                if len(latitudeMaxWind0) == len(memberNumber):
                    latitudeWind[:, 0] = latitudeMaxWind0
                    longitudeWind[:, 0] = longitudeMaxWind0
                    wind[:, 0] = windMaxWind0
                else:
                    latitudeWind[:, 0] = latitudeMaxWind0[0]
                    longitudeWind[:, 0] = longitudeMaxWind0[0]
                    wind[:, 0] = windMaxWind0[0]
                
                # Determine ATCF ID
                fix_lat = latitudeCentre
                fix_lon = longitudeCentre
                
                if abs(fix_lat) > 90:
                    for i in range(len(latitudeAnalysis)):
                        if abs(latitudeAnalysis[i]) < 90:
                            fix_lat = latitudeAnalysis[i]
                            fix_lon = longitudeAnalysis[i]
                            break
                    if abs(fix_lat) > 90:
                        continue
                        
                print(f"Checking cross references for ATCF ID... {inum}{bchar}  {sname}")
                print(f"{fix_lat} {fix_lon} {year} {month} {day} {hour}")
                
                atcfid, found = self.match_atcf_id(fix_lat, fix_lon, year, month, day, hour)
                
                if not found:
                    if not doform:
                        continue
                    basin = 'XX'
                    if bchar == 'L': basin = 'AL'
                    if bchar == 'E': basin = 'EP'
                    if bchar == 'W': basin = 'WP'
                    if bchar == 'S': basin = 'SH'
                    atcfid = f"{basin}{inum:02d}{year:04d}"
                
                print(f"ATCFID: {atcfid}")
                basin = atcfid[:2]
                snum = int(atcfid[2:4])
                
                if basin == 'XX' and not doform:
                    continue
                    
                atfile = f"A{atcfid}.DAT"
                
                self.clear_internal_atcf()
                self.get_atcf_records(atfile, 'ANY ')
                
                jdmsg = self.djuliana(month, day, year, hour)
                found = False
                
                for i in range(self.num_fcst):
                    if (self.fcst[i].tech == 'ECMF' and 
                        abs(self.fcst[i].jdnow - jdmsg) < 1.0/24):
                        found = True
                        
                if found:
                    print("Forecast already in ATCF file")
                    continue
                
                # Process forecast periods
                for i in range(1, numberOfPeriods):
                    rankPeriod = i
                    rankPeriodStr = str(rankPeriod)
                    
                    # Get time period
                    ivalues = codes_get(ibufr, f'#{rankPeriodStr}#timePeriod')
                    for k in range(len(ivalues)):
                        if ivalues[k] != CODES_MISSING_LONG:
                            period[i] = ivalues[k]
                    
                    # Get storm location significance
                    rankSignificance = 3 + (i-1)*2
                    rankSignificanceStr = str(rankSignificance)
                    ivalues = codes_get(ibufr, f'#{rankSignificanceStr}#meteorologicalAttributeSignificance')
                    for k in range(len(ivalues)):
                        if ivalues[k] != CODES_MISSING_LONG:
                            significance = ivalues[k]
                    
                    # Get storm position
                    rankPosition = 3 + (i-1)*2
                    rankPositionStr = str(rankPosition)
                    values = codes_get(ibufr, f'#{rankPositionStr}#latitude')
                    latitude[:, i] = values
                    values = codes_get(ibufr, f'#{rankPositionStr}#longitude')
                    longitude[:, i] = values
                    
                    if significance == 1:
                        rankPressure = 1 + (i-1)
                        rankPressureStr = str(rankPressure)
                        values = codes_get(ibufr, f'#{rankPressureStr}#pressureReducedToMeanSeaLevel')
                        pressure[:, i] = values
                    else:
                        print(f"ERROR: unexpected meteorologicalAttributeSignificance={significance}")
                        return
                    
                    # Get maximum wind significance
                    rankSignificance += 1
                    rankSignificanceStr = str(rankSignificance)
                    ivalues = codes_get(ibufr, f'#{rankSignificanceStr}#meteorologicalAttributeSignificance')
                    for k in range(len(ivalues)):
                        if ivalues[k] != CODES_MISSING_LONG:
                            significance = ivalues[k]
                    
                    # Get maximum wind position
                    rankPosition += 1
                    rankPositionStr = str(rankPosition)
                    values = codes_get(ibufr, f'#{rankPositionStr}#latitude')
                    latitudeWind[:, i] = values
                    values = codes_get(ibufr, f'#{rankPositionStr}#longitude')
                    longitudeWind[:, i] = values
                    
                    if significance == 3:
                        rankWind = 1 + (i-1)
                        rankWindStr = str(rankWind)
                        values = codes_get(ibufr, f'#{rankWindStr}#windSpeedAt10M')
                        wind[:, i] = values
                    else:
                        print(f"ERROR: unexpected meteorologicalAttributeSignificance={significance}")
                        return
                
                # Process each ensemble member
                print(f"memnumbers {len(memberNumber)}")
                for i in range(len(memberNumber)):
                    skipMember = 1
                    
                    # Check if member has valid data
                    for j in range(len(period)):
                        if (latitude[i, j] != CODES_MISSING_DOUBLE or 
                            latitudeWind[i, j] != CODES_MISSING_DOUBLE):
                            skipMember = 0
                            break
                            
                    if skipMember != 1:
                        mytech = 'ECM '
                        if etypearray[i] == 1:
                            mytech = 'EEMN'
                        elif etypearray[i] > 1:
                            mytech = f"EC{memberNumber[i]:02d}"
                            
                        print(f"== Member {memberNumber[i]}")
                        
                        # Create new forecast record
                        new_fcst = ForecastTrack()
                        new_fcst.basin = basin
                        new_fcst.cyNum = snum
                        new_fcst.DTG = f"{year:04d}{month:02d}{day:02d}{hour:02d}"
                        new_fcst.jdnow = jdmsg
                        new_fcst.technum = 3
                        new_fcst.tech = mytech
                        new_fcst.stormname = sname
                        
                        jnow = 0
                        for j in range(len(period)):
                            if (latitude[i, j] != CODES_MISSING_DOUBLE or 
                                latitudeWind[i, j] != CODES_MISSING_DOUBLE):
                                jnow += 1
                                
                                # Calculate distance between center and max wind
                                dist, angle = self.gcdist(
                                    latitude[i, j], longitude[i, j],
                                    latitudeWind[i, j], longitudeWind[i, j])
                                rmax = dist / NM2M
                                if rmax > 70:
                                    rmax = 70.0  # Limit to prevent superstorms
                                    
                                # Store track data
                                new_fcst.track[jnow]['tau'] = period[j]
                                new_fcst.track[jnow]['lat'] = latitude[i, j]
                                new_fcst.track[jnow]['lon'] = longitude[i, j]
                                new_fcst.track[jnow]['mslp'] = pressure[i, j] / 100.0
                                new_fcst.track[jnow]['vmax'] = wind[i, j] * MS2KTS
                                new_fcst.track[jnow]['mrd'] = rmax
                        
                        self.fcst.append(new_fcst)
                        self.num_fcst += 1
                
                # Write output to ATCF file
                if self.num_fcst > 0:
                    with open(atfile, 'w') as f:
                        self.sort_fcst_records()
                        for i in range(self.num_fcst):
                            self.write_fcst_record(i)
                    print(f"Wrote {self.num_fcst} forecasts.")
                
                # Release BUFR message
                codes_release(ibufr)
                count += 1
                
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
