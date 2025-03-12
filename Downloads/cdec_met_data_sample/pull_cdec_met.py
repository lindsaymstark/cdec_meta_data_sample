import geopandas as gpd

from metloom.pointdata.cdec import CDECPointData
from metloom.variables import CdecStationVariables
from datetime import datetime


def make_snow_course_metadata():
    """
    Pull snow courses using metloom for all the Sierras. Rearranges data
    to match the csv format from Lindsay's SnowModel project. Then dumps to csv.

    # Columns:
    statecode, station ID, lat, lon, elev
    """
    f = 'sierras_outline.shp'
    shp_df = gpd.read_file(f)

    # Find all the stations and courses in the sierras
    pnts = CDECPointData.points_from_geometry(shp_df, variables=[CdecStationVariables.SWE], snow_courses=True)

    # Convert to df
    df = pnts.to_dataframe()

    # Rearrange format to look close to Glens file.

    # 1. Isolate location info from geometry
    df['lon'] = df.geometry.x
    df['lat'] = df.geometry.y
    df['elev'] = df.geometry.z

    # 2. Rename columns to better match
    df = df.rename(columns={"id":"station ID"})

    # 3. Remove the geometry column
    df = df.drop(columns=['geometry'])

    # 4. Add State Code
    df['statecode'] = 'CA'

    # 5. Set the file column order
    columns_order = ['statecode', 'station ID', 'lat', 'lon', 'elev']

    # 6. Dump to CSV
    df[columns_order].to_csv("Sierras_COURSE_station_info.csv", index=False)

    print(pnts)


def organize_for_snowmodel(df, is_snowcourse=False):
    """
    Process and output the data according to the Lindsay snowmodel format
    for a single site
    """

    # Columns of interest to output
    coi = ['Y', 'M', 'D', 'swe', 'depth', 'density']

    # TODO: This might need some tweaking for the occasional NV course??
    state_code = 'CA'

    # Decide site type
    sitetype = 'SNOCOURSE' if is_snowcourse else 'SMSITE' # Not sure when this is SNOTEL.


    # 1. Reset how the dataframe is indexed
    df = df.reset_index()

    # Isolate the site id
    stationID = df['site'].iloc[0]

    # 2. Separate out date format
    date_col = 'measurementDate' if is_snowcourse else 'datetime'
    df['Y'] = df[date_col].dt.year
    df['M'] = df[date_col].dt.strftime("%b")  # Grab 3 letter month
    df['D'] = df[date_col].dt.strftime('%d') # Ensure day is always 2 digits

    # 3. Rename columns
    df = df.rename(columns={"SWE":'swe', 'SNOWDEPTH':'depth'})

    # 4. convert SWE and depth from inches to mm and cm
    df['swe'] = df['swe'] * 25.4 # in -> mm
    df['depth'] = df['depth'] * 2.54 # in -> cm

    # 4. Compute the density
    # Set default value
    df['density'] = 0

    # Filter to valid density data
    ind = (df['swe'] > 0) & (df['depth'] > 0)

    # Compute density using rho_pure_water * mass[meters] / depth[meters]
    df['density'][ind] = 997 * 0.001 * df['swe'][ind] / (0.01 * df['depth'][ind])

    # 5. Save each to its own file
    out_file = f"{state_code}_{stationID}_{sitetype}.csv"
    print(f"Outputting data to {out_file}")
    df[coi].to_csv(out_file, float_format="%.1f", index=False)


def get_snow_course_data(start, end, limit=None):
    """
    Grab all the snow courses and their data during the period of interest.
    Then format for Lindsay's file
    """
    # Use limit if testing/debugging
    limit = -1 if limit is None else limit

    # Density is not built into metloom. We will compute it on the fly
    variables = [CdecStationVariables.SWE, CdecStationVariables.SNOWDEPTH]

    f = 'sierras_outline.shp'
    shp_df = gpd.read_file(f)

    # Find all the stations and courses in the sierras
    print('Finding all points in Sierras...')
    pnts = CDECPointData.points_from_geometry(shp_df, variables=[CdecStationVariables.SWE], snow_courses=True)

    # Loop over the pnt objects and pull snow course data
    for pnt in pnts.points[0:limit]:
        print(f"Pulling {pnt.id}")
        df = pnt.get_snow_course_data(start, end, variables=variables)

        # Account for sites that return null for whatever reason
        if df is not None:
            organize_for_snowmodel(df, is_snowcourse=True)


def get_cdec_snotel_data(start, end, limit=None):
    """
    Grab all the snow pillow and depth sensor during the period of interest
    and save then it to a file
    """
    # Limit number of stations if testing
    limit = -1 if limit is None else limit

    # Density is not built into metloom. We will compute it on the fly
    variables = [CdecStationVariables.SWE, CdecStationVariables.SNOWDEPTH]

    f = 'sierras_outline.shp'
    shp_df = gpd.read_file(f)

    # Find all the stations and courses in the sierras
    print('Finding all points in Sierras...')
    pnts = CDECPointData.points_from_geometry(shp_df,
                                              variables=[CdecStationVariables.SWE])

    # Loop over the pnt objects and pull snow course data
    for pnt in pnts.points[0:limit]:
        print(f"Pulling {pnt.id}")
        df = pnt.get_daily_data(start, end, variables=variables)

        # Account for sites that return null for whatever reason
        if df is not None:
            organize_for_snowmodel(df, is_snowcourse=False)

def main():
    """
    Main function to run everything
    """
    # Start time to begin pulling data
    start = datetime(2023, 10, 1)

    # End time to stop pulling data
    end = datetime(2024, 9, 30)

    # Download and make the metadata for snow courses file
    make_snow_course_metadata()

    # Download and make snow course data files
    get_snow_course_data(start, end, limit=3)

    # # Download and make station data files
    get_cdec_snotel_data(start, end, limit=3)


if __name__ == '__main__':
    main()

