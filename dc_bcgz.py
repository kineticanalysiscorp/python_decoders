import os
from datetime import datetime
import sys

def julian_date(month, day, year, hour):
    """Calculate Julian date."""
    dt = datetime(year, month, day, int(hour))
    return dt.toordinal() + 1721424.5 + (hour % 1)

def main():
    print("\nChina Met Agency/Guangzhou Bulletin to ATCF Track File Version 1.0")
    print("Copyright(c) 2023, Charles C Watson Jr.  All Rights Reserved.\n")

    # Initialize variables
    numpos = 0
    numfpos = 0
    mvmt = 'NA'
    rmax = 0
    vmax = 0
    mslp = 0
    infile = None

    # Parse command-line arguments
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg.startswith("-in") and i + 1 < len(args):
            infile = args[i + 1]

    if not infile or not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!")
        sys.exit(1)

    print(f"Reading {infile}")
    with open(infile, 'r') as f:
        lines = f.readlines()

    # Process input file
    wmohdr = None
    for line in lines:
        if "WHCI" in line:
            wmohdr = line[:18].strip()
            print(wmohdr)
            break

    if not wmohdr:
        print("*Error* WHCI header not found!")
        sys.exit(1)

    for line in lines:
        if "AT " in line:
            print(line.strip())
            dd, hh, yy1, sn1 = map(int, [line[3:5], line[5:7], line[12:14], line[14:16]])
            atcfid = f"WP{sn1:02d}20{yy1:02d}"
            break

    # Extract forecast data
    fix_lat, fix_lon = None, None
    for line in lines:
        if "NEAR" in line:
            tlat = float(line[line.index('R') + 1:].split()[0])
            tlon = float(line[line.index('H') + 1:].split()[0])
            if "SOUTH" in line:
                tlat = -tlat
            fix_lat, fix_lon = tlat, tlon
        if "MAX WINDS" in line:
            vmax = int(line[10:].strip())
            break

    if not fix_lat or not fix_lon:
        print("*Error* Fix latitude/longitude not found!")
        sys.exit(1)

    # Calculate Julian date
    now = datetime.now()
    yy, mm = now.year, now.month
    if dd > now.day:
        mm -= 1
    jdnow = julian_date(mm, dd, yy, hh)

    print(yy, mm, dd, hh)
    print(fix_lat, fix_lon, vmax)
    print(atcfid, yy, mm, dd, hh)

    # Check and update ATCF file
    atfile = f"A{atcfid}.bcgz"
    if not os.path.exists(atfile):
        print(f"*Caution* {atfile} does not exist!")
        num_fcst = 0
    else:
        # Simulate loading ATCF records
        print(f"Loading {atfile}")
        num_fcst = 1  # Placeholder for actual record count

    jdmsg = julian_date(mm, dd, yy, hh)
    found = False
    for i in range(num_fcst):
        # Simulate checking forecast records
        if False:  # Replace with actual condition
            found = True

    if found:
        print("Forecast already in ATCF file")
        return

    # Simulate updating forecast records
    num_fcst += 1
    print(f"Updated {atcfid} ATCF file.")

    # Append to SQL file
    with open('bcgz_updated.dat', 'a') as f:
        f.write(f"{atcfid}\n")

if __name__ == "__main__":
    main()
