import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pyproj import Transformer

st.markdown(
    "<h1 style='color: #2E86C1; white-space: nowrap; margin-left: -100px;'>🚀  Welcome to the DQ Projects/Operations app 🚀</h1>",
    unsafe_allow_html=True
)


st.markdown('# Please select the TAM you would like to explore on the left side menu')

