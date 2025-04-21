# Converted from abom_module in Fortran

# Constants from the module
JMV_HDR_FMT = "(I4,I2,I2,I2,x,I2,A1,x,A10,x,I3,2x,I2,x,I3,x,I2,x,A4,x,I4)"
JMV_FST_FMT = "(X,I3,x,I3,A1,x,I4,A1,x,I3)"
JMV_PO1_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,x,I3,A1,x,I3)"
JMV_PO2_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,I4,A1,x,I3)"

UINP = 200
USQL = 201

SCAN_HDR = 0
SCAN_FST = 1
SCAN_POS = 2

# Shared state
scan_mode = None
inbuffy = ""

import sys
import os
import re
from datetime import datetime


positions = []


def parse_jmv_hdr(line):
    match = re.match(r"\s*(\d{4})(\d{2})(\d{2})(\d{2})\s+(\d{2})([NS])\s+(\w{1,10})\s+(\d{3})\s+(\d{2})\s+(\d{3})\s+(\d{2})\s+(\w{1,4})\s+(\d{4})", line)
    if match:
        return match.groups()
    return None


def parse_jmv_fst(line):
    match = re.match(r"\s*(\d{3})\s+(\d{3})([EW])\s+(\d{4})([ ]?)\s+(\d{3})", line)
    if match:
        return match.groups()
    return None


def parse_jmv_pos(line):
    match = re.match(r"\s*(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\s+(\d{3})([NS])\s+(\d{3})([EW])\s+(\d{3})", line)
    if match:
        return match.groups()
    return None


def format_atcf_record(yy, mm, dd, hh, lat, ns, lon, ew, vmax, atcfid):
    lat_str = f"{lat:03d}{ns}"
    lon_str = f"{lon:04d}{ew}"
    dtg = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
    return f"{atcfid}, {dtg}, 0, {lat_str}, {lon_str}, {vmax:03d}, , , , , , , , , , , ,"


def main():
    print("\nABOM Technical Message to ATCF Track File Version 1.1")
    print("(BuildData placeholder)")
    print("(CopyrightData placeholder)")
    print()

    numpos = 0
    numfpos = 0
    atcfid = ""  # Will be extracted from header later

    # Parse command-line arguments
    infile = ""
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg.startswith("-in") and i + 1 < len(args):
            infile = args[i + 1]

    if not infile:
        print("Error: No input file specified with '-in <filename>'.")
        sys.exit(1)

    if not os.path.exists(infile):
        print(f"Error: File '{infile}' not found.")
        sys.exit(1)

    try:
        with open(infile, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file '{infile}': {e}")
        sys.exit(1)

    scan_mode = SCAN_HDR

    for lineno, line in enumerate(lines, 1):
        inbuffy = line.strip()

        try:
            if scan_mode == SCAN_HDR:
                result = parse_jmv_hdr(inbuffy)
                if result:
                    print(f"Parsed Header: {result}")
                    yy, mm, dd, hh = map(int, result[:4])
                    atcfid = result[11]  # bomid
                    scan_mode = SCAN_FST
                else:
                    print(f"[Line {lineno}] Failed to parse header: {inbuffy}")

            elif scan_mode == SCAN_FST:
                result = parse_jmv_fst(inbuffy)
                if result:
                    print(f"Parsed First Fix: {result}")
                    scan_mode = SCAN_POS
                else:
                    print(f"[Line {lineno}] Failed to parse first fix: {inbuffy}")

            elif scan_mode == SCAN_POS:
                result = parse_jmv_pos(inbuffy)
                if result:
                    print(f"Parsed Position Fix: {result}")
                    y, mo, d, h, _, lat, ns, lon, ew, vmax = result
                    positions.append({
                        "yy": int(y),
                        "mm": int(mo),
                        "dd": int(d),
                        "hh": int(h),
                        "lat": int(lat),
                        "ns": ns,
                        "lon": int(lon),
                        "ew": ew,
                        "vmax": int(vmax)
                    })
                else:
                    print(f"[Line {lineno}] Failed to parse position fix: {inbuffy}")
        except Exception as parse_err:
            print(f"[Line {lineno}] Unexpected error: {parse_err}")

    if not atcfid:
        print("Error: No valid ATCF ID (bomid) found in input file.")
        sys.exit(1)

    if not positions:
        print("Warning: No position records were successfully parsed.")

    print("\nConverted ATCF Records:")
    output_filename = f"{atcfid}.dat"

    try:
        with open(output_filename, "w") as outf:
            for pos in positions:
                rec = format_atcf_record(pos['yy'], pos['mm'], pos['dd'], pos['hh'], pos['lat'], pos['ns'], pos['lon'], pos['ew'], pos['vmax'], atcfid)
                print(rec)
                outf.write(rec + "\n")
        print(f"\nOutput written to '{output_filename}'")
    except Exception as out_err:
        print(f"Error writing to file '{output_filename}': {out_err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
