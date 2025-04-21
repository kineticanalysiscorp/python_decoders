import os
import math
import csv

# Constants
UCSV = 201
UOUT = 202
UXRF = 203

def get_environment_variable(var_name):
    """Get the value of an environment variable."""
    return os.getenv(var_name, '')

def parse_csv_line(line):
    """Parse a CSV line."""
    return list(csv.reader([line]))[0]

def get_csv_var(data, key):
    """Get a value from the parsed CSV data by key."""
    return data.get(key, '')

def get_int_var(data, key):
    """Get an integer value from the parsed CSV data by key."""
    try:
        return int(data.get(key, 0))
    except ValueError:
        return 0

def get_dbl_var(data, key):
    """Get a double (float) value from the parsed CSV data by key."""
    try:
        return float(data.get(key, 0.0))
    except ValueError:
        return 0.0

def write_carq_record(carq):
    """Write the carq record (mock function for demonstration)."""
    print('Writing CARQ Record:', carq)

def main():
    print("\nABOM Best Track database to ATCF B Deck\n")
    print("Build Data: <Insert Build Data Here>")
    print("Copyright Data: <Insert Copyright Data Here>\n")

    # Get environment variable
    taoshome = get_environment_variable('TAOS_HOME')
    if not taoshome:
        print("TAOS_HOME environment variable not set.")
        return

    bomfile = os.path.join(taoshome, 'support/tc_catalogs/IDCKMSTM0S.csv')
    if not os.path.exists(bomfile):
        print(f"FAIL: {bomfile} not found!")
        return

    # Open the CSV file
    with open(bomfile, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        gotheader = False
        numstorms = 0

        lastbomid = 'none'
        irec = 1

        with open('bom_ids.csv', 'w') as uxrf:
            for row in csv_reader:
                bomid = row.get('DISTURBANCE_ID', '').strip()
                if not bomid:
                    continue

                if bomid != lastbomid:
                    atcf_file = f"BAU{bomid[9:11]}{bomid[2:6]}.DAT"
                    atcfid = f"AU{bomid[9:11]}{bomid[2:6]}"
                    cynum = int(bomid[9:11])
                    name = row.get('NAME', '').strip()
                    tm = row.get('TM', '').strip()

                    uxrf.write(f"{atcfid},{bomid[9:12]},{tm[:4]},{name}\n")

                carq = {
                    'basin': 'AU',
                    'cynum': cynum,
                    'stormname': row.get('NAME', '').strip(),
                    'dtg': f"{tm[:4]}{tm[5:7]}{tm[8:10]}{tm[11:13]}",
                    'tech': 'BEST',
                    'lat': get_dbl_var(row, 'LAT'),
                    'lon': get_dbl_var(row, 'LON'),
                    'mslp': get_int_var(row, 'CENTRAL_PRES'),
                    'mrd': get_int_var(row, 'MN_RADIUS_MAX_WIND') / 1.852,
                }

                if carq['mslp'] == 0:
                    continue

                wspd = get_dbl_var(row, 'MAX_WIND_SPD') * 1.944
                if wspd < 0:
                    wspd = 0

                if wspd == 0:
                    cp = 1012. - carq['mslp']
                    if cp < 1.0:
                        cp = 1.0
                    carq['vmax'] = 14.1 * math.sqrt(cp)
                else:
                    cfactor = 0.9
                    carq['vmax'] = wspd / cfactor

                carq['windrad'] = [
                    {
                        'value': 34,
                        'code': 'NEQ',
                        'radii': [
                            get_int_var(row, 'MN_RADIUS_GF_SECNE'),
                            get_int_var(row, 'MN_RADIUS_GF_SECSE'),
                            get_int_var(row, 'MN_RADIUS_GF_SECSW'),
                            get_int_var(row, 'MN_RADIUS_GF_SECNW'),
                        ]
                    }
                ]

                carq['rrp'] = get_int_var(row, 'MN_RADIUS_OUTER_ISOBAR')
                carq['radp'] = get_int_var(row, 'ENV_PRES')

                write_carq_record(carq)

                lastbomid = bomid

if __name__ == "__main__":
    main()
