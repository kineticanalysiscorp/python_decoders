import sys
import os
from datetime import datetime
from typing import NamedTuple, List, Tuple, Optional, Dict

# Constants equivalent to the Fortran module
JMV_HDR_FMT = "(I4,I2,I2,I2,x,I2,A1,x,A10,x,I3,2x,I2,x,I3,x,I2,x,A4,x,I4)"
JMV_FST_FMT = "(X,I3,x,I3,A1,x,I4,A1,x,I3)"
JMV_PO1_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,x,I3,A1,x,I3)"
JMV_PO2_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,I4,A1,x,I3)"

SCAN_HDR = 0
SCAN_FST = 1
SCAN_POS = 2

# Data structures to replace Fortran records
class TrackPoint(NamedTuple):
    tau: int
    lat: float
    lon: float
    vmax: int
    mslp: int
    ty: str = '  '

class ForecastRecord(NamedTuple):
    basin: str
    cyNum: int
    DTG: str
    jdnow: float
    technum: int
    tech: str
    stormname: str
    track: List[TrackPoint]

# Global variables to replace Fortran common blocks
fcst_records: List[ForecastRecord] = []
carq_records: List[dict] = []  # Simplified for this example
num_fcst = 0
num_carq = 0

def djuliana(mm: int, dd: int, yy: int, hh: float) -> float:
    """Convert date to Julian day (simplified implementation)"""
    # Note: This is a simplified version. For precise calculations, consider using datetime or specialized libraries
    dt = datetime(yy, mm, dd) if yy > 100 else datetime(1900 + yy, mm, dd)
    return dt.timestamp() / 86400 + 2440587.5 + hh/24  # Unix epoch to Julian day conversion

def clear_internal_atcf():
    """Clear internal ATCF records"""
    global fcst_records, carq_records, num_fcst, num_carq
    fcst_records = []
    carq_records = []
    num_fcst = 0
    num_carq = 0

def get_atcf_records(atfile: str, tech_filter: str):
    """Load ATCF records from file (simplified implementation)"""
    global fcst_records, num_fcst
    # In a real implementation, this would parse the ATCF file format
    # For now, we'll just mock the functionality
    if os.path.exists(atfile):
        print(f"Loading {atfile}")
        # This would actually parse the file and populate fcst_records
    else:
        print(f"*Caution* {atfile} does not exist!")

def sort_fcst_records():
    """Sort forecast records (simplified implementation)"""
    global fcst_records
    # In a real implementation, this would sort by some criteria
    pass

def sort_carq_records():
    """Sort CARQ records (simplified implementation)"""
    global carq_records
    # In a real implementation, this would sort by some criteria
    pass

def write_fcst_record(idx: int):
    """Write forecast record to file (simplified implementation)"""
    # In a real implementation, this would write in ATCF format
    record = fcst_records[idx]
    print(f"Writing forecast record: {record}")

def write_carq_record(idx: int):
    """Write CARQ record to file (simplified implementation)"""
    # In a real implementation, this would write in ATCF format
    record = carq_records[idx]
    print(f"Writing CARQ record: {record}")

def match_jma_id(jmaid: int, yy: int) -> Tuple[str, bool]:
    """Match JMA ID to ATCF ID using cross-reference file"""
    found = False
    atcfid = ""
    
    if not os.path.exists('jma_atcf.xref'):
        return atcfid, found
    
    with open('jma_atcf.xref', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                aid = int(parts[0])
                aidtxt = parts[1]
                try:
                    ayy = int(aidtxt[4:8])  # Assuming format is consistent with Fortran code
                except (ValueError, IndexError):
                    continue
                
                if jmaid == aid and ayy == yy:
                    atcfid = aidtxt
                    found = True
                    print(f"Found JMAID XREF {jmaid} {atcfid}")
                    break
    
    return atcfid, found

def update_jma_id(jmaid: int, atcfid: str):
    """Update JMA cross-reference file with new ID"""
    print(f"Updating JMA cross reference file {jmaid} {atcfid}")
    with open('jma_atcf.xref', 'a') as f:
        f.write(f"{jmaid} {atcfid}\n")

def match_atcf_id(lat: float, lon: float, yy: int, mm: int, dd: int, hh: int) -> Tuple[str, bool]:
    """Match position and date to ATCF ID (simplified implementation)"""
    # In a real implementation, this would use a database or algorithm to find matching storms
    # For now, we'll return a dummy value
    atcfid = "WP012023"  # Dummy value
    found = True
    return atcfid, found

def main():
    global fcst_records, num_fcst
    
    print("\nNP/JMA TEPS to ATCF Track File Version 1.0")
    print("Copyright(c) 2009-11, Charles C Watson Jr.  All Rights Reserved.\n")
    
    # Parse command line arguments
    infile = 'msgin'
    numargs = len(sys.argv) - 1
    i = 1
    while i <= numargs:
        argin = sys.argv[i]
        if argin.startswith("-in"):
            if i + 1 <= numargs:
                infile = sys.argv[i + 1]
                i += 1
        i += 1
    
    # Check if input file exists
    if not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!")
        sys.exit(1)
    
    print(f"Reading {infile}")
    
    # Read and process the input file
    with open(infile, 'r') as f:
        # Find RJTD line
        buffy = ""
        for line in f:
            if "RJTD" in line:
                buffy = line.strip()
                break
        
        wmohdr = buffy[:18]
        
        # Find NAME and PSTN lines
        jmaid = -1
        for line in f:
            buffy = line.strip()
            if buffy.startswith('NAME'):
                print(buffy)
                iz = buffy.find('(')
                if iz > 0:
                    try:
                        jmaid = int(buffy[iz+1:])
                    except ValueError:
                        pass
            if buffy.startswith('PSTN'):
                break
        
        # Parse position line
        parts = buffy[5:].split()
        try:
            dd = int(parts[0])
            hh = int(parts[1])
            rlat = float(parts[2][:-1])
            ns = parts[2][-1]
            rlon = float(parts[3][:-1])
            ew = parts[3][-1]
        except (ValueError, IndexError):
            print("Error parsing position line")
            sys.exit(1)
        
        if ns == 'S':
            rlat = -rlat
        if ew == 'W':
            rlon = -rlon
        
        now = datetime.now()
        yy = now.year
        mm = now.month
        if dd > now.day:
            mm -= 1
        
        jdnow = djuliana(mm, dd, yy, hh * 1.0)
        
        # Match JMA ID or position to ATCF ID
        atcfid = ""
        found = False
        if jmaid > 0:
            atcfid, found = match_jma_id(jmaid, yy)
        
        if not found:
            atcfid, found = match_atcf_id(rlat, rlon, yy, mm, dd, hh)
            invest = False
            if found and jmaid > 0:
                try:
                    iz = int(atcfid[3])
                    if iz >= 7:
                        invest = True
                    if not invest:
                        update_jma_id(jmaid, atcfid)
                except (ValueError, IndexError):
                    pass
        
        if not found:
            print(f"No ATCF match {yy} {dd} {mm} {hh} {rlat} {rlon}")
            sys.exit(1)
        
        clear_internal_atcf()
        
        # Process ATCF file
        atfile = f"A{atcfid}.jmaobj"
        if not os.path.exists(atfile):
            print(f"*Caution* {atfile} does not exist!")
            num_fcst = 0
        else:
            clear_internal_atcf()
            get_atcf_records(atfile, 'ANY ')
        
        jdmsg = djuliana(mm, dd, yy, hh * 1.0)
        found = False
        for rec in fcst_records:
            if rec.tech == 'JMAE' and abs(rec.jdnow - jdmsg) < 1.0/24:
                found = True
                break
        
        if found:
            print("Forecast already in ATCF file")
            return
        
        # Read forecast data
        ivmax = 0
        pmin = 0
        for line in f:
            buffy = line.strip()
            if "FORECAST" in buffy:
                break
            if buffy.startswith('MXWD'):
                try:
                    ivmax = int(buffy[5:8])
                except ValueError:
                    pass
            if buffy.startswith('PRES'):
                try:
                    pmin = int(buffy[5:9])
                except ValueError:
                    pass
        
        # Create new forecast record
        num_fcst += 1
        basin = atcfid[:2]
        try:
            inum = int(atcfid[2:4])
        except ValueError:
            inum = 0
        
        dtg = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
        track = [TrackPoint(tau=0, lat=rlat, lon=rlon, vmax=ivmax, mslp=pmin)]
        
        # Read forecast positions
        numfpos = 1
        for line in f:
            buffy = line.strip()
            if len(buffy) < 3:
                continue
            if "T=" in buffy:
                try:
                    parts = buffy[2:].split()
                    vt = int(parts[0])
                    rlat = float(parts[1][:-1])
                    ns = parts[1][-1]
                    rlon = float(parts[2][:-1])
                    ew = parts[2][-1]
                    delp = int(parts[3])
                    delv = int(parts[4])
                except (ValueError, IndexError):
                    continue
                
                if ns == 'S':
                    rlat = -rlat
                if ew == 'W':
                    rlon = -rlon
                
                numfpos += 1
                track.append(TrackPoint(
                    tau=vt,
                    lat=rlat,
                    lon=rlon,
                    vmax=track[0].vmax + delv,
                    mslp=track[0].mslp + delp
                ))
                print(f"{numfpos} {vt} {rlat} {rlon} {delp} {delv}")
        
        if numfpos <= 1:
            sys.exit(1)
        
        # Add the new forecast record
        fcst_records.append(ForecastRecord(
            basin=basin,
            cyNum=inum,
            DTG=dtg,
            jdnow=jdmsg,
            technum=1,
            tech='JMAE',
            stormname='',
            track=track
        ))
    
    # Write output
    with open(atfile, 'w') as f:
        sort_carq_records()
        for i in range(num_carq):
            write_carq_record(i)
        
        sort_fcst_records()
        for i in range(num_fcst):
            write_fcst_record(i)
    
    print(f"Updated {atcfid} ATCF file.")
    with open('jmao_updated.dat', 'a') as f:
        f.write(f"{atcfid}\n")

if __name__ == "__main__":
    main()
