import os
import re
from datetime import datetime
import sys

# Global variables and parameters
UINP = 200
USQL = 201

# Data structures to replace Fortran records
class ForecastTrack:
    def __init__(self):
        self.tau = 0
        self.lat = -999.0
        self.lon = -999.0
        self.vmax = -999
        self.mslp = -999
        self.mrd = -999
        self.ty = "  "

class ForecastRecord:
    def __init__(self):
        self.basin = ""
        self.cyNum = 0
        self.DTG = ""
        self.jdnow = 0.0
        self.technum = 0
        self.tech = ""
        self.stormname = ""
        self.track = [ForecastTrack() for _ in range(36)]

# Global storage for forecasts and carq records
num_fcst = 0
fcst = []
num_carq = 0
carq = []

# -----------------------------------------------------------------
# Utility functions
def djuliana(mm, dd, yy, hh):
    """Convert Gregorian date to Julian date"""
    a = (14 - mm) // 12
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jdn = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (hh - 12) / 24.0

def clear_internal_atcf():
    global num_fcst, fcst, num_carq, carq
    num_fcst = 0
    fcst = []
    num_carq = 0
    carq = []

def get_atcf_records(atfile, tech_filter):
    """Read ATCF records from file"""
    global num_fcst, fcst
    
    try:
        with open(atfile, 'r') as f:
            for line in f:
                if line.startswith(('AL', 'EP', 'CP', 'WP', 'IO', 'SH')):
                    parts = line.split(',')
                    if len(parts) < 11:
                        continue
                    
                    # Create new forecast record if needed
                    if num_fcst == 0 or fcst[-1].DTG != parts[2].strip():
                        num_fcst += 1
                        new_fcst = ForecastRecord()
                        new_fcst.basin = parts[0].strip()
                        new_fcst.cyNum = int(parts[1].strip())
                        new_fcst.DTG = parts[2].strip()
                        new_fcst.technum = int(parts[4].strip())
                        new_fcst.tech = parts[5].strip()
                        new_fcst.stormname = parts[27].strip() if len(parts) > 27 else ""
                        
                        # Parse date to calculate Julian date
                        dtg = new_fcst.DTG
                        yy = int(dtg[:4])
                        mm = int(dtg[4:6])
                        dd = int(dtg[6:8])
                        hh = int(dtg[8:10])
                        new_fcst.jdnow = djuliana(mm, dd, yy, hh)
                        
                        fcst.append(new_fcst)
                    
                    # Add track data
                    tau = int(parts[3].strip())
                    lat = float(parts[6].strip())
                    lon = float(parts[7].strip())
                    vmax = int(parts[8].strip())
                    mslp = int(parts[9].strip()) if parts[9].strip() else -999
                    
                    # Find position in track (tau/6 for 6-hourly intervals)
                    pos = tau // 6
                    if pos < 0 or pos >= 36:
                        continue
                    
                    fcst[-1].track[pos].tau = tau
                    fcst[-1].track[pos].lat = lat
                    fcst[-1].track[pos].lon = lon
                    fcst[-1].track[pos].vmax = vmax
                    fcst[-1].track[pos].mslp = mslp
    except FileNotFoundError:
        print(f"*Caution* {atfile} does not exist!")
        num_fcst = 0

def sort_carq_records():
    """Sort CARQ records (placeholder)"""
    pass

def sort_fcst_records():
    """Sort forecast records by date"""
    global fcst
    fcst.sort(key=lambda x: x.DTG)

def write_carq_record(index):
    """Write CARQ record to file (placeholder)"""
    pass

def write_fcst_record(index):
    """Write forecast record to ATCF file"""
    rec = fcst[index]
    with open(atfile, 'a') as f:
        for track in rec.track:
            if track.lat == -999:
                continue
            line = (
                f"{rec.basin}, {rec.cyNum:02d}, {track.tau:03d}, {rec.DTG}, "
                f"{rec.technum:03d}, {rec.tech:4s}, {track.lat:5.1f}N, {track.lon:5.1f}E, "
                f"{track.vmax:03d}, {track.mslp:04d}, , , , , , , , , , , , , , "
                f"{rec.stormname}\n"
            )
            f.write(line)

def match_atcf_id(fix_lat, fix_lon, jdnow, atcfid):
    """Match position with ATCF ID (placeholder implementation)"""
    # This would need actual implementation based on how the matching works
    found = False
    atcfid[0] = "IO012023"  # Placeholder for Indian Ocean storm
    return found

def clean_number_string(s):
    """Clean a string to extract numbers and decimal points"""
    return ''.join([c if c.isdigit() or c == '.' else ' ' for c in s])

# -----------------------------------------------------------------
# Main program
def main():
    global num_fcst, fcst, num_carq, carq, atfile
    
    print("\nRSMC New Delhi to ATCF Track File Version 2.0")
    print("Copyright(c) 2010-2020, Charles C Watson Jr.  All Rights Reserved.\n")
    
    # Parse command line arguments
    args = sys.argv[1:]
    infile = ""
    
    for i in range(len(args)):
        if args[i] == "-in" and i+1 < len(args):
            infile = args[i+1]
            break
    
    if not infile:
        print("Usage: python dc_dems.py -in <input_file>")
        sys.exit(1)
    
    if not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!")
        sys.exit(1)
    
    print(f"Reading {infile}")
    
    # Initialize variables
    numpos = 0
    numfpos = 0
    mvmt = "NA"
    rmax = 0
    vmax = 0
    atcfid = [""]
    wmohdr = ""
    fix_lat = 0.0
    fix_lon = 0.0
    mslp = 0
    hh = 0
    mm = 0
    dd = 0
    yy = datetime.now().year
    
    # Main processing loop
    while True:
        numpos = 0
        numfpos = 0
        mvmt = "NA"
        rmax = 0
        vmax = 0
        
        with open(infile, 'r') as f:
            # Find the WMO header
            for line in f:
                if "WTIN" in line:
                    wmohdr = line[:18]
                    print(wmohdr.strip())
                    break
            
            # Parse the header information
            for line in f:
                line = line.strip()
                if 'PRESENT DATE' in line:
                    print(line)
                    iz = line.find(':') + 2
                    try:
                        dd, hh = map(int, line[iz:iz+5].split())
                    except ValueError:
                        continue
                
                elif 'PRESENT POSITION' in line:
                    print(line)
                    iz = line.find(':') + 1
                    
                    # Extract latitude
                    lat_str = clean_number_string(line[iz:iz+8])
                    try:
                        tlat = float(lat_str)
                    except ValueError:
                        continue
                    
                    # Extract longitude
                    iz_slash = line.find('/')
                    lon_str = clean_number_string(line[iz_slash:iz_slash+8])
                    try:
                        tlon = float(lon_str)
                    except ValueError:
                        continue
                
                elif 'MAX SUSTAINED' in line:
                    print(line)
                    iz = line.find(':') + 2
                    try:
                        vmax = int(line[iz:].strip())
                    except ValueError:
                        continue
                
                elif 'RADIUS OF MAXIMUM' in line:
                    print(line)
                    iz = line.find('WIND') + 5
                    try:
                        rmax = int(line[iz:].strip())
                    except ValueError:
                        continue
                
                elif 'FORECASTS:' in line:
                    break
        
        # Adjust month if needed
        current_day = datetime.now().day
        if dd > current_day:
            mm = datetime.now().month - 1
        else:
            mm = datetime.now().month
        
        print(f"{yy} {mm} {dd} {hh}")
        print(f"{tlat} {tlon} {vmax} {rmax}")
        
        fix_lat = tlat
        fix_lon = tlon
        mslp = 0  # DEMs doesn't seem to provide MSLP
        
        jdnow = djuliana(mm, dd, yy, hh)
        
        # Match the storm ID
        found = match_atcf_id(fix_lat, fix_lon, jdnow, atcfid)
        invest = False
        if found:
            try:
                iz = int(atcfid[0][3])
                if iz >= 7:
                    invest = True
            except (ValueError, IndexError):
                pass
        
        if not found:
            print(f"No ATCF match {yy} {dd} {mm} {hh} {fix_lat} {fix_lon}")
            continue  # Instead of stop, we continue to process next message
        
        print(f"{atcfid[0]} {yy} {mm} {dd} {hh}")
        
        # Prepare the ATCF file
        atfile = f"A{atcfid[0]}.dems"
        valid = os.path.exists(atfile)
        if not valid:
            print(f"*Caution* {atfile} does not exist!")
            num_fcst = 0
        else:
            clear_internal_atcf()
            get_atcf_records(atfile, 'ANY ')
        
        # Check if this forecast already exists
        jdmsg = djuliana(mm, dd, yy, hh)
        found = False
        for f in fcst:
            if f.tech == 'DEMS' and abs(f.jdnow - jdmsg) < 1.0/24:
                found = True
                break
        
        if found:
            print("Forecast already in ATCF file")
            continue
        
        # Add new forecast record
        num_fcst += 1
        new_fcst = ForecastRecord()
        new_fcst.basin = atcfid[0][:2]
        try:
            new_fcst.cyNum = int(atcfid[0][2:4])
        except ValueError:
            new_fcst.cyNum = 0
        new_fcst.DTG = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
        new_fcst.jdnow = jdmsg
        new_fcst.technum = 1
        new_fcst.tech = "DEMS"
        new_fcst.stormname = ''
        
        # Add initial position
        numfpos = 1
        new_fcst.track[0].tau = 0
        new_fcst.track[0].lat = fix_lat
        new_fcst.track[0].lon = fix_lon
        new_fcst.track[0].vmax = vmax
        new_fcst.track[0].mslp = mslp
        new_fcst.track[0].mrd = rmax
        
        # Parse forecast data
        with open(infile, 'r') as f:
            # Skip to forecast data
            for line in f:
                if 'FORECASTS:' in line:
                    break
            
            # Read forecast positions
            while True:
                line = f.readline()
                if not line:
                    break
                
                if 'VALID AT' not in line:
                    continue
                
                try:
                    # Parse valid time
                    vt = int(line.split()[0])
                    
                    # Read next line for date and position
                    line = f.readline()
                    if not line:
                        break
                    
                    # Parse date
                    try:
                        dd1, hh1 = map(int, line[:5].split())
                    except ValueError:
                        continue
                    
                    # Parse latitude
                    iz_z = line.find('Z')
                    lat_str = clean_number_string(line[iz_z:iz_z+8])
                    try:
                        tlat = float(lat_str)
                    except ValueError:
                        continue
                    
                    # Parse longitude
                    iz_slash = line.find('/')
                    lon_str = clean_number_string(line[iz_slash:iz_slash+8])
                    try:
                        tlon = float(lon_str)
                    except ValueError:
                        continue
                    
                    # Read next line for wind speed
                    line = f.readline()
                    if not line:
                        break
                    
                    # Parse wind speed
                    iz_colon = line.find(':') + 1
                    try:
                        ivmax = int(line[iz_colon:].strip())
                    except ValueError:
                        continue
                    
                    # Add to forecast track
                    if numfpos < 36:
                        new_fcst.track[numfpos].tau = vt
                        new_fcst.track[numfpos].lat = tlat
                        new_fcst.track[numfpos].lon = tlon
                        new_fcst.track[numfpos].vmax = ivmax
                        print(f"{vt} {tlat} {tlon} {ivmax}")
                        numfpos += 1
                
                except (ValueError, IndexError):
                    continue
        
        fcst.append(new_fcst)
        
        # Write the updated ATCF file
        with open(atfile, 'w') as f:
            # Write CARQ records (placeholder)
            pass
        
        # Sort and write forecast records
        sort_fcst_records()
        for i in range(num_fcst):
            write_fcst_record(i)
        
        print(f"Updated {atcfid[0]} ATCF file.")
        
        # Update the SQL file
        with open('dems_updated.dat', 'a') as f:
            f.write(f"{atcfid[0]}\n")

if __name__ == "__main__":
    main()
