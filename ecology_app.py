import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Title of the app
st.title("Ecological Transect Data Processor")

# Upload the Excel file
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    # Load the data from sheets
    positional_df = pd.read_excel(uploaded_file, sheet_name="PositionalCharacteristics")
    transects_df = pd.read_excel(uploaded_file, sheet_name="Transects")
    readme_df = pd.read_excel(uploaded_file, sheet_name="ReadMe")

    # Clean whitespace
    transects_df["type"] = transects_df["type"].str.strip()
    readme_df["name"] = readme_df["name"].str.strip()

    # Map native status
    name_to_native = readme_df.set_index("name")["native"]
    transects_df["native"] = transects_df["type"].map(name_to_native)

    # Initialize calculations DataFrame
    calculations_df = pd.DataFrame()
    calculations_df["transect"] = positional_df["transect"]
    calculations_df["tran_length"] = positional_df["HTS"]
    calculations_df["dune_length"] = positional_df["toe_sea"] - positional_df["toe_in"]
    calculations_df["veg_length"] = positional_df["lowest_veg"]

    # Percent cover calculations
    pct_cover_all_whole = transects_df.groupby("transect")["cor_length"].sum() / calculations_df.set_index("transect")["tran_length"]
    calculations_df["pct_cover_all_whole"] = calculations_df["transect"].map(pct_cover_all_whole)

    vegetation_df = transects_df[transects_df["type"].str.len().isin([4, 5])]
    veg_cover_sum = vegetation_df.groupby("transect")["cor_length"].sum()
    calculations_df["pct_cover_veg_whole"] = calculations_df["transect"].map(veg_cover_sum / calculations_df.set_index("transect")["tran_length"])

    native_vegetation_df = transects_df[(transects_df["type"].str.len().isin([4, 5])) & (transects_df["native"] == 1.0)]
    native_veg_cover_sum = native_vegetation_df.groupby("transect")["cor_length"].sum()
    calculations_df["pct_cover_native_veg_whole"] = calculations_df["transect"].map(native_veg_cover_sum / calculations_df.set_index("transect")["tran_length"])

    non_native_vegetation_df = transects_df[(transects_df["type"].str.len().isin([4, 5])) & (transects_df["native"] == 0.0)]
    non_native_veg_cover_sum = non_native_vegetation_df.groupby("transect")["cor_length"].sum()
    calculations_df["pct_cover_non_native_veg_whole"] = calculations_df["transect"].map(non_native_veg_cover_sum / calculations_df.set_index("transect")["tran_length"])

    # Display DataFrame
    st.subheader("Processed Transect Data")
    st.dataframe(calculations_df)

    # Visualization
    st.subheader("Vegetation Cover Across Transects")

    fig, ax = plt.subplots()
    ax.bar(calculations_df["transect"], calculations_df["pct_cover_veg_whole"], color="green", label="Total Vegetation")
    ax.bar(calculations_df["transect"], calculations_df["pct_cover_native_veg_whole"], color="blue", label="Native Vegetation")
    ax.bar(calculations_df["transect"], calculations_df["pct_cover_non_native_veg_whole"], color="red", label="Non-Native Vegetation")
    ax.set_xlabel("Transect")
    ax.set_ylabel("Percent Cover")
    ax.legend()
    st.pyplot(fig)

    # Allow user to download processed data
    st.subheader("Download Processed Data")
    csv = calculations_df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "processed_transect_data.csv", "text/csv")

