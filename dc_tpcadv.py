import os
import re
from datetime import datetime, timedelta
from typing import List, Dict
import sys

# Example to how run file
# python3 dc_tpcadv.py -in NHC_message.dat

# Initialize variables
infile = None

# Get the number of command-line arguments
numargs = len(sys.argv)

# Loop through the command-line arguments
for i in range(1, numargs):  # Start from 1 to skip the script name
    if sys.argv[i] == "-in":  # Check if the argument is "-in"
        if i + 1 < numargs:  # Ensure there is a value after "-in"
            infile = sys.argv[i + 1]  # Get the value of the infile
        else:
            print("Error: No input file specified after '-in'")
            sys.exit(1)

# Check if infile was set
if infile is None:
    print("Error: '-in' argument is required")
    sys.exit(1)

# Print the infile for debugging
print(f"Input file: {infile}")

def extract_atcfid(filepath: str) -> str:
    with open(filepath, 'r') as file:
        for line in file:
            # Look for the line containing the ATCFID
            match = re.search(r'\b(AL|EP|CP|WP|IO|SH|SL|GM|MM|AA|BB|CC|DD|EE|FF|GG|HH|II|JJ|KK|LL|NN|OO|PP|QQ|RR|SS|TT|UU|VV|WW|XX|YY|ZZ)\d{6}\b', line)
            if match:
                return match.group(0)  # Return the matched ATCFID
    raise ValueError(f"ATCFID not found in file: {filepath}")

atfile = f"A{extract_atcfid(infile)}.DAT"  # Construct the ATCF output file name
ATCF_CYNUM = atfile[3:5]  # Extract the ATCF cyclone number from the filename
print(atfile)
ATCF_BASIN = atfile[1:3]  # Extract the ATCF basin from the filename
ATCF_YEAR = atfile[4:8]  # Extract the ATCF year from the filename


# ATCF-related structures
class TrackPoint:
    def __init__(self):
        self.tau = 0
        self.lat = 0.0
        self.cyNum = ATCF_CYNUM
        self.lon = 0.0
        self.vmax = 0
        self.mslp = 0
        self.radii = {"34": {"NE": 0, "SE": 0, "SW": 0, "NW": 0},
                      "50": {"NE": 0, "SE": 0, "SW": 0, "NW": 0},
                      "64": {"NE": 0, "SE": 0, "SW": 0, "NW": 0}}

class Forecast:
    def __init__(self):
        self.basin = "AL"
        self.cyNum = ATCF_CYNUM
        self.DTG = ""
        self.tech = "OFCL"
        self.stormname = ""
        self.track: List[TrackPoint] = []

# Global storage for forecasts
num_fcst = 0
fcst: List[Forecast] = []
current_storm = None  # To store current storm information

def extract_month_from_file(filepath: str) -> int:
    """Extract the month from NHC_message.dat and return it as an integer."""
    # Map month abbreviations to integers
    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    # Open the file and search for the month
    with open(filepath, 'r') as file:
        for line in file:
            # Search for the month abbreviation in the line
            match = re.search(r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b', line)
            if match:
                month_str = match.group(1)
                return month_map[month_str]
    
    # If no month is found, raise an error
    raise ValueError(f"Month not found in file: {filepath}")

def is_leap_year(year: int) -> bool:
    """Check if a year is a leap year."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


# Function to determine the number of days in a given month
def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month."""
    days_per_month = {
        1: 31, 2: 29 if is_leap_year(year) else 28, 3: 31, 4: 30,
        5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    return days_per_month[month]


def format_lat_lon(value: float, is_lat: bool) -> str:
    """Format latitude or longitude into ATCF format."""
    direction = "N" if is_lat else "W"
    formatted = f"{abs(int(value * 10)):03d}{direction}"
    return formatted

def parse_radii(line: str) -> Dict[str, int]:
    """Parse radii information from a line using regex."""
    radii = {"NE": 0, "SE": 0, "SW": 0, "NW": 0}
    match = re.search(r"(\d+)NE\s+(\d+)SE\s+(\d+)SW\s+(\d+)NW", line)
    if match:
        radii["NE"] = int(match.group(1))
        radii["SE"] = int(match.group(2))
        radii["SW"] = int(match.group(3))
        radii["NW"] = int(match.group(4))
    return radii


def parse_current_storm(lines: List[str]):
    """Parse current storm information using regex."""
    global current_storm

    # Extract the year from the file (assume it's on line 6)
    year = None
    for line in lines:
        # Match a 4-digit year at the end of the line
        year_match = re.search(r'\b(\d{4})$', line)
        if year_match:
            year = int(year_match.group(1))
            break

    if year is None:
        raise ValueError("Year not found in NHC_message.dat")


    for i, line in enumerate(lines):
        # Match previous storm center location
        print("line = ", line)
        match_previous = re.search(r"AT (\d{2}/\d{4}Z) CENTER WAS LOCATED NEAR ([\d.]+[NS])\s+([\d.]+[EW])", line)
        if match_previous:
            # Extract the date, time, latitude, and longitude
            prev_day = int(match_previous.group(1).strip()[0:2])
            print("prev_day = ", prev_day)
            prev_hour = int(match_previous.group(1).strip()[3:5])
            prev_lat = float(match_previous.group(2).strip()[:-1])
            prev_lon = float(match_previous.group(3).strip()[:-1])
            print(prev_hour)
            
            # Print for debugging
            print(f"Previous storm center location: {prev_lat}N, {prev_lon}W at day {prev_day}, hour {prev_hour}")
            
            # Optionally, store the previous storm center location in a variable or object
            previous_storm = {
                "day": prev_day,
                "hour": prev_hour,
                "lat": prev_lat,
                "lon": prev_lon
            }

            break


    current_month = extract_month_from_file(infile)
    global dtg_previous
    dtg_previous = datetime(year, current_month, prev_day, prev_hour)  # Format as YYYYMMDDHH
    global initial_datetime
    initial_datetime = dtg_previous  # Store the initial forecast datetime
    dtg_previous = dtg_previous.strftime("%Y%m%d%H")  # Format as YYYYMMDDHH



    for i, line in enumerate(lines):
        # Match storm center location
        match = re.search(r"(?:POTENTIAL TROP CYCLONE )?CENTER LOCATED NEAR\s+(\d+\.\d+)N\s+(\d+\.\d+)W", line)
        print(match)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            print("lat = ", lat)
            print("lon = ", lon)
            current_month = extract_month_from_file(infile)
            print(current_month)
            dtg_match = re.search(r"AT (\d{2})/(\d{4})Z", line)
            if dtg_match:
                day = int(dtg_match.group(1))
                hour = int(dtg_match.group(2)[:2])
                dtg = datetime(year, current_month, day, hour).strftime("%Y%m%d%H")  # Format as YYYYMMDDHH
            else:
                dtg = ""

            # Parse pressure and wind speed
            pressure_line = lines[i + 5]
            mslp_match = re.search(r"ESTIMATED MINIMUM CENTRAL PRESSURE\s+(\d+)", pressure_line)
            vmax_match = re.search(r"MAX SUSTAINED WINDS\s+(\d+)", lines[i+6])
            if not vmax_match:
                vmax_match = re.search(r"MAX SUSTAINED WINDS\s+(\d+)", lines[i+7])
                # Parse radii
                radii_64 = parse_radii(lines[i + 8])
                radii_50 = parse_radii(lines[i + 9])
                radii_34 = parse_radii(lines[i + 10])
            else:
                # Parse radii
                radii_64 = parse_radii(lines[i + 7])
                radii_50 = parse_radii(lines[i + 8])
                radii_34 = parse_radii(lines[i + 9])

            mslp = int(mslp_match.group(1)) if mslp_match else 0
            vmax = int(vmax_match.group(1)) if vmax_match else 0


            current_dtg = datetime(year, current_month, day, hour)  # Format as YYYYMMDDHH

            # Create a TrackPoint for the current storm
            global current_storm
            current_storm = TrackPoint()
            # Calculate tau based on the difference between the current and previous storm times

            current_storm.tau = int((current_dtg - initial_datetime).total_seconds() // 3600)
            current_storm.cyNum = int(ATCF_CYNUM)
            current_storm.lat = lat
            current_storm.lon = lon
            current_storm.vmax = vmax
            current_storm.mslp = mslp
            current_storm.dtg = dtg  # Format as YYYYMMDDHH
            current_storm.radii["64"] = radii_64
            current_storm.radii["50"] = radii_50
            current_storm.radii["34"] = radii_34

            break




    # Create a TrackPoint for the previous storm
    global previous_storm_point
    previous_storm_point = TrackPoint()
    previous_storm_point.tau = 0
    previous_storm_point.cyNum = int(ATCF_CYNUM)
    previous_storm_point.lat = prev_lat
    previous_storm_point.lon = prev_lon
    previous_storm_point.vmax = vmax
    previous_storm_point.mslp = mslp
    previous_storm_point.dtg = dtg_previous  # Format as YYYYMMDDHH
    previous_storm_point.radii["64"] = radii_64
    previous_storm_point.radii["50"] = radii_50
    previous_storm_point.radii["34"] = radii_34

    print("prev storm = ", previous_storm_point.vmax)




def extract_storm_name(filepath: str) -> str:
    with open(filepath, 'r') as file:
        for line in file:
            # Look for the line containing "HURRICANE <name>" or "TROPICAL STORM <name>"
            match = re.search(r'\b(HURRICANE|TROPICAL STORM|TROPICAL CYCLONE)\s+([A-Z]+)\b', line)
            if match:
                return match.group(2)  # Return the storm name
    raise ValueError(f"Storm name not found in file: {filepath}")



def parse_nhc_marine():
    """Parse NHC marine advisory message using regex."""
    global num_fcst, fcst

    with open(infile, 'r') as f:
        lines = f.readlines()
    
    # Extract the year from the file
    year = None
    for line in lines:
        year_match = re.search(r'\b(\d{4})$', line)
        if year_match:
            year = int(year_match.group(1))
            break

    if year is None:
        raise ValueError("Year not found in NHC_message.dat")
    
    # Extract the current month from the file
    current_month = extract_month_from_file(infile)
    
    # Extract the storm name
    storm_name = extract_storm_name(infile)

    # Parse current storm information
    parse_current_storm(lines)
    
    current_forecast = None
 # To store the initial forecast datetime
    for i, line in enumerate(lines):
        # Match forecast data
        if line.startswith("FORECAST VALID") or line.startswith("OUTLOOK VALID"):
            try:
                print(line)
                # Extract date and time
                date_time_match = re.search(r"(\d{2})/(\d{4})Z", line)
                if date_time_match:
                    day = int(date_time_match.group(1))
                    hour = int(date_time_match.group(2)[:2])

                    print(current_month)
                    print(day)


                    forecast_datetime = datetime(year, current_month, day, hour)  # Keep as datetime object
                    
                    print(forecast_datetime)

                    
                    # Calculate the timedelta in hours from the initial forecast
                    timedelta_hours = int((forecast_datetime - initial_datetime).total_seconds() // 3600)
                    if timedelta_hours < 0:
                        current_month += 1
                        forecast_datetime = datetime(year, current_month, day, hour)  # Keep as datetime object
                        timedelta_hours = int((forecast_datetime - initial_datetime).total_seconds() // 3600)


                        

                else:
                    raise ValueError(f"Invalid date format in line: {line}")
                
                # Extract latitude and longitude
                lat_lon_line = lines[i]
                lat_lon_match = re.search(r"(\d+\.\d+)N\s+(\d+\.\d+)W", lat_lon_line)
                lat = float(lat_lon_match.group(1)) if lat_lon_match else 0.0
                lon = float(lat_lon_match.group(2)) if lat_lon_match else 0.0
                
                # Extract maximum wind speed
                vmax_line = lines[i + 1]
                print(vmax_line)
                vmax_match = re.search(r"MAX WIND\s+(\d+)", vmax_line)
                vmax = int(vmax_match.group(1)) if vmax_match else 0


                # Initialize radii dictionaries with default values
                radii_34 = {"NE": 0, "SE": 0, "SW": 0, "NW": 0}
                radii_50 = {"NE": 0, "SE": 0, "SW": 0, "NW": 0}
                radii_64 = {"NE": 0, "SE": 0, "SW": 0, "NW": 0}

                # Check for and parse radii lines dynamically
                for j in range(2, 6):  # Look at the next few lines for radii information
                    if i + j < len(lines):
                        line = lines[i + j]
                        if "64 KT" in line:
                            radii_64 = parse_radii(line)
                        elif "50 KT" in line:
                            radii_50 = parse_radii(line)
                        elif "34 KT" in line:
                            radii_34 = parse_radii(line)


                # Extract minimum central pressure (if available)
                mslp = 0  # Default value if not provided


                
            except (IndexError, ValueError):
                print("error")
                continue
            
            # Create a new track point
            tp = TrackPoint()
            tp.tau = timedelta_hours  # Use the calculated timedelta in hours
            tp.lat = lat
            tp.lon = lon
            tp.vmax = vmax
            tp.mslp = mslp
            if radii_34 is not None:
                tp.radii["34"] = radii_34
            else:
                pass
            if radii_50 is not None:
                tp.radii["50"] = radii_50
            else:
                pass
            if radii_64 is not None:
                tp.radii["64"] = radii_64
            else:
                pass


            # Add track point to forecast
            if current_forecast is None or current_forecast.DTG != forecast_datetime.strftime("%Y%m%d%H"):
                current_forecast = Forecast()
                current_forecast.DTG = forecast_datetime.strftime("%Y%m%d%H")  # Format DTG for output
                fcst.append(current_forecast)
                num_fcst += 1
            
            current_forecast.track.append(tp)
        

    # Write out updated ATCF file
    with open(atfile, 'w') as atf:
        # Write previous storm information
        if previous_storm_point:
            written_rows = set()
            for wind_speed in ["34", "50", "64"]:
                radii = previous_storm_point.radii[wind_speed]
                # Debug: Print formatted lat and lon
                formatted_lat = format_lat_lon(previous_storm_point.lat, True)
                formatted_lon = format_lat_lon(previous_storm_point.lon, False)
                # Skip writing the row if all radii values are zero
                if all(value == 0 for value in radii.values()):
                    if wind_speed in ["50", "64"]:
                        continue
                    line = (f"AL, {previous_storm_point.cyNum:2d}, {previous_storm_point.dtg},  1, OFCL,  {previous_storm_point.tau:2}, "
                            f"{formatted_lat},  {formatted_lon:<2}, "
                            f"{previous_storm_point.vmax:3d}, {previous_storm_point.mslp:4d}  \n")
                else:
                    # Create the row string with explicit spacing between lat and lon
                    line = (f"AL, {previous_storm_point.cyNum:2d}, {previous_storm_point.dtg},  1, OFCL,  {previous_storm_point.tau:2}, "
                            f"{formatted_lat},  {formatted_lon:<2}, "
                            f"{previous_storm_point.vmax:3d}, {previous_storm_point.mslp:4d}, XX,  {wind_speed}, NEQ, "
                            f" {radii['NE']:3d},  {radii['SE']:3d},  {radii['SW']:3d},  {radii['NW']:3d}, ,   , , , , , ,      {storm_name.strip()}       , \n")
                # Debug: Print the generated line
                # Skip duplicate rows
                if line in written_rows:
                    continue
                written_rows.add(line)
                atf.write(line)


        # Write current storm information
        if current_storm:
            written_rows = set()  # To track already written rows
            for wind_speed in ["34", "50", "64"]:
                radii = current_storm.radii[wind_speed]
                # Debug: Print formatted lat and lon
                formatted_lat = format_lat_lon(current_storm.lat, True)
                formatted_lon = format_lat_lon(current_storm.lon, False)
                # Skip writing the row if all radii values are zero
                if all(value == 0 for value in radii.values()):
                    if wind_speed in ["50", "64"]:
                        continue
                    line = (f"AL, {current_storm.cyNum:2d}, {previous_storm_point.dtg},  1, OFCL,  {current_storm.tau:2}, "
                            f"{formatted_lat},  {formatted_lon:<2}, "
                            f"{current_storm.vmax:3d}, {current_storm.mslp:4d}  \n")
                else:                    
                    # Create the row string with explicit spacing between lat and lon
                    line = (f"AL, {current_storm.cyNum:2d}, {previous_storm_point.dtg},  1, OFCL,  {current_storm.tau:2}, "
                            f"{formatted_lat},  {formatted_lon:<2}, "
                            f"{current_storm.vmax:3d}, {current_storm.mslp:4d}, XX,  {wind_speed}, NEQ, "
                            f" {radii['NE']:3d},  {radii['SE']:3d},  {radii['SW']:3d},  {radii['NW']:3d}, ,   , , , , , ,      {storm_name.strip()}       , \n")
                # Debug: Print the generated line
                # Skip duplicate rows
                if line in written_rows:
                    continue
                written_rows.add(line)
                atf.write(line)



        # Write forecast data
        for forecast in fcst:
            written_rows = set()  # To track already written rows
            for tp in forecast.track:
                for wind_speed in ["34", "50", "64"]:
                    radii = tp.radii[wind_speed]
                    # Debug: Print formatted lat and lon
                    formatted_lat = format_lat_lon(tp.lat, True)
                    formatted_lon = format_lat_lon(tp.lon, False)
                    # Skip writing the row if all radii values are zero
                    if all(value == 0 for value in radii.values()):
                        if wind_speed in ["50", "64"]:
                            continue
                        line = (f"{forecast.basin}, {int(forecast.cyNum):2d}, {previous_storm_point.dtg},  1, {forecast.tech}, {tp.tau:3}, "
                                f"{formatted_lat},  {formatted_lon:<2}, "
                                f"{tp.vmax:3d}, {tp.mslp:4d}  \n")
                    else:
                        # Create the row string with explicit spacing between lat and lon
                        line = (f"{forecast.basin}, {int(forecast.cyNum):2d}, {previous_storm_point.dtg},  1, {forecast.tech}, {tp.tau:3}, "
                                f"{formatted_lat},  {formatted_lon:<2}, "
                                f"{tp.vmax:3d}, {tp.mslp:4d}, XX,  {wind_speed}, NEQ, "
                                f" {radii['NE']:3d},  {radii['SE']:3d},  {radii['SW']:3d},  {radii['NW']:3d}, ,   , , , , , ,      {storm_name.strip()}       , \n")

                    # Debug: Print the generated line
                    # Skip duplicate rows
                    if line in written_rows:
                        continue
                    written_rows.add(line)
                    atf.write(line)


# Example usage in the main program
def main():
    """Main program"""
    if infile is None:
        print("Error: '-in' argument is required")
        sys.exit(1)

    parse_nhc_marine()


if __name__ == "__main__":
    main()
