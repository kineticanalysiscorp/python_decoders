import sys
import os
from datetime import datetime
import re
from typing import List, Dict, Tuple, Optional

# Module-level constants (equivalent to the Fortran module)
JMV_HDR_FMT = "(I4,I2,I2,I2,x,I2,A1,x,A10,x,I3,2x,I2,x,I3,x,I2,x,A4,x,I4)"
JMV_FST_FMT = "(X,I3,x,I3,A1,x,I4,A1,x,I3)"
JMV_PO1_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,x,I3,A1,x,I3)"
JMV_PO2_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,I4,A1,x,I3)"

UINP = 200
USQL = 201

SCAN_HDR = 0
SCAN_FST = 1
SCAN_POS = 2

# Global variables to maintain state similar to Fortran
inbuffy = ""
num_fcst = 0
fcst = []  # Will be a list of dictionaries to hold forecast data
num_carq = 0
carq = []  # Will be a list of dictionaries to hold carq data

class ForecastTrack:
    def __init__(self):
        self.tau = 0
        self.lat = -999.0
        self.lon = -999.0
        self.vmax = 0
        self.mslp = 0
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
        self.track = [ForecastTrack() for _ in range(36)]  # 36 track positions

def djuliana(mm: int, dd: int, yy: int, hh: float) -> float:
    """Convert date to Julian day"""
    # This is a placeholder - need proper Julian date calculation
    dt = datetime(yy, mm, dd) + timedelta(hours=hh)
    a = (14 - mm) // 12
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jdn = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (hh / 24.0) - 0.5

def getline(file_handle) -> Tuple[str, int]:
    """Read a line from input file and clean it"""
    global inbuffy
    line = file_handle.readline()
    if not line:
        return "", 1  # EOF
    
    # Clean the line - replace control characters with spaces
    cleaned = []
    for c in line:
        if ord(c) <= 13:
            cleaned.append(' ')
        else:
            cleaned.append(c)
    inbuffy = ''.join(cleaned).strip()
    return inbuffy, 0

def match_pag_id(jmaid: int, yy: int) -> Tuple[str, bool]:
    """Match PAGASA ID to ATCF ID from reference file"""
    found = False
    atcfid = ""
    
    if not os.path.exists('pag_atcf.xref'):
        return atcfid, found
    
    with open('pag_atcf.xref', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            try:
                aid = int(parts[0])
                aidtxt = parts[1]
                ayy = int(aidtxt[4:8]) if len(aidtxt) >= 8 else 0
                
                if jmaid == aid and ayy == yy:
                    atcfid = aidtxt
                    found = True
                    print(f"Found PAGID XREF {jmaid} {atcfid}")
                    break
            except (ValueError, IndexError):
                continue
    
    return atcfid, found

def update_pag_id(jmaid: int, atcfid: str):
    """Update the PAGASA cross reference file"""
    print(f"Updating PAGASA cross reference file {jmaid} {atcfid}")
    with open('pag_atcf.xref', 'a') as f:
        f.write(f"{jmaid} {atcfid}\n")

def match_atcf_id(rlat: float, rlon: float, yy: int, mm: int, dd: int, hh: int) -> Tuple[str, bool]:
    """Match position and date to find ATCF ID"""
    # This is a placeholder - the actual implementation would need to 
    # compare with existing ATCF data to find matching storms
    # In the original Fortran, this appears to be implemented elsewhere
    return "", False

def clear_internal_atcf():
    """Clear internal ATCF data structures"""
    global num_fcst, fcst, num_carq, carq
    num_fcst = 0
    fcst = []
    num_carq = 0
    carq = []

def get_atcf_records(atfile: str, tech: str):
    """Read ATCF records from file"""
    # This is a placeholder - would need to implement actual ATCF file parsing
    global num_fcst, fcst
    if not os.path.exists(atfile):
        return
    
    # In a real implementation, we would parse the ATCF file here
    # and populate the fcst list with ForecastRecord objects
    pass

def sort_carq_records():
    """Sort CARQ records"""
    # Placeholder - would implement sorting logic
    pass

def write_carq_record(idx: int):
    """Write a CARQ record"""
    # Placeholder - would implement writing logic
    pass

def sort_fcst_records():
    """Sort forecast records"""
    # Placeholder - would implement sorting logic
    pass

def write_fcst_record(idx: int):
    """Write a forecast record"""
    # Placeholder - would implement writing logic
    pass

def main():
    global num_fcst, fcst, inbuffy
    
    # Initialize variables
    numpos = 0
    numfpos = 0
    infile = ""
    
    # Parse command line arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-in":
            i += 1
            if i < len(args):
                infile = args[i]
        i += 1
    
    # Check if input file exists
    if not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!")
        sys.exit(1)
    
    print(f"Reading {infile}")
    
    with open(infile, 'r') as finp:
        while True:
            numpos = 0
            numfpos = 0
            mvmt = "NA"
            iadv = 0
            mslp = 0
            
            # Find RPMM header
            while True:
                buffy = finp.readline()
                if not buffy:
                    return  # EOF
                if "RPMM" in buffy:
                    break
            
            wmohdr = buffy[:18].strip()
            print(wmohdr)
            
            jmaid = -1
            hh = 0
            dd = 0
            mm = 0
            yy = 0
            
            # Parse the header information
            while True:
                buffy = finp.readline()
                if not buffy:
                    return  # EOF
                
                if buffy[5:11] == "PAGASA":
                    print(buffy.strip())
                    buffy = finp.readline()
                    iz = buffy.find('(')
                    if iz != -1:
                        try:
                            jmaid = int(buffy[iz+1:].split()[0])
                        except (ValueError, IndexError):
                            jmaid = -1
                
                if buffy.startswith("ANAL"):
                    try:
                        hh = int(buffy[12:14])
                        dd = int(buffy[20:22])
                        if "APRIL" in buffy:
                            mm = 4
                    except (ValueError, IndexError):
                        print("Error reading date")
                        return
                
                if buffy.startswith("PSTN"):
                    break
            
            # Get current date if not set
            if yy == 0:
                now = datetime.now()
                yy = now.year
                mm = now.month if mm == 0 else mm
            
            # Parse position
            try:
                parts = buffy[5:].split()
                rlat = float(parts[0][:-1])
                ns = parts[0][-1]
                rlon = float(parts[1][:-1])
                ew = parts[1][-1]
                
                if ns == 'S':
                    rlat = -rlat
                if ew == 'W':
                    rlon = -rlon
                
                if dd > datetime.now().day:
                    mm -= 1
            except (ValueError, IndexError):
                print("Error reading position")
                return
            
            print(yy, mm, dd, hh, rlat, rlon)
            jdnow = djuliana(mm, dd, yy, hh * 1.0)
            
            # Find matching ATCF ID
            atcfid, found = match_pag_id(jmaid, yy)
            
            if not found:
                print("Trying to match ATCFID...")
                atcfid, found = match_atcf_id(rlat, rlon, yy, mm, dd, hh)
                if found:
                    invest = False
                    if len(atcfid) >= 4:
                        try:
                            iz = int(atcfid[3])
                            if iz >= 7:
                                invest = True
                        except ValueError:
                            pass
                    
                    if jmaid > 0:
                        update_pag_id(jmaid, atcfid)
            
            if not found:
                print(f"No ATCF match {yy} {mm} {dd} {hh} {rlat} {rlon}")
                return
            
            print(f"atcfid: {atcfid}  jmaid: {jmaid}")
            
            atfile = f"A{atcfid}.pag"
            valid = os.path.exists(atfile)
            if not valid:
                print(f"*Caution* {atfile} does not exist!")
                num_fcst = 0
            else:
                clear_internal_atcf()
                get_atcf_records(atfile, 'ANY ')
            
            jdmsg = djuliana(mm, dd, yy, hh * 1.0)
            found = False
            for i in range(num_fcst):
                if (hasattr(fcst[i], 'tech') and fcst[i].tech == 'RPMM' and 
                    abs(fcst[i].jdnow - jdmsg) < 1.0/24):
                    found = True
                    break
            
            if found:
                print("Forecast already in ATCF file")
                continue
            
            # Parse movement and other data
            mvmt = buffy[6:].strip()
            mslp = 0
            ivmax = 0
            
            while True:
                buffy = finp.readline()
                if not buffy:
                    break
                
                if "FORECAST" in buffy:
                    break
                
                if buffy.startswith("MXWD"):
                    try:
                        ivmax = int(buffy[5:8])
                    except ValueError:
                        pass
                
                if buffy.startswith("PRES"):
                    try:
                        mslp = int(buffy[5:8])
                    except ValueError:
                        pass
            
            # Create new forecast record
            fr = ForecastRecord()
            num_fcst += 1
            fcst.append(fr)
            
            fr.basin = atcfid[:2]
            try:
                inum = int(atcfid[2:4])
                fr.cyNum = inum
            except ValueError:
                fr.cyNum = 0
            
            fr.DTG = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
            fr.jdnow = jdmsg
            fr.technum = 1
            fr.tech = "RPMM"
            fr.stormname = ""
            
            # Initial position
            numfpos = 1
            fr.track[0].tau = 0
            tlat = rlat
            tlon = rlon
            if ns == 'S':
                tlat = -tlat
            if ew == 'W':
                tlon = -tlon
            fr.track[0].lat = tlat
            fr.track[0].lon = tlon
            fr.track[0].vmax = ivmax
            fr.track[0].mslp = mslp
            fix_lat = tlat
            fix_lon = tlon
            vmax = ivmax
            
            # Parse forecast positions
            while True:
                buffy = finp.readline()
                if not buffy:
                    break
                
                if "VALID" in buffy:
                    try:
                        vt = int(buffy[2:5])
                        buffy = finp.readline()
                        mslp = 0
                        
                        # Parse position
                        parts = buffy.split()
                        rlat = float(parts[0][:-1])
                        ns = parts[0][-1]
                        rlon = float(parts[1][:-1])
                        ew = parts[1][-1]
                        
                        # Parse MSLP if available
                        if len(buffy) >= 60:
                            try:
                                mslp = int(buffy[55:59])
                            except ValueError:
                                pass
                        
                        buffy = finp.readline()
                        try:
                            ivmax = int(buffy[:3])
                        except ValueError:
                            ivmax = 0
                        
                        if ivmax == 0:
                            continue
                        
                        if ns == 'S':
                            rlat = -rlat
                        if ew == 'W':
                            rlon = -rlon
                        
                        numfpos += 1
                        if numfpos >= len(fr.track):
                            # Extend track list if needed
                            fr.track.append(ForecastTrack())
                        
                        fr.track[numfpos-1].tau = vt
                        tlat = rlat
                        tlon = rlon
                        if ns == 'S':
                            tlat = -tlat
                        if ew == 'W':
                            tlon = -tlon
                        fr.track[numfpos-1].lat = tlat
                        fr.track[numfpos-1].lon = tlon
                        fr.track[numfpos-1].vmax = ivmax
                        fr.track[numfpos-1].mslp = mslp
                    except (ValueError, IndexError):
                        continue
            
            # Write output files
            with open(atfile, 'w') as fout:
                sort_carq_records()
                for i in range(num_carq):
                    write_carq_record(i)
                
                sort_fcst_records()
                for i in range(num_fcst):
                    write_fcst_record(i)
            
            print(f"Updated {atcfid} ATCF file.")
            
            with open('pag_updated.dat', 'a') as f:
                f.write(f"{atcfid}\n")
            
            # Write SQL file
            fname = f"{atcfid}_message.sql"
            with open(fname, 'w') as fsql:
                fsql.write("INSERT INTO rsfc_messages (atcfid,rsfcid,msg_hdr,msg_type,msg_advnr,msg_time,fcst_time,lat,lon,vmax,mslp,movement,message,geom) VALUES(\n")
                fsql.write(f"    '{atcfid}',\n")
                fsql.write(f"    '{jmaid:04d}',\n")
                fsql.write(f"    '{wmohdr.strip()}',\n")
                fsql.write("    'FORECAST',\n")
                fsql.write(f"    {iadv:5d},\n")
                fsql.write(f"    '{yy:04d}-{mm:02d}-{dd:02d} {hh:02d}:00',\n")
                fsql.write(f"    '{yy:04d}-{mm:02d}-{dd:02d} {hh:02d}:00',\n")
                fsql.write(f"    {fix_lat:10.5f},\n")
                fsql.write(f"    {fix_lon:10.5f},\n")
                fsql.write(f"    {vmax:5d},\n")
                fsql.write(f"    {mslp:5d},\n")
                fsql.write(f"    '{mvmt.strip()}',\n")
                fsql.write("''\n")
                
                # Write message content
                finp.seek(0)  # Rewind to start of file
                while True:
                    line, ios = getline(finp)
                    if ios != 0:
                        break
                    fsql.write(line + "\n")
                    if line.startswith("//"):
                        break
                
                fsql.write("',\n")
                fsql.write(f"    ST_GeomFromText('POINT({fix_lon:12.6f} {fix_lat:12.6f})',4326));\n")

if __name__ == "__main__":
    main()
