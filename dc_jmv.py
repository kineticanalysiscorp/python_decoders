import os
import sys
import re
from datetime import datetime
import math

# Constants and parameters from jmv_module
JMV_HDR_FMT = "(I4,I2,I2,I2,x,I2,A1,x,A10,x,I3,2x,I2,x,I3,x,I2,x,A4,x,I4)"
JMV_HDR_SHT = "(I4,I2,I2,I2,x,I2,A1)"
JMV_FST_FMT = "(X,I3,x,I3,A1,x,I4,A1,x,I3)"
JMV_PO1_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,x,I3,A1,x,I3)"
JMV_PO2_FMT = "(I2,I2,I2,I2,I2,x,I3,A1,I4,A1,x,I3)"

UINP = 200
USQL = 201

SCAN_HDR = 0
SCAN_FST = 1
SCAN_POS = 2
scan_mode = SCAN_HDR

# Data structures to replace Fortran records
class ForecastTrack:
    def __init__(self):
        self.lat = -999.0
        self.lon = -999.0
        self.vmax = -999
        self.tau = -999
        self.ty = '  '
        self.windrad = ['AAA'] * 4  # Assuming 4 wind radii

class ForecastRecord:
    def __init__(self):
        self.basin = ''
        self.cyNum = 0
        self.DTG = ''
        self.jdnow = 0.0
        self.technum = 0
        self.tech = ''
        self.stormname = ''
        self.track = [ForecastTrack() for _ in range(36)]  # 36 track positions

# Global variables to replace Fortran common blocks
num_fcst = 0
fcst = [ForecastRecord() for _ in range(1000)]  # Assuming max 1000 forecasts
num_carq = 0
carq = []  # Not fully implemented in this conversion
inbuffy = ''
builddata = "Build information not available"
copyrightdata = "Copyright information not available"

def djuliana(mm, dd, yy, hh):
    """Convert date to Julian day"""
    if yy < 100:
        if yy > 50:
            yy += 1900
        else:
            yy += 2000
    
    dt = datetime(yy, mm, dd) + timedelta(hours=hh)
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    return jd

def clear_internal_atcf():
    """Clear internal ATCF records"""
    global num_fcst, fcst, num_carq, carq
    num_fcst = 0
    fcst = [ForecastRecord() for _ in range(1000)]
    num_carq = 0
    carq = []

def get_atcf_records(atfile, tech_filter):
    """Load ATCF records from file"""
    # Implementation would read the ATCF file and populate fcst and carq arrays
    pass

def sort_carq_records():
    """Sort CARQ records"""
    # Implementation would sort carq array
    pass

def write_carq_record(i):
    """Write CARQ record to file"""
    # Implementation would write carq record
    pass

def sort_fcst_records():
    """Sort forecast records"""
    # Implementation would sort fcst array by date
    pass

def write_fcst_record(i):
    """Write forecast record to file"""
    record = fcst[i]
    with open(atfile, 'a') as f:
        # Write the record in ATCF format
        # This is a simplified version - actual implementation would match ATCF specs
        for track in record.track:
            if track.lat != -999:
                line = f"{record.basin}, {record.cyNum:02d}, {record.DTG}, {record.tech}, "
                line += f"{track.tau:03d}, {track.lat:.1f}N, {abs(track.lon):.1f}W, "
                line += f"{track.vmax:03d}\n"
                f.write(line)

def write_fcst_sqlrecord(i, sqlfile, source):
    """Write forecast record to SQL file"""
    # Implementation would write SQL INSERT statements
    pass

def getline(fileobj):
    """Read a line from file and clean it"""
    global inbuffy
    line = fileobj.readline()
    if not line:
        return 1  # EOF
    
    # Clean the line
    cleaned = []
    for c in line:
        if ord(c) < 32 or ord(c) == 127:
            cleaned.append(' ')
        elif c == "'":
            cleaned.append('*')
        else:
            cleaned.append(c)
    
    inbuffy = ''.join(cleaned).strip()
    return 0

def parse_jmv_hdr_sht(line):
    """Parse short JMV header format"""
    # Format: (I4,I2,I2,I2,x,I2,A1)
    try:
        yy = int(line[0:4])
        mm = int(line[4:6])
        dd = int(line[6:8])
        hh = int(line[8:10])
        inum = int(line[11:13])
        bchar = line[13]
        return yy, mm, dd, hh, inum, bchar, 0
    except:
        return None

def parse_jmv_fst_fmt(line):
    """Parse forecast format"""
    # Format: (X,I3,x,I3,A1,x,I4,A1,x,I3)
    try:
        parts = line.split()
        vt = int(parts[0])
        ilat = int(parts[1][:-1])
        ns = parts[1][-1]
        ilon = int(parts[2][:-1])
        ew = parts[2][-1]
        ivmax = int(parts[3])
        return vt, ilat, ns, ilon, ew, ivmax
    except:
        return None

def parse_jmv_po1_fmt(line):
    """Parse position format 1"""
    # Format: (I2,I2,I2,I2,I2,x,I3,A1,x,I3,A1,x,I3)
    try:
        is2 = int(line[0:2])
        yy = int(line[2:4])
        mm = int(line[4:6])
        dd = int(line[6:8])
        hh = int(line[8:10])
        
        rest = line[11:].split()
        ilat = int(rest[0][:-1])
        ns = rest[0][-1]
        ilon = int(rest[1][:-1])
        ew = rest[1][-1]
        ivmax = int(rest[2])
        return is2, yy, mm, dd, hh, ilat, ns, ilon, ew, ivmax
    except:
        return None

def parse_jmv_po2_fmt(line):
    """Parse position format 2"""
    # Format: (I2,I2,I2,I2,I2,x,I3,A1,I4,A1,x,I3)
    try:
        is2 = int(line[0:2])
        yy = int(line[2:4])
        mm = int(line[4:6])
        dd = int(line[6:8])
        hh = int(line[8:10])
        
        rest = line[11:].split()
        ilat = int(rest[0][:-1])
        ns = rest[0][-1]
        ilon = int(rest[1][:-1])
        ew = rest[1][-1]
        ivmax = int(rest[2])
        return is2, yy, mm, dd, hh, ilat, ns, ilon, ew, ivmax
    except:
        return None

def main():
    global scan_mode, num_fcst, fcst, inbuffy, atfile
    
    print("\nJTWC JMV format to ATCF")
    print(builddata)
    print(copyrightdata)
    print()
    
    basin = 'XX'
    atcfid = 'XX999999'
    atfile = 'badfile.dat'
    numpos = 0
    numfpos = 0
    source = 'JMV_DECODE'
    infile = ''
    
    # Parse command line arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-in":
            infile = args[i+1]
            i += 1
        elif args[i] == "-source":
            source = args[i+1]
            i += 1
        i += 1
    
    mvmt = 'NA'
    mslp = 0
    iadv = 0
    
    if not os.path.exists(infile):
        print(f"*Error* {infile} does not exist!")
        sys.exit(1)
    
    print(f"Reading {infile}")
    
    scan_mode = SCAN_HDR
    wmohdr = 'NOT FOUND'
    yy0 = mm0 = dd0 = hh0 = 0
    fix_lat = fix_lon = 0.0
    vmax = 0
    
    with open(infile, 'r') as f:
        for line in f:
            buffy = line.strip()
            
            if buffy.startswith('WT'):
                wmohdr = buffy[:18]
            if (buffy.startswith('//') or buffy.startswith('AMP')) and scan_mode != SCAN_HDR:
                scan_mode = SCAN_POS
            if len(buffy) < 2:
                continue
            if 'MOVEMENT' in buffy:
                mvmt = buffy
            
            if buffy.startswith('ALERT'):
                sname = 'INVEST'
                try:
                    inum = int(buffy[20:22])
                except:
                    inum = 0
                scan_mode = SCAN_POS
                
                # Read next line for date
                buffy = next(f).strip()
                try:
                    yy = int(buffy[0:4])
                    mm = int(buffy[4:6])
                    dd = int(buffy[6:8])
                    hh = int(buffy[8:10])
                except:
                    print("bad dtg in header line 2")
                    sys.exit(1)
                
                # Find PGTW line
                while True:
                    buffy = next(f).strip()
                    if 'PGTW' in buffy:
                        break
                
                basin = 'WP'
                if 'IO' in buffy[2:4]:
                    basin = 'WP'
                if 'PS' in buffy[2:4]:
                    basin = 'SH'
                if 'XS' in buffy[2:4]:
                    basin = 'SH'
                
                yyb = yy
                if basin in ["SP", "SH"]:
                    if mm >= 7:
                        yyb += 1
                
                atcfid = f"{basin}{inum:02d}{yyb:04d}"
                atfile = f"A{atcfid}.DAT"
                print(f"atfile: {atfile}")
                
                if not os.path.exists(atfile):
                    print(f"*Caution* {atfile} does not exist!")
                    num_fcst = 0
                else:
                    clear_internal_atcf()
                    get_atcf_records(atfile, 'ANY ')
                
                jdmsg = djuliana(mm, dd, yy, hh)
                found = False
            
            if scan_mode == SCAN_HDR:
                if len(buffy) < 25:
                    continue
                
                # Try to parse short header format
                header_data = parse_jmv_hdr_sht(buffy)
                if header_data is None:
                    continue
                
                yy, mm, dd, hh, inum, bchar, _ = header_data
                iadv = 0
                
                # Try to parse storm name
                sname = buffy[15:].split()[0][:10]
                
                # Try to parse advisory number
                try:
                    iadv = int(buffy[26:29])
                except:
                    iadv = 0
                
                print(f"iadv: {iadv}")
                scan_mode = SCAN_FST
                print(f"found header: {buffy[:30]}")
                
                basin = 'XX'
                if bchar == 'B':
                    basin = 'IO'
                elif bchar == 'S':
                    basin = 'SH'
                elif bchar == 'P':
                    basin = 'SH'
                elif bchar == 'W':
                    basin = 'WP'
                elif bchar == 'A':
                    basin = 'IO'
                elif bchar == 'C':
                    basin = 'CP'
                elif bchar == 'E':
                    basin = 'EP'
                
                if basin == 'XX':
                    print("Bad Basin")
                    sys.exit(1)
                
                yyb = yy
                if basin in ["SP", "SH"]:
                    if mm >= 9:
                        yyb += 1
                
                atcfid = f"{basin}{inum:02d}{yyb:04d}"
                atfile = f"A{atcfid}.DAT"
                print(f"atfile: {atfile}")
                
                if not os.path.exists(atfile):
                    print(f"*Caution* {atfile} does not exist!")
                    num_fcst = 0
                else:
                    clear_internal_atcf()
                    get_atcf_records(atfile, 'ANY ')
                
                jdmsg = djuliana(mm, dd, yy, hh)
                found = False
                
                for i in range(num_fcst):
                    if fcst[i].tech == 'JTWC' and abs(fcst[i].jdnow - jdmsg) < 1.0/24:
                        found = True
                
                if found:
                    scan_mode = SCAN_POS
                    sys.exit(0)
                
                num_fcst += 1
                fcst[num_fcst-1].basin = basin
                fcst[num_fcst-1].cyNum = inum
                fcst[num_fcst-1].DTG = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
                fcst[num_fcst-1].jdnow = jdmsg
                fcst[num_fcst-1].technum = 1
                fcst[num_fcst-1].tech = 'JTWC'
                fcst[num_fcst-1].stormname = sname
                
                for i in range(36):
                    fcst[num_fcst-1].track[i].lat = -999
                    fcst[num_fcst-1].track[i].ty = '  '
                    for j in range(4):
                        fcst[num_fcst-1].track[i].windrad[j] = 'AAA'
            
            elif scan_mode == SCAN_FST:
                if buffy.startswith('T'):
                    forecast_data = parse_jmv_fst_fmt(buffy)
                    if forecast_data is not None:
                        vt, ilat, ns, ilon, ew, ivmax = forecast_data
                        numfpos += 1
                        fcst[num_fcst-1].track[numfpos-1].tau = vt
                        
                        tlat = ilat / 10.0
                        tlon = ilon / 10.0
                        if ns == 'S':
                            tlat = -tlat
                        if ew == 'W':
                            tlon = -tlon
                        
                        fcst[num_fcst-1].track[numfpos-1].lat = tlat
                        fcst[num_fcst-1].track[numfpos-1].lon = tlon
                        fcst[num_fcst-1].track[numfpos-1].vmax = ivmax
                        
                        if vt == 0:
                            fix_lat = tlat
                            fix_lon = tlon
                            vmax = ivmax
                            yy0 = yy
                            mm0 = mm
                            dd0 = dd
                            hh0 = hh
            
            elif scan_mode == SCAN_POS:
                pos_data = parse_jmv_po2_fmt(buffy)
                if pos_data is None:
                    pos_data = parse_jmv_po1_fmt(buffy)
                
                if pos_data is not None:
                    is2, yy, mm, dd, hh, ilat, ns, ilon, ew, ivmax = pos_data
                    yy += 2000
                    if yy == 2000:
                        continue
                    
                    jdmsg = djuliana(mm, dd, yy, hh)
                    found = False
                    
                    for i in range(num_fcst):
                        if fcst[i].tech == 'JTWC' and abs(fcst[i].jdnow - jdmsg) < 1.0/24:
                            found = True
                    
                    if not found:
                        num_fcst += 1
                        fcst[num_fcst-1].basin = basin
                        fcst[num_fcst-1].cyNum = inum
                        fcst[num_fcst-1].DTG = f"{yy:04d}{mm:02d}{dd:02d}{hh:02d}"
                        fcst[num_fcst-1].jdnow = jdmsg
                        fcst[num_fcst-1].technum = 0
                        fcst[num_fcst-1].tech = 'JTWC'
                        fcst[num_fcst-1].stormname = sname
                        
                        for i in range(36):
                            fcst[num_fcst-1].track[i].lat = -999
                            for j in range(4):
                                fcst[num_fcst-1].track[i].windrad[j] = ' '
                            fcst[num_fcst-1].track[i].ty = '  '
                        
                        numfpos = 1
                        fcst[num_fcst-1].track[numfpos-1].tau = 0
                        
                        tlat = ilat / 10.0
                        tlon = ilon / 10.0
                        if ns == 'S':
                            tlat = -tlat
                        if ew == 'W':
                            tlon = -tlon
                        
                        fcst[num_fcst-1].track[numfpos-1].lat = tlat
                        fcst[num_fcst-1].track[numfpos-1].lon = tlon
                        fcst[num_fcst-1].track[numfpos-1].vmax = ivmax
                        
                        for j in range(4):
                            fcst[num_fcst-1].track[i].windrad[j] = 'AAA'
    
    # Write output files
    with open(atfile, 'w') as f:
        sort_carq_records()
        for i in range(num_carq):
            write_carq_record(i)
        
        sort_fcst_records()
        for i in range(num_fcst):
            write_fcst_record(i)
    
    print(f"Updated {atcfid} ATCF file.")
    
    with open('jmv_updated.dat', 'a') as f:
        f.write(f"{atcfid}\n")
    
    # Write SQL files
    with open("rsfc_messages_table.sql", 'w') as f:
        f.write("drop table rsfc_messages;\n")
        f.write("create table rsfc_messages (\n")
        f.write(" atcfid char(8),\n")
        f.write(" msg_hdr char(18),\n")
        f.write(" msg_type char(10),\n")
        f.write(" msg_advnr int,\n")
        f.write(" msg_time timestamp,\n")
        f.write(" fcst_time timestamp,\n")
        f.write(" message text,\n")
        f.write(" lat real,\n")
        f.write(" lon real,\n")
        f.write(" vmax int,\n")
        f.write(" mslp int,\n")
        f.write(" movement varchar(40)\n")
        f.write(");\n")
        f.write(f"SELECT AddGeometryColumn ('public', 'rsfc_messages', 'geom', 4326, 'POINT', 2);\n")
    
    try:
        hh1 = int(wmohdr[13:15])
    except:
        hh1 = 0
    
    sql_filename = f"{atcfid}_message.sql"
    with open(sql_filename, 'w') as f:
        f.write("INSERT INTO rsfc_messages (atcfid,msg_hdr,msg_type,msg_advnr,msg_time,fcst_time,lat,lon,vmax,mslp,movement,message,geom) VALUES(\n")
        f.write(f"    '{atcfid}',\n")
        f.write(f"    '{wmohdr.strip()}',\n")
        f.write(f"    'FORECAST',\n")
        f.write(f"    {iadv:5d},\n")
        f.write(f"    '{yy0:04d}-{mm0:02d}-{dd0:02d} {hh1:02d}:00',\n")
        f.write(f"    '{yy0:04d}-{mm0:02d}-{dd0:02d} {hh0:02d}:00',\n")
        f.write(f"    {fix_lat:10.5f},\n")
        f.write(f"    {fix_lon:10.5f},\n")
        f.write(f"    {vmax:5d},\n")
        f.write(f"    {mslp:5d},\n")
        f.write(f"    '{mvmt.strip()}',\n")
        f.write("''\n")
        
        with open(infile, 'r') as inf:
            while True:
                line = inf.readline()
                if not line:
                    break
                cleaned = line.strip().replace("'", "*")
                f.write(cleaned + "\n")
                if line.startswith('//'):
                    break
        
        f.write("',\n")
        f.write(f"    ST_GeomFromText('POINT({fix_lon:12.6} {fix_lat:12.6})',4326));\n")

if __name__ == "__main__":
    main()
