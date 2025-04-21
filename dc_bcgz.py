import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class TrackPoint:
    def __init__(self):
        self.tau = 0
        self.lat = -999.0
        self.lon = -999.0
        self.vmax = 0
        self.mslp = 0
        self.mrd = 0
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
        self.track = [TrackPoint() for _ in range(36)]  # Initialize 36 track points

class ATCFProcessor:
    def __init__(self):
        self.num_fcst = 0
        self.fcst = []
        self.num_carq = 0
        self.carq = []

    def clear_internal_atcf(self):
        self.num_fcst = 0
        self.fcst = []
        self.num_carq = 0
        self.carq = []

    def djuliana(self, mm: int, dd: int, yy: int, hh: float) -> float:
        """Convert date to Julian day (simplified version)"""
        # Note: This is a simplified version. For precise calculations, use a proper Julian date function
        return float(datetime(yy, mm, dd).toordinal()) + hh / 24.0

    def match_atcf_id(self, fix_lat: float, fix_lon: float, yy: int, mm: int, dd: int, hh: int, atcfid: str, found: bool):
        """Match ATCF ID (simplified version)"""
        # In the original Fortran, this would match against existing ATCF records
        # Here we just pass through the atcfid
        pass

    def get_atcf_records(self, atfile: str, tech: str):
        """Load ATCF records from file (simplified version)"""
        # In a full implementation, this would parse the ATCF file
        pass

    def sort_carq_records(self):
        """Sort CARQ records (placeholder)"""
        pass

    def write_carq_record(self, index: int):
        """Write CARQ record (placeholder)"""
        pass

    def sort_fcst_records(self):
        """Sort forecast records (placeholder)"""
        pass

    def write_fcst_record(self, index: int):
        """Write forecast record (placeholder)"""
        pass

def main():
    processor = ATCFProcessor()
    
    print("\nChina Met Agency/Guangzhou Bulletin to ATCF Track File Version 1.0")
    print("Copyright(c) 2023, Charles C Watson Jr.  All Rights Reserved.\n")

    # Parse command line arguments
    infile = ""
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith("-in"):
            if i + 1 < len(sys.argv[1:]):
                infile = sys.argv[i + 2]

    if not infile:
        print("Error: No input file specified")
        sys.exit(1)

    if not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!")
        sys.exit(1)

    print(f"Reading {infile}")

    current_time = datetime.now()
    yy = current_time.year
    mm = current_time.month
    dd = current_time.day
    hh = current_time.hour

    with open(infile, 'r') as f:
        while True:
            # Find WHCI line
            while True:
                buffy = f.readline().strip()
                if not buffy:
                    break  # EOF
                if "WHCI" in buffy:
                    break
            else:
                break  # EOF reached

            wmohdr = buffy[:18]
            print(wmohdr)

            # Process the bulletin
            tlat = 0.0
            tlon = 0.0
            vmax = 0
            atcfid = ""
            
            while True:
                buffy = f.readline().strip()
                if not buffy:
                    break  # EOF

                if 'AT ' in buffy:
                    print(buffy)
                    # Parse date/time information
                    parts = buffy.split()
                    dd = int(parts[1])
                    hh = int(parts[2])
                    yy1 = int(parts[3])
                    sn1 = int(parts[4])
                    atcfid = f"WP{sn1:02d}{20}{yy1:02d}"
                    
                    while True:
                        buffy = f.readline().strip()
                        if not buffy:
                            break
                        print(buffy)
                        
                        if 'FCST' in buffy:
                            break
                        if buffy.startswith('NEAR'):
                            if 'R' in buffy:
                                iz = buffy.index('R') + 1
                                tlat = float(buffy[iz:].split()[0])
                            if 'H' in buffy:
                                iz = buffy.index('H') + 1
                                tlon = float(buffy[iz:].split()[0])
                            if 'SOUTH' in buffy:
                                tlat = -tlat
                        if 'MAX WINDS' in buffy:
                            vmax = int(buffy[10:].split()[0])
                    break

            if dd > current_time.day:
                mm -= 1

            print(yy, mm, dd, hh)
            print(tlat, tlon, vmax)
            fix_lat = tlat
            fix_lon = tlon

            jdnow = processor.djuliana(mm, dd, yy, hh * 1.0)
            print(atcfid, yy, mm, dd, hh)
            found = False
            processor.match_atcf_id(fix_lat, fix_lon, yy, mm, dd, hh, atcfid, found)
            print(atcfid, yy, mm, dd, hh)

            atfile = f"A{atcfid}.bcgz"
            if not os.path.exists(atfile):
                print(f"*Caution* {atfile} does not exist!")
                processor.num_fcst = 0
            else:
                processor.clear_internal_atcf()
                processor.get_atcf_records(atfile, 'ANY ')

            jdmsg = processor.djuliana(mm, dd, yy, hh * 1.0)

            # Check if forecast already exists
            found = False
            for fcst in processor.fcst:
                if fcst.tech == 'BCGZ' and abs(fcst.jdnow - jdmsg) < 1.0 / 24:
                    found = True
                    break

            if found:
                print("Forecast already in ATCF file")
                continue

            # Create new forecast record
            new_fcst = Forecast()
            processor.num_fcst += 1
            new_fcst.basin = atcfid[:2]
            new_fcst.cyNum = int(atcfid[2:4])
            new_fcst.DTG = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
            new_fcst.jdnow = jdmsg
            new_fcst.technum = 1
            new_fcst.tech = 'BCGZ'
            new_fcst.stormname = ''

            # Add initial position
            numfpos = 0
            new_fcst.track[numfpos].tau = 0
            new_fcst.track[numfpos].lat = fix_lat
            new_fcst.track[numfpos].lon = fix_lon
            new_fcst.track[numfpos].vmax = vmax
            new_fcst.track[numfpos].mslp = 0  # mslp not set in original
            new_fcst.track[numfpos].mrd = 0   # rmax not set in original

            # Process forecast positions
            while True:
                if 'FCST' not in buffy:
                    buffy = f.readline()
                    if not buffy:
                        break
                    continue

                # Parse forecast data
                parts = buffy.split()
                vt = int(parts[1])
                
                buffy = f.readline()
                if not buffy:
                    break
                
                if 'R' in buffy:
                    iz = buffy.index('R') + 1
                    tlat = float(buffy[iz:].split()[0])
                if 'H' in buffy:
                    iz = buffy.index('H') + 1
                    tlon = float(buffy[iz:].split()[0])
                if 'SOUTH' in buffy:
                    tlat = -tlat
                
                buffy = f.readline()
                if not buffy:
                    break
                
                ivmax = int(buffy[10:].split()[0])

                numfpos += 1
                new_fcst.track[numfpos].tau = vt
                new_fcst.track[numfpos].lat = tlat
                new_fcst.track[numfpos].lon = tlon
                new_fcst.track[numfpos].vmax = ivmax
                print(vt, tlat, tlon, ivmax)

            processor.fcst.append(new_fcst)

            # Write output file
            with open(atfile, 'w') as atf:
                # In a full implementation, this would write all records
                processor.sort_carq_records()
                for i in range(processor.num_carq):
                    processor.write_carq_record(i)

                processor.sort_fcst_records()
                for i in range(processor.num_fcst):
                    processor.write_fcst_record(i)

            print(f"Updated {atcfid} ATCF file.")
            
            with open('bcgz_updated.dat', 'a') as sqlf:
                sqlf.write(f"{atcfid}\n")

if __name__ == "__main__":
    main()
