import streamlit as st
import pandas as pd
from pathlib import Path
from pandas.errors import EmptyDataError

st.set_page_config(layout="wide")
st.title("📂 Open Positions")

file = Path("data/open_positions.csv")
try:
    df = pd.read_csv(file) if file.exists() else pd.DataFrame()
except EmptyDataError:
    df = pd.DataFrame()

if df.empty:
    st.info("No open paper positions yet.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)
