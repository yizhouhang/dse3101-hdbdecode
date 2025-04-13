import streamlit as st

def homepage(t):
    st.title(t["title"])
    st.write(t["description"])
    
    st.markdown("---")
    st.header(t["homepage1"])

    st.markdown(t["homepage2"])
    st.markdown(t["homepage3"])
    if st.button(t["homepage4"], key="home_trend_btn"):
        st.query_params["page"] = "HDB Price Trend"
        st.session_state.page = "HDB Price Trend"
        st.rerun()
            
    left_col, right_col = st.columns([1.3, 1]) 

    with left_col:

        st.markdown(t["homepage5"])
        st.markdown(t["homepage6"])
        if st.button(t["homepage7"], key="home_predict_btn"):
            st.query_params["page"] = "Predict Your HDB Price"
            st.session_state.page = "Predict Your HDB Price"
            st.rerun()

        st.markdown(t["homepage8"])
        st.markdown(t["homepage9"])
        if st.button(t["homepage10"], key="home_finder_btn"):
            st.query_params["page"] = "Find Your Ideal Home"
            st.session_state.page = "Find Your Ideal Home"
            st.rerun()

    with right_col:
        st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
        st.image("hdb5.jpeg", use_container_width=True)


    
    st.markdown("---")
    st.markdown(t["contact"])
