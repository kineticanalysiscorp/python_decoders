import re
import sys
from datetime import datetime, timedelta


def parse_and_convert_to_atcf(input_file, output_file):
    """
    Parses a text file with tropical cyclone warnings and forecasts
    and converts it into a modified ATCF format.
    """
    with open(input_file, "r") as file:
        data = file.read()

    # Extract the cyclone name and warning number
    subj_match = re.search(r"SUBJ/TROPICAL CYCLONE (\d+[A-Z]) \(([\w\s]+)\) WARNING NR (\d+)", data)
    if not subj_match:
        print("Error: Unable to extract cyclone name or warning number.")
        return

    cyclone_id, cyclone_name, warning_number = subj_match.groups()
    cyclone_name = cyclone_name.strip().upper()
    cyclone_id = cyclone_id[:-1]

    # Extract central pressure (MSLP)
    central_pressure_match = re.search(r"MINIMUM CENTRAL PRESSURE AT \d{6}Z IS (\d+) MB", data)
    central_pressure = central_pressure_match.group(1) if central_pressure_match else "0000"

    # Extract warning position and wind radii
    warning_match = re.search(r"WARNING POSITION:\s*(\d{6}Z) --- NEAR\s*(\d+\.\d)([NS])\s*(\d+\.\d)([EW])", data)
    if not warning_match:
        print("Error: Unable to extract warning position.")
        return

    warning_time, lat_deg, lat_dir, lon_deg, lon_dir = warning_match.groups()
    lat_tenths = f"{int(float(lat_deg) * 10):4d}{lat_dir}" #convert to tenths of degree
    lon_tenths = f"{int(float(lon_deg) * 10):5d}{lon_dir}" #convert to tenths of degree
    warning_time = warning_time[:-1]    # strip trailing Z
    print("warning_time = ", warning_time)
    warning_year = str(datetime.now().year) + warning_time # add year at front of time

    # Determine BASIN based on location
    lon_float = float(lon_deg)
    lat_float = float(lat_deg)
    if (lon_dir == 'E' and 100 <= lon_float <= 180 and lat_dir == "N"):
        BASIN = "WP"
    if (lon_dir == 'E' and 20 <= lon_float <= 100 and lat_dir == "N"):
        BASIN = "NI"
    if (lat_dir == "S"):
        BASIN = "SH"

    # Extract wind radii for the warning
    wind_radii = extract_wind_radii(data, warning_time)

    # Extract warning and process each forecast time
    warning_test = list(re.findall(
        r"(\d{6}Z) --- NEAR (\d+\.\d)([NS]) (\d+\.\d)([EW])", data, re.DOTALL))
    warning = re.findall(r"MAX SUSTAINED WINDS - (\d+) KT, GUSTS (\d+)", data, )[0]
    warning_wind = warning[0]
    warning = warning_test[0] + warning   # concatenate so it is same as forecasts

    # Prepare the ATCF lines for the warning
    f_time = 0  # use for current position
    dummy = 0 # place holder
    atcf_lines = []
    atcf_lines.extend(generate_atcf_lines(BASIN, cyclone_id, cyclone_name, warning_year, lat_tenths, lon_tenths, warning_wind, dummy, f_time, wind_radii))


# Now do forecasts
    # Extract forecast and process each forecast time

    forecasts = re.findall(
        r"(\d{6}Z) --- (\d+\.\d)([NS]) (\d+\.\d)([EW])\s*MAX SUSTAINED WINDS - (\d+) KT, GUSTS (\d+) KT", data, re.DOTALL)  # find wind radii
    forecast_times = re.findall(r"(\d+) HRS", data, re.DOTALL)  # extract forecast times
    if len(forecasts) == len(forecast_times):
        forecasts_leads = extend_tuples_with_integer(forecasts, forecast_times)
    else:
        forecasts_leads = extend_tuples_with_integer(forecasts, forecast_times)

    # Parse the year from the warning time
    current_year = datetime.utcnow().year
    warning_datetime = datetime.strptime(warning_time, "%d%H%M").replace(year=current_year)

    for forecast in forecasts_leads:
        forecast_time, lat_deg, lat_dir, lon_deg, lon_dir, wind, gust, lead = forecast
        forecast_time = forecast_time[:-1]  # strip trailing Z
        forecast_datetime = datetime.strptime(forecast_time, "%d%H%M").replace(year=current_year)
        # Check if forecast extends to a new year
        if forecast_datetime < warning_datetime:
            forecast_datetime = forecast_datetime.replace(year=current_year + 1)

        lat_tenths = f"{int(float(lat_deg) * 10):4d}{lat_dir}"
        lon_tenths = f"{int(float(lon_deg) * 10):5d}{lon_dir}"
        forecast_radii = extract_wind_radii(data, forecast_time)
        atcf_lines.extend(generate_atcf_lines(BASIN, cyclone_id, cyclone_name, warning_year, lat_tenths, lon_tenths, wind, forecast_times, lead, forecast_radii))

    # Write the ATCF lines to the output file
    with open(output_file, "w") as file:
        file.writelines(atcf_lines)


def extract_wind_radii(data, valid_time):
    """
    Extracts wind radii for a specific valid time (warning or forecast).
    Returns a dictionary with wind radii for 34, 50, and 64 knots.
    Omits missing quadrants.
    """
    wind_radii = {"034": None, "050": None, "064": None}
    for wind_speed in ["064", "050", "034"]:
        # Match wind radii for the specific valid time
        match = re.findall(
            rf"{valid_time}.*?RADIUS OF {wind_speed} KT WINDS - (\d+) NM NORTHEAST QUADRANT\s+(\d+) NM SOUTHEAST QUADRANT\s+(\d+) NM SOUTHWEST QUADRANT\s+(\d+) NM NORTHWEST QUADRANT",
            data, re.DOTALL
        )
        if match:
            radii = match
            wind_radii[wind_speed] = [
                format_radii_value(int(radii[0][0])),
                format_radii_value(int(radii[0][1])),
                format_radii_value(int(radii[0][2])),
                format_radii_value(int(radii[0][3])),
            ]

    return wind_radii


def format_radii_value(value):
    """
    Formats a radius value, omitting it if it's missing or invalid.
    """
    if value is None or value in {"N/A", "NONE"}:
        return None
    return f"{int(value):3}"


def generate_atcf_lines(BASIN, cyclone_id, cyclone_name, time, lat, lon, wind, forecast_times, lead, wind_radii):
    """
    Generates ATCF lines for the given cyclone, time, and wind radii.
    Each wind category (34, 50, 64 knots) is written as a separate line.
    Missing quadrants are omitted.
    """
    #print("in generate_atcf_lines")
    atcf_lines = []
    radii_written = False
    count = 0
    for wind_speed, radii in wind_radii.items():
        if radii:
            # Filter out None values (missing quadrants)
            filtered_radii = [r for r in radii if r is not None]
            if not "filtered_radii" in locals():
                count = 1
                print("count = ", count)
                radii_written = False
            #if r in radii is None and r in radii == 34: radii_written = False
            if filtered_radii:  # Only write the line if there are remaining quadrants
                #line = f"{cyclone_id},{time},{lat},{lon},{wind_speed},{','.join(filtered_radii)},{cyclone_name}\n"
                formatted_lead = f"{int(lead):3}"
                formatted_radii = ", ".join(f"{int(r):>4}" for r in filtered_radii)
                line = f"{BASIN}, {cyclone_id}, {time},  1, JTWC, {int(lead):>3},{lat},{lon},  {wind[1:]},    0,   ,  {wind_speed[1:]}, AAA, {''.join(formatted_radii)}, , , , , , , , , , , {cyclone_name}, ,\n"
                print(filtered_radii)
                atcf_lines.append(line)
                radii_written = True

        # If no radii were written, add a placeholder line
        if not "filtered_radii" in locals() and count == 0:
            formatted_lead = f"{int(lead):3}"
            line = f"{BASIN}, {cyclone_id}, {time},  1, JTWC, {int(lead):>3},{lat},{lon},  {wind[1:]},    0,   ,  , , ,  , , , , , , , , , , , {cyclone_name}, ,\n"
            count = count + 1
            atcf_lines.append(line)

    return atcf_lines

def extend_tuples_with_integer(list_of_tuples, integers):
    """Extends each tuple in a list with corresponding integer(s).

    Args:
        list_of_tuples: A list of tuples.
        integers: A list of integers to add to the tuples.

    Returns:
        A new list with extended tuples.
    """
    if len(list_of_tuples) != len(integers):
        raise ValueError("The list of tuples and integers must have the same length.")

    extended_list = [tuple(list(t) + [n]) for t, n in zip(list_of_tuples, integers)]
    return extended_list

if __name__ == "__main__":
    # Ensure proper usage
    if len(sys.argv) != 3:
        print("Usage: python atcf_format_converter.py <input_file> <output_file>")
        sys.exit(1)

    # Get input and output file paths from the command line
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Run the parser and converter
    atcf_data = parse_and_convert_to_atcf(input_file, output_file)
