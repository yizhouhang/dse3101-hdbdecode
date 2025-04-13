import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.features import CustomIcon
from dynamic_filter import dynamic_filter

def ideal_home(t):
    tab1, tab2 = st.tabs([t['ideal9'], t['ideal10']])

    with tab1:
        @st.cache_data
        def load_data():
            return pd.read_csv("find_your_ideal_home.csv")

        df = load_data()
        df["postal_code"] = df["postal_code"].astype(str).str.zfill(6)
        df = df.drop_duplicates(subset=["postal_code", "flat_type", "storey_range"])
        df.columns = df.columns.str.strip()

        st.title(t['ideal11'])
        st.warning(t['ideal12'])
        st.write("")

        # --- Required Filters ---
        budget_range = st.slider(t['ideal13'], 220000, 1550000, (400000, 700000), step=10000, format="%d")
        flat_types_available = sorted(df["flat_type"].dropna().unique())

        st.write("")
        st.write("")

        flat_types = st.multiselect(t['ideal14'], flat_types_available)
        st.write("")
        st.write("")

        filter_values = {}
        st.write(t["ideal31"])
        # --- Expandable Optional Filters ---
        with st.expander(t['ideal15']):
            st.markdown(t['ideal16'])
            if st.checkbox(t['ideal17']):
                filter_values['town'] = st.multiselect(t['ideal18'], sorted(df['town'].dropna().unique()))
            if st.checkbox(t['ideal19']):
                filter_values['storey_range'] = st.slider(t['ideal20'], 1, 50, (5, 25))
            if st.checkbox(t['ideal21']):
                filter_values['remaining_lease'] = st.slider(t['ideal22'], 1, 99, (60, 99))

        with st.expander(t['ideal23']):
            st.markdown(t['ideal24'])

            if st.checkbox(t['ideal25']):
                mrt_choice = st.selectbox(t['ideal26'], ['<100m', '<500m', '<1km', '<2km', '<3km'])
                filter_values['nearest_mrt_distance'] = {
        '<100m': 100, '<500m': 500, '<1km': 1000, '<2km': 2000, '<3km': 3000
    }[mrt_choice]


            if st.checkbox(t['ideal27']):
                bus_choice = st.selectbox(t['ideal28'], ['<100m', '<500m', '<1km'])
                filter_values['nearest_bus_distance'] = {
        '<100m': 100, '<500m': 500, '<1km': 1000
    }[bus_choice]


        with st.expander(t["ideal29"]):
            st.markdown(t["ideal30"])
            for score in ["schools", "shopping", "food", "recreation", "healthcare"]:
                label = t["ideal36"].format(score=t[score].capitalize())  
                if st.checkbox(label):
                    val = st.radio(
                        f"{t[score]} Score",
                        options=[1, 2, 3, 4, 5],
                        index=2,
                        horizontal=True,
                        key=f"radio_{score}"
                    )
                    filter_values[score] = val
        st.write("")
        st.write("")
        st.caption(t['amenity_caption'])
        
        with st.expander(t['amenity_expander_title']):
                st.markdown(t['amenity_expander_description'])
      
            # --- Filter Button ---
        if st.button(t['ideal37']):
            selected_flat_types = flat_types if flat_types else df["flat_type"].unique().tolist()
            results = dynamic_filter(df, budget_range, selected_flat_types, filter_values)
            st.session_state.filtered_results = results

        if "filtered_results" in st.session_state:
            results = st.session_state.filtered_results


                # Prepare and rename DataFrame...
            display_df = results[[
                    "town", "prediction_reverted", "remaining_lease_reverted", "flat_type", 
                    "storey_range", "address", "postal_code", "nearest_mrt_name", "nearest_bus_name",
                    "education_score", "shopping_score", "food_score", "recreation_score", "healthcare_score"
                ]].copy()

            display_df.rename(columns={
                    "town": "Town",
                    "prediction_reverted": "Predicted Price (SGD)",
                    "remaining_lease_reverted": "Remaining Lease (Years)",
                    "flat_type": "Flat Type",
                    "storey_range": "Storey Range",
                    "address": "Address",
                    "postal_code": "Postal Code",
                    "nearest_mrt_name": "Nearest MRT",
                    "nearest_bus_name": "Nearest Bus Stop",
                    "education_score": 'Schools',
                    "shopping_score": "Shopping",
                    "food_score": "Food",
                    "recreation_score": "Recreation",
                    "healthcare_score": "Healthcare"
                }, inplace=True)

                # Format numeric columns
            display_df["Predicted Price (SGD)"] = display_df["Predicted Price (SGD)"].round(0).astype(int)
            display_df["Remaining Lease (Years)"] = display_df["Remaining Lease (Years)"].astype(float).round(1)
            for col in ["Schools", "Shopping", "Food", "Recreation", "Healthcare"]:
                display_df[col] = display_df[col].astype(float).round(1)

            if len(display_df)==0:
                st.warning(t['ideal38'])

            else: 
                # Sorting

                columns_to_display = [
                'Town', 'Address', 'Postal Code', 'Predicted Price (SGD)', 'Flat Type',
                'Storey Range', 'Remaining Lease (Years)', 'Schools', 'Shopping', 'Food',
                'Recreation', 'Healthcare']
                display_df = display_df[columns_to_display]

            sort_option = st.selectbox(
                t["ideal39"],
                [t["ideal40"], t["ideal41"], t["ideal42"]],
                key="sort_option_selector"
            )

            if sort_option == t["ideal40"]:  # Cheapest
                display_df = display_df.sort_values("Predicted Price (SGD)")
            elif sort_option == t["ideal41"]:  # Longest Lease
                display_df = display_df.sort_values("Remaining Lease (Years)", ascending=False)
            elif sort_option == t["ideal42"]:  # Best Amenities
                display_df["Avg Amenity Score"] = display_df[["Schools", "Shopping", "Food", "Recreation", "Healthcare"]].mean(axis=1)
                display_df = display_df.sort_values("Avg Amenity Score", ascending=False)

            display_df = display_df.reset_index(drop=True)
            display_df.index += 1

            st.dataframe(display_df.head(10), use_container_width=True)
            st.caption(t["ideal43"].format(n=len(display_df), sort_option=sort_option))
            st.warning(t["ideal44"])

              

        

    with tab2:
        st.title(t["ideal1"])

        geospatial_data = pd.read_csv("hdb_geospatial.csv")

        if "postal_codes" not in st.session_state:
            st.session_state.postal_codes = []

        code = st.text_input(t["ideal2"])

        if st.button(t["ideal3"]):
            if code and code not in st.session_state.postal_codes:
                if code in geospatial_data["postal_code"].values:
                    st.session_state.postal_codes.append(code)
                    
                else:
                    st.warning(t["ideal4"])

        st.subheader(t["ideal5"])

        cols = st.columns(4)  

        for i, code in enumerate(st.session_state.postal_codes):
            col = cols[i % 4]
            with col:
                st.markdown(f"""
                    <div style='
                        border: 1px solid #ccc;
                        padding: 10px;
                        border-radius: 10px;
                        margin-bottom: 10px;
                        background-color: #f9f9f9;
                        text-align: center;
                    '>
                        <b>{code}</b>
                    </div>
                """, unsafe_allow_html=True)

                if st.button(t["ideal6"], key=f"remove_{code}"):
                    st.session_state.postal_codes.remove(code)
                    st.rerun()


        filtered_data = geospatial_data[geospatial_data["postal_code"].isin(st.session_state.postal_codes)]

        if not filtered_data.empty:
            m = folium.Map(location=[1.3521, 103.8198], zoom_start=12)
            for _, row in filtered_data.iterrows():
                popup_text = (
                    f"Postal Code: {row['postal_code']}<br>"
                    f"Nearest MRT: {row['nearest_mrt_name']} ({int(row['nearest_mrt_distance'])}m)<br>"
                    f"Nearest Bus Stop: {row['nearest_bus_name']} ({int(row['nearest_bus_distance'])}m)"
                )
                custom_icon = CustomIcon(
                    icon_image="location.png",  
                    icon_size=(45, 45),  
                )   
                folium.Marker(
                    location=[row["latitude"], row["longitude"]],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon = custom_icon
                ).add_to(m)

            # st.markdown("### 🗺️ Map of Selected HDBs")
            st_folium(m, width=1000, height=500)
        else:
            st.info(t['ideal8'])
        
        if not filtered_data.empty:
            display_df = filtered_data[[
                "postal_code",
                "nearest_mrt_name",
                "nearest_mrt_distance",
                "nearest_bus_name",
                "nearest_bus_distance"
            ]].rename(columns={
                "postal_code": "Postal Code",
                "nearest_mrt_name": "Nearest MRT",
                "nearest_mrt_distance": "MRT Distance (m)",
                "nearest_bus_name": "Nearest Bus Stop",
                "nearest_bus_distance": "Bus Stop Distance (m)"
            })

            # Round the distances to the nearest whole number
            display_df["MRT Distance (m)"] = display_df["MRT Distance (m)"].round(0).astype(int)
            display_df["Bus Stop Distance (m)"] = display_df["Bus Stop Distance (m)"].round(0).astype(int)

            # Drop the index column (row number)
            display_df = display_df.reset_index(drop=True)
            display_df.index +=1

            st.subheader(t["ideal7"])
            st.dataframe(display_df, use_container_width=True)


                
        st.markdown("---")
        st.markdown(t["contact"])

