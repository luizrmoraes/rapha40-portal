import streamlit as st
import psycopg2


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        st.secrets["supabase_db"]["url"]
    )