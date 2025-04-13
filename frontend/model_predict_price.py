import pandas as pd
from shapely.geometry import Point, shape
import requests
import json
import geopandas as gpd
from math import radians, cos, sin, sqrt, atan2

df_resale = pd.read_csv("resale_price_cleaned.csv")

df_resale = df_resale.drop(columns=["town"])

# Normalize

# For each column, store the max and min for later normalization
min_max_dict = {
    col: {
        "min": df_resale[col].min(),
        "max": df_resale[col].max()
    }
    for col in df_resale.columns
}


def normalize_column(value, col):
    min_val = min_max_dict[col]["min"]
    max_val = min_max_dict[col]["max"]
    if max_val == min_val:
        return 0 
    return (value - min_val) / (max_val - min_val)

ONEMAP_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1M2M4NGU0YmJlMWVlZDhmMDczNDk4ODVmZDExYWRjOSIsImlzcyI6Imh0dHA6Ly9pbnRlcm5hbC1hbGItb20tcHJkZXppdC1pdC1uZXctMTYzMzc5OTU0Mi5hcC1zb3V0aGVhc3QtMS5lbGIuYW1hem9uYXdzLmNvbS9hcGkvdjIvdXNlci9wYXNzd29yZCIsImlhdCI6MTc0Mzc1ODAyNSwiZXhwIjoxNzQ0MDE3MjI1LCJuYmYiOjE3NDM3NTgwMjUsImp0aSI6IkF6YWZjWGxDb2tNb0hmQ1AiLCJ1c2VyX2lkIjozNTA0LCJmb3JldmVyIjpmYWxzZX0.CMD124pML3xaJU45AklBASBYNmojp_wctKoRupiDkQ0"


with open('planning_area.json') as f:
    planning_areas = json.load(f)['SearchResults']

def get_coordinates_from_postal(postal_code):
    url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
    headers = {"Authorization": ONEMAP_TOKEN}
    response = requests.get(url, headers=headers)
    data = response.json()
    if data["found"] > 0:
        result = data["results"][0]
        return float(result["LATITUDE"]), float(result["LONGITUDE"])
    return None, None


def get_planning_area_from_point(lat, lon, planning_areas):
    point = Point(lon, lat) 
    
    for area in planning_areas:
        geojson = json.loads(area['geojson'])  
        polygon = shape(geojson)
        
        if polygon.contains(point):
            return area['pln_area_n']
    
    return None

def get_planning_area_from_postal(postal_code):
    lat, lon = get_coordinates_from_postal(postal_code)
    if (lat is None) or (lon is None):
        return "Invalid postal code"
    return get_planning_area_from_point(lat, lon, planning_areas)

bus_stops = gpd.read_file("BusStopLocation_Nov2024/BusStop.shp")
MRT_stops = pd.read_csv("MRT Stations.csv")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2*R*atan2(sqrt(a), sqrt(1 - a))

from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)

def svy21_to_wgs84(easting, northing):
    lon, lat = transformer.transform(easting, northing)
    return lat, lon


bus_stops['x_coord'] = bus_stops.geometry.apply(lambda geom: geom.x)
bus_stops['y_coord'] = bus_stops.geometry.apply(lambda geom: geom.y)
bus_stops['Latitude'], bus_stops['Longitude'] = zip(*bus_stops.apply(lambda row: svy21_to_wgs84(row['x_coord'], row['y_coord']), axis=1))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

def get_nearest_distances(lat, lon):
    MRT_stops['distance'] = MRT_stops.apply(
        lambda row: haversine(lat, lon, row['Latitude'], row['Longitude']), axis=1
    )
    nearest_mrt_distance = MRT_stops['distance'].min()

    # Calculate distances to all bus stops
    bus_stops['distance'] = bus_stops.apply(
        lambda row: haversine(lat, lon, row['Latitude'], row['Longitude']), axis=1
    )
    nearest_bus_distance = bus_stops['distance'].min()

    return nearest_mrt_distance, nearest_bus_distance

def get_amenity_score(hdb_lat, hdb_lon, amenity_type):
 
    if amenity_type == "education":
        df = pd.read_csv("Amenities_school.csv")
    elif amenity_type == "healthcare":
        df = pd.read_csv("Amenities_healthcare.csv")
    elif amenity_type == "shopping":
        df = pd.read_csv("Amenities_shopping.csv")
    elif amenity_type == "food":
        df = pd.read_csv("Amenities_food.csv")
    elif amenity_type == "recreation":
        df = pd.read_csv("Amenities_recreation.csv")
    else:
        raise ValueError(f"Unsupported amenity type: {amenity_type}")

    scores = []
    for _, row in df.iterrows():
        distance = haversine(hdb_lat, hdb_lon, row['lat'], row['lon'])
        if distance <= 3000:
            score = 1 * 1000 / (distance + 50)
            scores.append(score)
    
    total_score = sum(scores)

    return total_score

def get_religion (town):
    # religion
    df_religion = pd.read_csv("religion_2020.csv")
    df_religion.rename(columns = {"Number":"town"}, inplace = True)
    df_religion['town'] = df_religion['town'].replace('Kallang', 'Kallang/Whampoa')
    # Combine 'Outram', 'Downtown Core', 'River Valley', 'Novena' into 'Central Area'
    central_area_row = df_religion[df_religion['town'].isin(['Outram', 'Downtown Core', 'River Valley', 'Novena'])].sum(numeric_only=True)
    central_area_row['town'] = 'CENTRAL AREA'
    df_religion = df_religion[~df_religion['town'].isin(['Outram', 'Downtown Core', 'River Valley', 'Novena', 'Total','Others'])]
    df_religion = pd.concat([df_religion, pd.DataFrame([central_area_row])], ignore_index=True)
    # Capitalize the 'town' column
    df_religion['town'] = df_religion['town'].str.upper()

    for col in df_religion.columns:
        if col != "town":
            df_religion[col] = pd.to_numeric(df_religion[col], errors='coerce')
            df_religion[col] = df_religion[col].astype(float)
    for col in df_religion.columns:
        if col != "town" and col != "Total":
            df_religion[col] = df_religion[col] / df_religion["Total"]

    df = pd.DataFrame()

    for _, row in df_religion.iterrows():
        if town == row['town']:
            df['NoReligion'] = [row['NoReligion']]
            df['Buddhism'] = [row['Buddhism']]
            df['Taoism1'] = [row['Taoism1']]
            df['Islam'] = [row['Islam']]
            df['Hinduism'] = [row['Hinduism']]
            df['Sikhism'] = [row['Sikhism']]
            df['Christianity_Catholic'] = [row['Christianity_Catholic']]
            df['Christianity_OtherChristians'] = [row['Christianity_OtherChristians']]
            df['OtherReligions'] = [row['OtherReligions']]
            break
    
    return df

def get_income (town):
    
    # avg household income
    df_income = pd.read_csv("resale_price_cleaned.csv")
    df_income = df_income[df_income['month'] == '2024-12']
    df_income = df_income[['town', 'avg_household_income']]
    df_income = df_income.drop_duplicates()

    df = pd.DataFrame()
    
    for _, row in df_income.iterrows():
        if town == row['town']:
            df['avg_household_income'] = [row['avg_household_income']]
            break


    return df


df_income = pd.read_csv("resale_price_cleaned.csv")

def get_flat_type(flat_type):
    if flat_type == "1 Room":
        return 1
    elif flat_type == "2 Room":
        return 2
    elif flat_type == "3 Room":
        return 3
    elif flat_type == "4 Room":
        return 4
    elif flat_type == "5 Room":
        return 5
    elif flat_type == "Executive":
        return 6
    elif flat_type == "Multi-Generation":
        return 7
    else:
        raise ValueError(f"Unsupported flat type: {flat_type}")



def price_predict(storey_range, flat_type, remaining_lease, postal_code, model):

    # town, lat, lon
    town = get_planning_area_from_postal(postal_code)
    lat, lon = get_coordinates_from_postal(postal_code)
    mrt = get_nearest_distances(lat,lon)[0]
    bus = get_nearest_distances(lat,lon)[1]

    # amenity score
    education_score = get_amenity_score(lat, lon, "education")
    shopping_score = get_amenity_score(lat, lon, "shopping")
    food_score = get_amenity_score(lat, lon, "food")
    recreation_score = get_amenity_score(lat, lon, "recreation")
    healthcare_score = get_amenity_score(lat, lon, "healthcare")

    # demographic
    religion_df = get_religion(town)
    income_df = get_income(town)

    X_input = pd.DataFrame([{
        'town': town,
        'storey_range': storey_range,
        'flat_type': get_flat_type(flat_type),
        'remaining_lease': remaining_lease,
        'lat': lat,
        'lon': lon,
        'nearest_mrt_distance': mrt,
        'nearest_bus_distance': bus,
        'education_score': education_score,
        'shopping_score': shopping_score,
        'food_score': food_score,
        'recreation_score': recreation_score,
        'healthcare_score': healthcare_score,

        # Based on 2024-12 data
        'inflation_rate (x100)': 0.3468,
        'resident_unemployment_rate': 2.0,
        'interest_rate': 2.1123,
        
        'avg_household_income': income_df['avg_household_income'].iloc[0],
        'NoReligion': religion_df['NoReligion'].iloc[0],
        'Buddhism': religion_df['Buddhism'].iloc[0],
        'Taoism1': religion_df['Taoism1'].iloc[0],
        'Islam': religion_df['Islam'].iloc[0],
        'Hinduism': religion_df['Hinduism'].iloc[0],
        'Sikhism': religion_df['Sikhism'].iloc[0],
        'Christianity_Catholic': religion_df['Christianity_Catholic'].iloc[0],
        'Christianity_OtherChristians': religion_df['Christianity_OtherChristians'].iloc[0],
        'OtherReligions': religion_df['OtherReligions'].iloc[0],
        'priv_prop': 27531.0,
    

        'year': 2025,
        'month_num': 4
        }])
    
    # for each input, make them normalized by using their (original value - min)/(max - min)
    for col in X_input.columns:
        if col in min_max_dict:
            X_input[col] = X_input[col].apply(lambda x: normalize_column(x, col))
    y = model.predict(X_input)
    y = y * (min_max_dict['resale_price']['max']- min_max_dict['resale_price']['min']) + min_max_dict['resale_price']['min']
    return y[0]


