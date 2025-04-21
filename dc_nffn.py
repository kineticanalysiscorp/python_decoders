import sys
import os
from datetime import datetime
import re

# Constants and module-level variables
JMEE_HDR_FMT = "(I4,I2,I2,I2,x,I2,A1,x,A10,x,I3,2x,I2,x,I3,x,I2,x,A4,x,I4)"
JMEE_FST_FMT = "(X,I3,x,I3,A1,x,I4,A1,x,I3)"
JMEE_PO1_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,x,I3,A1,x,I3)"
JMEE_PO2_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,I4,A1,x,I3)"

UINP = 200
USQL = 201

SCAN_HDR = 0
SCAN_FST = 1
SCAN_POS = 2
scan_mode = SCAN_HDR

# ATCF-related structures (simplified for Python)
class TrackPoint:
    def __init__(self):
        self.tau = 0
        self.lat = -999.0
        self.lon = -999.0
        self.vmax = -999
        self.mslp = -999
        self.ty = '  '

class Forecast:
    def __init__(self):
        self.basin = ''
        self.cyNum = 0
        self.DTG = ''
        self.jdnow = 0.0
        self.technum = 0
        self.tech = ''
        self.stormname = ''
        self.track = [TrackPoint() for _ in range(36)]

# Global variables
num_fcst = 0
fcst = []
num_carq = 0
carq = []

def djuliana(mm, dd, yy, hh):
    """Approximate Julian date calculation (simplified)"""
    # Note: This is a simplified version. For precise calculations, consider using astronomy libraries
    a = (14 - mm) // 12
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jdn = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (hh - 12) / 24.0

def clear_internal_atcf():
    """Clear internal ATCF data structures"""
    global num_fcst, fcst, num_carq, carq
    num_fcst = 0
    fcst = []
    num_carq = 0
    carq = []

def match_atcf_id(fix_lat, fix_lon, jdnow, atcfid, found):
    """
    Match storm based on position and time
    Simplified version - in a real implementation, you'd need a database or file lookup
    """
    # This is a placeholder - actual implementation would need a proper matching system
    atcfid[0] = 'SH'  # Default basin (South Hemisphere)
    atcfid[2:] = '01'  # Default storm number
    found[0] = True  # Assume we found a match for this example

def get_atcf_records(atfile, tech_filter):
    """Load ATCF records from file"""
    # This would parse the ATCF file and populate the global fcst and carq variables
    pass

def sort_carq_records():
    """Sort CARQ records"""
    # Implementation would sort the carq list
    pass

def write_carq_record(i):
    """Write CARQ record to file"""
    # Implementation would write the record
    pass

def sort_fcst_records():
    """Sort forecast records"""
    # Implementation would sort the fcst list
    pass

def write_fcst_record(i):
    """Write forecast record to file"""
    # Implementation would write the record
    pass

def parse_numeric_field(buffy, start, length):
    """Parse numeric field from buffer, handling special characters"""
    nbuf = []
    wflag = False
    sflag = False
    
    for i in range(start, start + length):
        c = buffy[i]
        if c == 'W':
            wflag = True
        elif c == 'S':
            sflag = True
        elif not c.isdigit() and c != '.':
            c = ' '
        nbuf.append(c)
    
    num_str = ''.join(nbuf).strip()
    if not num_str:
        return None, False, False
    
    try:
        value = float(num_str)
        return value, wflag, sflag
    except ValueError:
        return None, False, False

def main():
    global num_fcst, fcst
    
    print("\nRSMC Nadi (NFFN) to ATCF Track File Version 1.0")
    print("Copyright(c) 2010-2020, Charles C Watson Jr.  All Rights Reserved.\n")
    
    numpos = 0
    numfpos = 0
    
    now = datetime.now()
    yy = now.year
    mm = now.month
    
    # Parse command line arguments
    infile = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith("-in"):
            if i+1 < len(sys.argv):
                infile = sys.argv[i+2]
    
    if not infile or not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!" if infile else "*Error* No input file specified!")
        sys.exit(1)
    
    print(f"Reading {infile}")
    
    with open(infile, 'r') as f:
        while True:
            numpos = 0
            numfpos = 0
            mvmt = 'NA'
            mslp = 0
            
            # Find NFFN header
            for line in f:
                if "NFFN" in line:
                    wmohdr = line[:18]
                    print(wmohdr.strip())
                    dd = int(line[12:14])
                    hh = int(line[14:16])
                    break
            
            # Skip next line
            next(f)
            
            # Find position and pressure
            fix_lat = 0.0
            fix_lon = 0.0
            ivmax = 0
            
            for line in f:
                if "LOCATED NEAR" in line:
                    iz = line.index("LOCATED NEAR") + 12
                    
                    # Parse latitude
                    tlat, _, sflag = parse_numeric_field(line, iz, 8)
                    if tlat is not None:
                        fix_lat = -tlat if sflag else tlat
                    
                    # Parse pressure
                    iz = line.find("HPA ") - 5
                    mslp_str, _, _ = parse_numeric_field(line, iz, 8)
                    if mslp_str is not None:
                        mslp = int(mslp_str)
                    
                    # Read next line for longitude
                    line = next(f)
                    iz = 0
                    tlon, wflag, _ = parse_numeric_field(line, iz, 8)
                    if tlon is not None:
                        fix_lon = -tlon if wflag else tlon
                    
                    break
            
            # Find maximum winds
            for line in f:
                if "AVERAGE" in line:
                    iz = line.find("AVERAGE")
                    iz = line.find("KNOTS", iz+1)
                    if iz == -1:
                        line = next(f)
                        iz = line.find("KNOTS")
                    
                    iz = iz - 5
                    ivmax_str, _, _ = parse_numeric_field(line, iz, 8)
                    if ivmax_str is not None:
                        ivmax = int(ivmax_str)
                    break
            
            print(fix_lat, fix_lon, yy, mm, dd, hh)
            
            jdnow = djuliana(mm, dd, yy, hh * 1.0)
            atcfid = ''
            found = [False]
            
            match_atcf_id(fix_lat, fix_lon, jdnow, atcfid, found)
            if not found[0]:
                print(f"No ATCF match {yy} {dd} {mm} {hh} {fix_lat} {fix_lon}")
                continue
            
            invest = False
            if len(atcfid) >= 4 and atcfid[3].isdigit():
                iz = int(atcfid[3])
                if iz >= 7:
                    invest = True
            
            print(atcfid, yy, mm, dd, hh)
            clear_internal_atcf()
            
            atfile = f"A{atcfid}.nffn"
            if not os.path.exists(atfile):
                print(f"*Caution* {atfile} does not exist!")
                num_fcst = 0
            else:
                clear_internal_atcf()
                get_atcf_records(atfile, 'ANY ')
            
            jdmsg = djuliana(mm, dd, yy, hh * 1.0)
            found_record = False
            for i in range(num_fcst):
                if (fcst[i].tech == 'NFFN' and abs(fcst[i].jdnow - jdmsg) < 1.0/24):
                    found_record = True
                    break
            
            if found_record:
                print("Forecast already in ATCF file")
                continue
            
            # Add new forecast record
            new_fcst = Forecast()
            new_fcst.basin = atcfid[:2]
            try:
                inum = int(atcfid[2:4])
                new_fcst.cyNum = inum
            except ValueError:
                new_fcst.cyNum = 0
            
            new_fcst.DTG = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
            new_fcst.jdnow = jdmsg
            new_fcst.technum = 1
            new_fcst.tech = 'NFFN'
            new_fcst.stormname = ''
            
            # Add initial position
            numfpos = 1
            new_fcst.track[0].tau = 0
            new_fcst.track[0].lat = fix_lat
            new_fcst.track[0].lon = fix_lon
            new_fcst.track[0].vmax = ivmax
            new_fcst.track[0].mslp = mslp
            
            # Parse forecast positions
            for line in f:
                if line.startswith('AT '):
                    parts = line[3:].split()
                    vt = int(parts[0])
                    
                    # Parse latitude
                    iz = line.find("UTC") + 3
                    tlat, _, sflag = parse_numeric_field(line, iz, 8)
                    if tlat is None:
                        continue
                    if sflag:
                        tlat = -tlat
                    
                    # Parse longitude
                    iz = line.find("MOV") - 9
                    tlon, wflag, _ = parse_numeric_field(line, iz, 8)
                    if tlon is None:
                        continue
                    if wflag:
                        tlon = -tlon
                    
                    # Parse wind speed
                    iz = line.find("WITH") + 4
                    ivmax_str, _, _ = parse_numeric_field(line, iz, 8)
                    if ivmax_str is None:
                        continue
                    ivmax = int(ivmax_str)
                    
                    # Add forecast point
                    if numfpos < 36:
                        new_fcst.track[numfpos].tau = vt
                        new_fcst.track[numfpos].lat = tlat
                        new_fcst.track[numfpos].lon = tlon
                        new_fcst.track[numfpos].vmax = ivmax
                        print(vt, tlat, tlon, ivmax)
                        numfpos += 1
            
            # Add the new forecast to the list
            fcst.append(new_fcst)
            num_fcst += 1
            
            # Write to ATCF file
            with open(atfile, 'w') as atcf_file:
                sort_carq_records()
                for i in range(num_carq):
                    write_carq_record(i)
                
                sort_fcst_records()
                for i in range(num_fcst):
                    write_fcst_record(i)
            
            print(f"Updated {atcfid} ATCF file.")
            
            with open('nffn_updated.dat', 'a') as sql_file:
                sql_file.write(f"{atcfid}\n")

if __name__ == "__main__":
    main()
