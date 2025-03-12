import geopandas as gpd

from metloom.pointdata.cdec import CDECPointData
from metloom.variables import CdecStationVariables


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



if __name__ == '__main__':
    make_snow_course_metadata()