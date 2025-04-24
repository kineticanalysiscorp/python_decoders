import os
import re
from datetime import datetime
import math

class TPCAdvisoryParser:
    def __init__(self):
        self.UINP = 200
        self.USQL = 201
        self.scan_mode = 0
        self.SCAN_HDR = 0
        self.SCAN_FST = 1
        self.SCAN_POS = 2
        self.inbuffy = ""
        self.infile = ""
        self.atfile = ""
        
        # ATCF module data structures
        self.fcst = []
        self.num_fcst = 0
        self.num_carq = 0
        self.UnitAT = 202
        
        # Month abbreviations to numbers
        self.month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
    def clear_internal_atcf(self):
        """Clear internal ATCF data structures"""
        self.fcst = []
        self.num_fcst = 0
        self.num_carq = 0
    
    def djuliana(self, month, day, year, hour):
        """Convert date to Julian day"""
        # Simplified version - for precise calculation consider using datetime or specialized libraries
        dt = datetime(year, month, day, int(hour), int((hour % 1) * 60))
        return dt.timestamp() / 86400.0 + 2440587.5  # Unix epoch to Julian day
    
    def getline(self, file_handle):
        """Read a line from input file and clean it"""
        line = file_handle.readline()
        if not line:
            return 1  # EOF
        
        # Clean the line
        cleaned = []
        for c in line[:255]:
            ord_c = ord(c)
            if ord_c < 32 or ord_c == 127:
                cleaned.append(' ')
            elif c == "'":
                cleaned.append('*')
            else:
                cleaned.append(c)
        
        self.inbuffy = ''.join(cleaned).strip()
        return 0
    
    def parse_nhc_marine(self):
        """Parse NHC Marine advisory message"""
        wmohdr = self.inbuffy[:18]
        name = ""
        advnr = 0
        atcfid = ""
        basin = ""
        inum = 0
        mo = dd = yy = hh = hh1 = 0
        fix_lat = fix_lon = fc_lat = fc_lon = fc_vmax = 0.0
        vmax = mslp = vt = 0
        mvmt = ""
        valid = False
        found = False
        
        print(f"Marine Message ID: {wmohdr}")
        
        # Find header line and read name
        with open(self.infile, 'r') as fin:
            while True:
                line = fin.readline()
                if not line:
                    return
                
                iza = line.find("FORECAST/ADVISORY")
                if iza != -1:
                    try:
                        advnr = int(line[iza+25:iza+28].strip())
                    except ValueError:
                        advnr = 0
                    
                    if "SPECIAL" in line:
                        iza = line.find("SPECIAL")
                    if "INTERMEDIATE" in line:
                        iza = line.find("INTERMEDIATE")
                    
                    izb = iza - 1
                    while izb > 0 and line[izb] == ' ':
                        izb -= 1
                    
                    idx = izb - 1
                    while idx > 0 and line[idx] != ' ':
                        idx -= 1
                    
                    name = line[idx+1:izb+1].strip()
                    break
        
        print(f"{name} {advnr}")
        
        # Read ATCF ID
        with open(self.infile, 'r') as fin:
            self.getline(fin)
            line = self.inbuffy
            item = line[-10:-8].strip()
            try:
                ival = int(line[-8:-6])
                iyear = int(line[-6:-2])
            except ValueError:
                ival = iyear = 0
            
            if not item:
                idx = line.find(" AL") + 1
                if idx == 0:
                    idx = line.find(" EP") + 1
                if idx == 0:
                    idx = line.find(" CP") + 1
                
                if idx > 0:
                    item = line[idx:idx+2]
                    try:
                        ival = int(line[idx+2:idx+4])
                        iyear = int(line[idx+4:idx+8])
                    except ValueError:
                        return
                
                atcfid = f"{item}{ival:02d}{iyear:04d}"
            else:
                atcfid = f"{item}{ival:02d}{iyear:04d}"
        
        print(f"atcfid: {atcfid} {item} {iyear}")
        basin = atcfid[:2]
        inum = ival
        
        # Read date and time
        with open(self.infile, 'r') as fin:
            self.getline(fin)
            line = self.inbuffy
            if "ISSUED" in line:
                self.getline(fin)
                line = self.inbuffy
            
            try:
                # Try different formats to parse the date
                parts = line.split()
                hh = int(parts[0])
                dd = int(parts[2])
                yy = int(parts[3])
            except (IndexError, ValueError):
                return
            
            # Determine month
            mo = -1
            for month_abbr, month_num in self.month_map.items():
                if month_abbr in line:
                    mo = month_num
                    break
            
            if mo < 0:
                return
            
            print(f"Time: {hh} {dd} {mo} {yy}")
            
            # Parse the rest of the message
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    break
                
                if ("FORECASTER" in self.inbuffy or 
                    "NNNN" in self.inbuffy or 
                    "REQUEST FOR" in self.inbuffy):
                    break
                
                if "PRESENT MOVEMENT" in self.inbuffy:
                    if "STATIONARY" in self.inbuffy:
                        mvmt = self.inbuffy[17:].strip()
                    else:
                        mvmt = self.inbuffy[28:].strip()
                
                if "MAX SUSTAINED" in self.inbuffy:
                    try:
                        vmax = int(self.inbuffy[20:].strip())
                    except ValueError:
                        pass
                
                if "MINIMUM CENTRAL PRES" in self.inbuffy:
                    try:
                        mslp = int(self.inbuffy[35:].strip())
                    except ValueError:
                        pass
                
                if "REPEAT...CENTER L" in self.inbuffy:
                    try:
                        parts = self.inbuffy[29:].split()
                        fc_lat = float(parts[0])
                        ns = parts[1]
                        fc_lon = float(parts[2])
                        ew = parts[3]
                        
                        if ns == 'S':
                            fc_lat = -fc_lat
                        if ew == 'W':
                            fc_lon = -fc_lon
                    except (IndexError, ValueError):
                        pass
                
                if "CENTER LOCATED NEAR" in self.inbuffy:
                    idx = self.inbuffy.find("NEAR") + 5
                    try:
                        parts = self.inbuffy[idx:].split()
                        fc_lat = float(parts[0])
                        ns = parts[1]
                        fc_lon = float(parts[2])
                        ew = parts[3]
                        
                        if ns == 'S':
                            fc_lat = -fc_lat
                        if ew == 'W':
                            fc_lon = -fc_lon
                        
                        # Get time
                        idx2 = self.inbuffy.find("/") + 1
                        hh1 = int(self.inbuffy[idx2:idx2+4].strip())
                    except (IndexError, ValueError):
                        pass
                
                if "CENTER WAS LOCATED NEAR" in self.inbuffy:
                    idx = self.inbuffy.find("NEAR") + 5
                    try:
                        parts = self.inbuffy[idx:].split()
                        fix_lat = float(parts[0])
                        ns = parts[1]
                        fix_lon = float(parts[2])
                        ew = parts[3]
                        
                        if ns == 'S':
                            fix_lat = -fix_lat
                        if ew == 'W':
                            fix_lon = -fix_lon
                        
                        # Get time
                        idx2 = self.inbuffy.find("/") + 1
                        hh1 = int(self.inbuffy[idx2:idx2+4].strip())
                    except (IndexError, ValueError):
                        pass
                    break
        
        print(f"hh1: {hh1} {fc_lat} {fc_lon} {fix_lat} {fix_lon}")
        
        jdmsg = self.djuliana(mo, dd, yy, hh1 / 100.0)
        self.atfile = f"A{atcfid}.DAT"
        
        if not os.path.exists(self.atfile):
            print(f"*Caution* {self.atfile} does not exist!")
            self.num_fcst = 0
        else:
            print(f"Loading {self.atfile}")
            self.clear_internal_atcf()
            self.get_atcf_records(self.atfile, 'ANY ')
        
        # Check if this record already exists
        found = False
        for i in range(self.num_fcst):
            if (self.fcst[i]['tech'] == 'OFCL' and 
                abs(self.fcst[i]['jdnow'] - jdmsg) < 1.0 / 24):
                found = True
                break
        
        if found:
            return
        
        # Add new forecast record
        self.num_fcst += 1
        new_fcst = {
            'basin': basin,
            'cyNum': inum,
            'DTG': f"{yy:04d}{mo:02d}{dd:02d}{hh1//100:02d}",
            'jdnow': jdmsg,
            'technum': 1,
            'tech': 'OFCL',
            'stormname': name,
            'track': [
                {'tau': 0, 'lat': fix_lat, 'lon': fix_lon, 'vmax': vmax, 'mslp': mslp},
                {'tau': 3, 'lat': fc_lat, 'lon': fc_lon, 'vmax': vmax, 'mslp': mslp}
            ]
        }
        
        self.fcst.append(new_fcst)
        
        # Parse forecast positions
        vt = 12
        fidx = 2  # First two positions already added
        
        with open(self.infile, 'r') as fin:
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    break
                
                if ("FORECASTER" in self.inbuffy or 
                    "NNNN" in self.inbuffy or 
                    "ADVISORY" in self.inbuffy):
                    break
                
                if "VALID" in self.inbuffy:
                    idx = self.inbuffy.find("Z") + 2
                    try:
                        parts = self.inbuffy[idx:].split()
                        fc_lat = float(parts[0])
                        ns = parts[1]
                        fc_lon = float(parts[2])
                        ew = parts[3]
                        
                        if ns == 'S':
                            fc_lat = -fc_lat
                        if ew == 'W':
                            fc_lon = -fc_lon
                        
                        # Read next line for vmax
                        self.getline(fin)
                        if not self.inbuffy:
                            break
                        
                        fc_vmax = int(self.inbuffy[8:].strip())
                        
                        # Add to track
                        self.fcst[-1]['track'].append({
                            'tau': vt,
                            'lat': fc_lat,
                            'lon': fc_lon,
                            'vmax': fc_vmax
                        })
                        
                        fidx += 1
                        vt += 12
                        if vt == 84:
                            vt = 96
                        if vt == 108:
                            vt = 120
                    except (IndexError, ValueError):
                        pass
                
                self.getline(fin)
                if not self.inbuffy:
                    break
        
        # Write out updated file
        with open(self.atfile, 'w') as fout:
            self.sort_carq_records()
            for i in range(self.num_carq):
                self.write_carq_record(fout, i)
            
            self.sort_fcst_records()
            for i in range(self.num_fcst):
                self.write_fcst_record(fout, i)
        
        # Generate SQL files
        with open("rsfc_messages_table.sql", 'w') as sql:
            sql.write("drop table rsfc_messages;\n")
            sql.write("create table rsfc_messages (\n")
            sql.write(" atcfid char(8),\n")
            sql.write(" msg_hdr char(18),\n")
            sql.write(" msg_type char(10),\n")
            sql.write(" msg_advnr int,\n")
            sql.write(" msg_time timestamp,\n")
            sql.write(" fcst_time timestamp,\n")
            sql.write(" message text,\n")
            sql.write(" lat real,\n") 
            sql.write(" lon real,\n")
            sql.write(" vmax int,\n")
            sql.write(" mslp int,\n")
            sql.write(" movement varchar(40)\n")
            sql.write(");\n")
            sql.write(f"SELECT AddGeometryColumn ('public', 'rsfc_messages', 'geom', 4326, 'POINT', 2);\n")
        
        print(f"Updated {atcfid} ATCF file.")
        
        with open('tpc_updated.dat', 'a') as f:
            f.write(f"{atcfid}\n")
        
        # Second SQL file
        with open("rsfc_messages_table.sql", 'w') as sql:
            sql.write("create table rsfc_messages (\n")
            sql.write(" atcfid char(8),\n")
            sql.write(" msg_hdr char(18),\n")
            sql.write(" msg_type char(10),\n")
            sql.write(" msg_advnr int,\n")
            sql.write(" msg_time timestamp,\n")
            sql.write(" fcst_time timestamp,\n")
            sql.write(" lat real,\n") 
            sql.write(" lon real,\n")
            sql.write(" vmax int,\n")
            sql.write(" mslp int,\n")
            sql.write(" movement varchar(80),\n")
            sql.write(" message text\n")
            sql.write(");\n")
            sql.write(f"SELECT AddGeometryColumn ('public', 'rsfc_messages', 'geom', 4326, 'POINT', 2);\n")
        
        # Message-specific SQL
        fname = f"{atcfid}_message.sql"
        with open(fname, 'w') as sql:
            sql.write("INSERT INTO rsfc_messages (atcfid,msg_hdr,msg_type,msg_advnr,msg_time,fcst_time,lat,lon,vmax,mslp,movement,message,geom) VALUES(\n")
            sql.write(f"    '{atcfid}',\n")
            sql.write(f"    '{wmohdr.strip()}',\n")
            sql.write("    'FORECAST',\n")
            sql.write(f"    {advnr:5d},\n")
            sql.write(f"    '{yy:04d}-{mo:02d}-{dd:02d} {hh//100:02d}:00',\n")
            sql.write(f"    '{yy:04d}-{mo:02d}-{dd:02d} {hh1//100:02d}:00',\n")
            sql.write(f"    {fix_lat:10.5f},\n")
            sql.write(f"    {fix_lon:10.5f},\n")
            sql.write(f"    {vmax:5d},\n")
            sql.write(f"    {mslp:5d},\n")
            sql.write(f"    '{mvmt.strip()}',\n")
            
            # Write message content
            sql.write("''")
            with open(self.infile, 'r') as fin:
                for line in fin:
                    sql.write(line.strip() + "\n")
            sql.write("',\n")
            
            sql.write(f"    ST_GeomFromText('POINT({fix_lon:12.6f} {fix_lat:12.6f})',4326));\n")
    
    def parse_nhc_public(self):
        """Parse NHC Public advisory message"""
        wmohdr = self.inbuffy[:18]
        name = ""
        advnr = 0
        atcfid = ""
        basin = ""
        inum = 0
        mo = dd = yy = hh = hh1 = 0
        fix_lat = fix_lon = 0.0
        vmax = mslp = 0
        mvmt = ""
        mytech = "OFCP"
        
        print(f"Public Message ID: {wmohdr}")
        
        # Find header line and read name
        with open(self.infile, 'r') as fin:
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    return
                
                iza = self.inbuffy.find("ADVISORY")
                if iza != -1:
                    try:
                        advnr = int(self.inbuffy[iza+16:iza+20].strip())
                    except ValueError:
                        advnr = 0
                    
                    if "SPECIAL" in self.inbuffy:
                        iza = self.inbuffy.find("SPECIAL")
                    if "INTERMEDIATE" in self.inbuffy:
                        iza = self.inbuffy.find("INTERMEDIATE")
                    
                    izb = iza - 1
                    while izb > 0 and self.inbuffy[izb] == ' ':
                        izb -= 1
                    
                    idx = izb - 1
                    while idx > 0 and self.inbuffy[idx] != ' ':
                        idx -= 1
                    
                    name = self.inbuffy[idx+1:izb+1].strip()
                    break
        
        # Read ATCF ID
        with open(self.infile, 'r') as fin:
            self.getline(fin)
            line = self.inbuffy
            item = line[-10:-6].strip()
            try:
                iyear = int(line[-6:-2])
            except ValueError:
                iyear = 0
            
            if not item:
                idx = line.find(" AL") + 1
                if idx == 0:
                    idx = line.find(" EP") + 1
                if idx == 0:
                    idx = line.find(" CP") + 1
                
                if idx > 0:
                    item = line[idx:idx+4].strip()
                    try:
                        iyear = int(line[idx+4:idx+8])
                    except ValueError:
                        return
                
                atcfid = f"{item}{iyear:04d}"
            else:
                atcfid = f"{item}{iyear:04d}"
        
        basin = item[:2]
        try:
            inum = int(item[2:4])
        except ValueError:
            inum = 0
        
        # Read date and time
        with open(self.infile, 'r') as fin:
            self.getline(fin)
            line = self.inbuffy
            if "ISSUED" in line:
                self.getline(fin)
                line = self.inbuffy
            
            try:
                # Try different formats to parse the date
                parts = line.split()
                hh = int(parts[0])
                dd = int(parts[2])
                yy = int(parts[3])
            except (IndexError, ValueError):
                # Try discussion format
                try:
                    hh = int(line[:4])
                    parts = line[-7:].split()
                    dd = int(parts[0])
                    yy = int(parts[1])
                except (IndexError, ValueError):
                    return
            
            # Determine month
            mo = -1
            for month_abbr, month_num in self.month_map.items():
                if month_abbr in line:
                    mo = month_num
                    break
            
            if mo < 0:
                return
            
            # Determine timezone offset
            hoff = 400
            if "CDT" in line or "EST" in line:
                hoff = 500
            elif "EDT" in line:
                hoff = 400
            
            hh1 = hh + hoff
            
            if "KWNH" in wmohdr:
                mytech = "OHPC"
            
            # Parse the rest of the message
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    break
                
                if "$$" in self.inbuffy:
                    break
                
                if "LOCATION" in self.inbuffy:
                    try:
                        parts = self.inbuffy[10:].split()
                        fix_lat = float(parts[0])
                        ns = parts[1]
                        fix_lon = float(parts[2])
                        ew = parts[3]
                        
                        if ns == 'S':
                            fix_lat = -fix_lat
                        if ew == 'W':
                            fix_lon = -fix_lon
                    except (IndexError, ValueError):
                        pass
                
                if "MAXIMUM SUS" in self.inbuffy:
                    try:
                        vmax = int(self.inbuffy[26:].strip()) / 1.15
                    except ValueError:
                        pass
                
                if "MINIMUM CENT" in self.inbuffy:
                    try:
                        mslp = int(self.inbuffy[27:].strip())
                    except ValueError:
                        pass
                
                if "PRESENT MOVEMENT" in self.inbuffy:
                    mvmt = self.inbuffy[19:].strip()
                
                if "INITIAL" in self.inbuffy:
                    try:
                        parts = self.inbuffy[8:].split()
                        dd1 = int(parts[0])
                        hh1 = int(parts[1])
                        fix_lat = float(parts[2])
                        ns = parts[3]
                        fix_lon = float(parts[4])
                        ew = parts[5]
                        vmax = int(parts[6])
                        
                        if ns == 'S':
                            fix_lat = -fix_lat
                        if ew == 'W':
                            fix_lon = -fix_lon
                    except (IndexError, ValueError):
                        pass
                    break
        
        jdmsg = self.djuliana(mo, dd, yy, hh1 / 100.0)
        self.atfile = f"A{atcfid}.DAT"
        
        if not os.path.exists(self.atfile):
            print(f"*Caution* {self.atfile} does not exist!")
            self.num_fcst = 0
        else:
            print(f"Loading {self.atfile}")
            self.clear_internal_atcf()
            self.get_atcf_records(self.atfile, 'ANY ')
        
        # Check if this record already exists
        found = False
        for i in range(self.num_fcst):
            if (self.fcst[i]['tech'] == mytech and 
                abs(self.fcst[i]['jdnow'] - jdmsg) < 1.0 / 24):
                found = True
                break
        
        if found:
            return
        
        # Add new forecast record
        self.num_fcst += 1
        new_fcst = {
            'basin': basin,
            'cyNum': inum,
            'DTG': f"{yy:04d}{mo:02d}{dd:02d}{hh1//100:02d}",
            'jdnow': jdmsg - 3.0 / 24.0,
            'technum': 1,
            'tech': mytech,
            'stormname': name,
            'track': [
                {'tau': 3, 'lat': fix_lat, 'lon': fix_lon, 'vmax': vmax, 'mslp': mslp}
            ]
        }
        
        self.fcst.append(new_fcst)
        
        # Parse forecast positions
        fidx = 1  # First position already added
        
        with open(self.infile, 'r') as fin:
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    break
                
                if "HR VT" in self.inbuffy:
                    try:
                        parts = self.inbuffy.split()
                        vt = int(parts[0])
                        dd1 = int(parts[1])
                        hh1 = int(parts[2])
                        fix_lat = float(parts[3])
                        ns = parts[4]
                        fix_lon = float(parts[5])
                        ew = parts[6]
                        vmax = int(parts[7])
                        
                        if ns == 'S':
                            fix_lat = -fix_lat
                        if ew == 'W':
                            fix_lon = -fix_lon
                        
                        # Add to track
                        self.fcst[-1]['track'].append({
                            'tau': vt,
                            'lat': fix_lat,
                            'lon': fix_lon,
                            'vmax': 0,
                            'mslp': 0
                        })
                        
                        fidx += 1
                    except (IndexError, ValueError):
                        pass
        
        # Generate SQL files (similar to marine advisory)
        # ... (omitted for brevity, similar to parse_nhc_marine)
    
    def parse_nhc_discuss(self):
        """Parse NHC Discussion message"""
        wmohdr = self.inbuffy[:18]
        name = ""
        advnr = 0
        atcfid = ""
        basin = ""
        inum = 0
        mo = dd = yy = hh = hh1 = 0
        fix_lat = fix_lon = 0.0
        vmax = mslp = 0
        mvmt = ""
        
        print(f"Discussion Message ID: {wmohdr}")
        
        # Find header line and read name
        with open(self.infile, 'r') as fin:
            while True:
                line = fin.readline()
                if not line:
                    return
                
                iza = line.find("DISCUSSION")
                if iza != -1:
                    try:
                        advnr = int(line[iza+17:iza+21].strip())
                    except ValueError:
                        advnr = 0
                    
                    if "SPECIAL" in line:
                        iza = line.find("SPECIAL")
                    if "INTERMEDIATE" in line:
                        iza = line.find("INTERMEDIATE")
                    
                    izb = iza - 1
                    while izb > 0 and line[izb] == ' ':
                        izb -= 1
                    
                    idx = izb - 1
                    while idx > 0 and line[idx] != ' ':
                        idx -= 1
                    
                    name = line[idx+1:izb+1].strip()
                    break
        
        # Read ATCF ID
        with open(self.infile, 'r') as fin:
            self.getline(fin)
            line = self.inbuffy
            item = line[-10:-6].strip()
            try:
                iyear = int(line[-6:-2])
            except ValueError:
                iyear = 0
            
            if not item:
                idx = line.find(" AL") + 1
                if idx > 0:
                    item = line[idx:idx+4].strip()
                    try:
                        iyear = int(line[idx+4:idx+8])
                    except ValueError:
                        return
                
                atcfid = f"{item}{iyear:04d}"
            else:
                atcfid = f"{item}{iyear:04d}"
        
        basin = item[:2]
        try:
            inum = int(item[2:4])
        except ValueError:
            inum = 0
        
        # Read date and time
        with open(self.infile, 'r') as fin:
            self.getline(fin)
            line = self.inbuffy
            if "ISSUED" in line:
                self.getline(fin)
                line = self.inbuffy
            
            try:
                # Try different formats to parse the date
                parts = line.split()
                hh = int(parts[0])
                dd = int(parts[2])
                yy = int(parts[3])
            except (IndexError, ValueError):
                # Try discussion format
                try:
                    hh = int(line[:4])
                    parts = line[-7:].split()
                    dd = int(parts[0])
                    yy = int(parts[1])
                except (IndexError, ValueError):
                    return
            
            # Determine month
            mo = -1
            for month_abbr, month_num in self.month_map.items():
                if month_abbr in line:
                    mo = month_num
                    break
            
            if mo < 0:
                return
            
            # Parse the rest of the message
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    break
                
                if ("FORECASTER" in self.inbuffy or 
                    "NNNN" in self.inbuffy or 
                    "FORECAST POSITIONS" in self.inbuffy):
                    break
            
            while True:
                self.getline(fin)
                if not self.inbuffy:
                    break
                
                if ("FORECASTER" in self.inbuffy or 
                    "NNNN" in self.inbuffy or 
                    "$$" in self.inbuffy):
                    break
                
                if "INITIAL" in self.inbuffy:
                    try:
                        parts = self.inbuffy[12:].split()
                        dd1 = int(parts[0])
                        hh1 = int(parts[1])
                        fix_lat = float(parts[2])
                        ns = parts[3]
                        fix_lon = float(parts[4])
                        ew = parts[5]
                        vmax = int(parts[6])
                        
                        if ns == 'S':
                            fix_lat = -fix_lat
                        if ew == 'W':
                            fix_lon = -fix_lon
                    except (IndexError, ValueError):
                        pass
        
        jdmsg = self.djuliana(mo, dd, yy, hh1 / 100.0)
        self.atfile = f"A{atcfid}.DAT"
        
        if not os.path.exists(self.atfile):
            print(f"*Caution* {self.atfile} does not exist!")
            self.num_fcst = 0
        else:
            print(f"Loading {self.atfile}")
            self.clear_internal_atcf()
            self.get_atcf_records(self.atfile, 'ANY ')
        
        # Check if this record already exists
        found = False
        for i in range(self.num_fcst):
            if (self.fcst[i]['tech'] == 'OFCD' and 
                abs(self.fcst[i]['jdnow'] - jdmsg) < 1.0 / 24):
                found = True
                break
        
        if found:
            return
        
        # Add new forecast record
        self.num_fcst += 1
        new_fcst = {
            'basin': basin,
            'cyNum': inum,
            'DTG': f"{yy:04d}{mo:02d}{dd:02d}{hh1//100:02d}",
            'jdnow': jdmsg,
            'technum': 1,
            'tech': 'OFCD',
            'stormname': name,
            'track': [
                {'tau': 3, 'lat': fix_lat, 'lon': fix_lon, 'vmax': vmax, 'mslp': mslp}
            ]
        }
        
        self.fcst.append(new_fcst)
        
        # Write out updated file and generate SQL files
        # ... (omitted for brevity, similar to parse_nhc_marine)
    
    def parse_nhc_watch(self):
        """Parse NHC Watch message"""
        pass
    
    def get_atcf_records(self, filename, tech_filter):
        """Load ATCF records from file (placeholder)"""
        # Implementation would read the ATCF file and populate self.fcst and self.num_fcst
        pass
    
    def sort_carq_records(self):
        """Sort CARQ records (placeholder)"""
        pass
    
    def sort_fcst_records(self):
        """Sort forecast records (placeholder)"""
        pass
    
    def write_carq_record(self, file_handle, index):
        """Write CARQ record to file (placeholder)"""
        pass
    
    def write_fcst_record(self, file_handle, index):
        """Write forecast record to file (placeholder)"""
        pass

def main():
    parser = TPCAdvisoryParser()
    
    # Parse command line arguments
    import sys
    args = sys.argv[1:]
    
    for i, arg in enumerate(args):
        if arg.startswith("-in"):
            if i + 1 < len(args):
                parser.infile = args[i+1]
    
    # Check if input file exists
    if not os.path.exists(parser.infile):
        print(f"*Error* {parser.infile} does not exist!")
        return
    
    # Read input file and process messages
    with open(parser.infile, 'r') as fin:
        for line in fin:
            parser.inbuffy = line.strip()
            
            # NHC Atlantic
            if line.startswith("WTNT2"):
                parser.parse_nhc_marine()
            if line.startswith("WTNT3"):
                parser.parse_nhc_public()
            if line.startswith("WTNT4"):
                parser.parse_nhc_discuss()
            if line.startswith("WTNT8"):
                parser.parse_nhc_watch()
            
            # NHC East Pacific
            if line.startswith("WTPZ2"):
                parser.parse_nhc_marine()
            if line.startswith("WTPZ3"):
                parser.parse_nhc_public()
            if line.startswith("WTPZ4"):
                parser.parse_nhc_discuss()
            
            # CPHC Central Pacific
            if line.startswith("WTPA2"):
                parser.parse_nhc_marine()
            if line.startswith("WTPA3"):
                parser.parse_nhc_public()
            if line.startswith("WTPA4"):
                parser.parse_nhc_discuss()

if __name__ == "__main__":
    print("\nTPC Marine Advisory to ATCF Track File Version 4.0")
    # Would include build info and copyright here
    main()
