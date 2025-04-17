import os
import json
import joblib
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
from math import radians, cos, sin, sqrt, atan2
from pyproj import Transformer
import streamlit as st
import translations

# Set up base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

# Load and preprocess data
df_resale = pd.read_csv(os.path.join(data_dir, "resale_price_cleaned.csv")).drop(columns=["town"])
min_max_dict = {
    col: {"min": df_resale[col].min(), "max": df_resale[col].max()}
    for col in df_resale.columns
}

def normalize_column(value, col):
    min_val = min_max_dict[col]["min"]
    max_val = min_max_dict[col]["max"]
    if max_val == min_val:
        return 0
    return (value - min_val) / (max_val - min_val)


# Planning areas
with open(os.path.join(data_dir, "planning_area.json")) as f:
    planning_areas = json.load(f)['SearchResults']

def get_coordinates_from_postal(postal_code):

    import requests

    # Replace with your OneMap API login credentials
    email = "e1090510@u.nus.edu"
    password = "Onemap12345!"

    token_url = "https://www.onemap.gov.sg/api/auth/post/getToken"
    data = {"email": email, "password": password}

    response = requests.post(token_url, json=data)

    if response.status_code == 200:
        ONEMAP_TOKEN = response.json().get("access_token")
        print("Access Token:", ONEMAP_TOKEN)
    else:
        print("Failed to get token:", response.status_code, response.text)


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

# Geospatial files
bus_stops = gpd.read_file(os.path.join(data_dir, "BusStopLocation_Nov2024", "BusStop.shp"))
MRT_stops = pd.read_csv(os.path.join(data_dir, "MRT Stations.csv"))

# Coordinate conversion
transformer = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)
def svy21_to_wgs84(easting, northing):
    lon, lat = transformer.transform(easting, northing)
    return lat, lon

bus_stops['x_coord'] = bus_stops.geometry.apply(lambda geom: geom.x)
bus_stops['y_coord'] = bus_stops.geometry.apply(lambda geom: geom.y)
bus_stops['Latitude'], bus_stops['Longitude'] = zip(*bus_stops.apply(lambda row: svy21_to_wgs84(row['x_coord'], row['y_coord']), axis=1))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
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

    bus_stops['distance'] = bus_stops.apply(
        lambda row: haversine(lat, lon, row['Latitude'], row['Longitude']), axis=1
    )
    nearest_bus_distance = bus_stops['distance'].min()

    return nearest_mrt_distance, nearest_bus_distance

def get_amenity_score(lat, lon, amenity_type):
    df = pd.read_csv(os.path.join(data_dir, f"Amenities_{amenity_type}.csv"))
    scores = []
    for _, row in df.iterrows():
        distance = haversine(lat, lon, row['lat'], row['lon'])
        if distance <= 3000:
            score = 1 * 1000 / (distance + 50)
            scores.append(score)
    return sum(scores)

def get_religion(town):
    df = pd.read_csv(os.path.join(data_dir, "religion_2020.csv"))
    df.rename(columns={"Number": "town"}, inplace=True)
    df['town'] = df['town'].replace('Kallang', 'Kallang/Whampoa')
    central_area = df[df['town'].isin(['Outram', 'Downtown Core', 'River Valley', 'Novena'])].sum(numeric_only=True)
    central_area['town'] = 'CENTRAL AREA'
    df = df[~df['town'].isin(['Outram', 'Downtown Core', 'River Valley', 'Novena', 'Total', 'Others'])]
    df = pd.concat([df, pd.DataFrame([central_area])], ignore_index=True)
    df['town'] = df['town'].str.upper()
    for col in df.columns:
        if col != "town":
            df[col] = pd.to_numeric(df[col], errors='coerce')
    for col in df.columns:
        if col not in ["town", "Total"]:
            df[col] = df[col] / df["Total"]
    return df[df["town"] == town.upper()].reset_index(drop=True)

def get_income(town):
    df = pd.read_csv(os.path.join(data_dir, "resale_price_cleaned.csv"))
    df = df[df['month'] == '2024-12'][['town', 'avg_household_income']].drop_duplicates()
    return df[df["town"] == town].reset_index(drop=True)

def get_flat_type(flat_type):
    types = {
        "1 Room": 1,
        "2 Room": 2,
        "3 Room": 3,
        "4 Room": 4,
        "5 Room": 5,
        "Executive": 6,
        "Multi-Generation": 7
    }
    return types.get(flat_type)

def price_predict(storey_range, flat_type, remaining_lease, postal_code, model):
    town = get_planning_area_from_postal(postal_code)
    lat, lon = get_coordinates_from_postal(postal_code)
    mrt, bus = get_nearest_distances(lat, lon)

    education_score = get_amenity_score(lat, lon, "school")
    shopping_score = get_amenity_score(lat, lon, "shopping")
    food_score = get_amenity_score(lat, lon, "food")
    recreation_score = get_amenity_score(lat, lon, "recreation")
    healthcare_score = get_amenity_score(lat, lon, "healthcare")

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
        'inflation_rate (x100)': 0.3468,
        'resident_unemployment_rate': 2.0,
        'interest_rate': 2.1123,
        'avg_household_income': income_df['avg_household_income'].iloc[0],
        **religion_df.iloc[0].drop(["town", "Total"]).to_dict(),
        'priv_prop': 27531.0,
        'year': 2025,
        'month_num': 4
    }])

    for col in X_input.columns:
        if col in min_max_dict:
            X_input[col] = X_input[col].apply(lambda x: normalize_column(x, col))

    y = model.predict(X_input)
    y = y * (min_max_dict['resale_price']['max'] - min_max_dict['resale_price']['min']) + min_max_dict['resale_price']['min']
    return y[0]

def predict_price_all(t):
    st.title(t['predict1'])
    st.warning(t['predict2'])

    valid_input = True

    postal_code = st.text_input(t['predict3'])

    geospatial_data = pd.read_csv(os.path.join(data_dir, "hdb_geospatial.csv"))
    if postal_code and postal_code not in geospatial_data["postal_code"].values:
        st.warning(t["predictwarning1"])
        valid_input = False

    flat_type = st.selectbox(t['predict4'], 
        ['1 Room', '2 Room', '3 Room', '4 Room', '5 Room', 'Executive', 'Multi-Generation'])
    floor_number = st.number_input(t['predict5'], min_value=1)
    lease_left = st.number_input(t['predict6'], min_value=0, value=80)

    if lease_left > 99:
        st.warning(t["predictwarning2"])
        valid_input = False

    model = joblib.load(os.path.join(data_dir, "model_random_forest.pkl"))

    if st.button(t['predict7'], disabled=not valid_input):
        try:
            predicted_price = price_predict(
                storey_range=floor_number,
                flat_type=flat_type,
                remaining_lease=lease_left,
                postal_code=int(postal_code),
                model=model
            )
            st.write(f"### Predicted Price: ${predicted_price:,.2f}")
        except Exception as e:
            st.warning(t['predict8'])

    st.markdown("---")
    st.markdown(t["contact"])