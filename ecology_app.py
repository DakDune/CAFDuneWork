import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import copy
from io import BytesIO
from matplotlib import cm
import numpy as np

# Custom CSS for background image
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://raw.githubusercontent.com/DakDune/CAFDuneWork/refs/heads/main/dunepicloc.avif");
        background-size: cover;
        background-position: top;
    }
    </style>
    """,
    unsafe_allow_html=True
)




# Title of the app
st.title("Ecological Transect Data Processor")

st.write("")  # Adds a small space
st.markdown("<p style='font-size:18px; color:#FDFD96;'>By Dakota Fee and Maya Bernstein (Awesome people)!! Let me know if there is a problem with the site (@dakotafee@ucsb.edu)</p>", unsafe_allow_html=True)

st.write("")  # Adds a small space

#FOR THE INTERACTIVE DATA INPUT AND TEMPLATE FILE DOWNLOAD
# Load the template only once and store it in session state
template_path = "dune_data_blank.xlsx"

if "sheets_dict" not in st.session_state:
    st.session_state.sheets_dict = pd.read_excel(template_path, sheet_name=None)

sheets_dict = st.session_state.sheets_dict  # Reference from session state

# Section: Download Template File
st.header("Download Template")
with open(template_path, "rb") as file:
    st.download_button("Download Template (xlsx)", file, file_name="template.xlsx")

# Section: Interactive Data Entry
st.subheader("Or Input Data")

#FOR THE DRAG AND DROP
# Upload the Excel file
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    # Load the data from sheets
    positional_df = pd.read_excel(uploaded_file, sheet_name="PositionalCharacteristics")
    transects_df = pd.read_excel(uploaded_file, sheet_name="Transects")
    elevation_df = pd.read_excel(uploaded_file, sheet_name="Elevation")
    readme_df = pd.read_excel(uploaded_file, sheet_name="ReadMe")
    calculations_df = pd.DataFrame()
    # Strip leading/trailing spaces to ensure clean matching
    transects_df['type'] = transects_df['type'].str.strip()
    readme_df['name'] = readme_df['name'].str.strip()
    
    #amend the transects column to have more specific data so there are no duplicate values
    transects_df["transect"] = transects_df["sitename"] + "_" + transects_df["date"].astype(str) + "_" + transects_df["transect"]
    positional_df["transect"] = positional_df["sitename"] + "_" + positional_df["date"].astype(str) + "_" + positional_df["transect"]
    
    # Create a mapping from 'name' to 'native' from readme_df
    name_to_native = readme_df.set_index('name')['native']
    
    # Add 'native' column to transects_df based on 'type' matching 'name'
    transects_df['native'] = transects_df['type'].map(name_to_native)
    
    # Create a mapping from 'name' to 'codetype' in readme_df
    type_to_codetype = readme_df.set_index('name')['codetype']
    # Map the 'codetype' values to transects_df based on 'type'
    transects_df['codetype'] = transects_df['type'].map(type_to_codetype)
    # Fill missing 'codetype' values with "Dead Terrestrial Plant" if 'type' contains "-D"
    transects_df.loc[transects_df['type'].str.contains('-D', na=False), 'codetype'] = "Dead Terrestrial Plant"
    
    
    # Create a mapping for positional information (toe_sea, toe_in, lowest_veg)
    positional_mapping = positional_df.set_index('transect')[['toe_sea', 'toe_in', 'lowest_veg']]
    
    # Map the positional values to transects_df
    transects_df = transects_df.join(positional_mapping, on='transect')
    
    # Calculate if the row starts or ends within the dune
    start_within_dune = (transects_df['start'] <= transects_df['toe_sea']) & (transects_df['start'] >= transects_df['toe_in'])
    end_within_dune = (transects_df['end'] >= transects_df['toe_in']) & (transects_df['end'] <= transects_df['toe_sea'])
    
    # Create the final 'dune' column directly
    transects_df['dune'] = start_within_dune | end_within_dune
    
    
    # Identify if the row is within the vegetated portion of the dune
    transects_df['veg'] = transects_df['start'] <= transects_df['lowest_veg']
    
    #transects_df.drop(columns=["sitename", "date"], inplace=True)
    
    #transect letter
    calculations_df["transect"] = positional_df["transect"]
    #transect name and site name
    calculations_df["sitename"] = positional_df ["sitename"]
    calculations_df["date"] = positional_df["date"]
    # transect length
    calculations_df["tran_length"] = (positional_df["HTS"] - positional_df["eastend"]).abs()
     # dune length
    calculations_df["dune_length"] = positional_df["toe_sea"] - positional_df["toe_in"].abs()
    # vegeted length
    calculations_df["veg_length"] = (positional_df["lowest_veg"] - positional_df["eastend"]).abs()
    
    # -------all cover types------
    
    # EVERYTHING OVER ENTIRE TRANSECT
    calculations_df = calculations_df.merge(
        transects_df.groupby("transect")["cor_length"].sum().reset_index(),
        on="transect", how="left"
    )
    calculations_df["pctcov_all_whole"] = calculations_df["cor_length"] / calculations_df["tran_length"]
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # EVERYTHING OVER DUNE PORTION OF TRANSECT
    dune_df = transects_df[transects_df["dune"] == True] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    
    calculations_df = calculations_df.merge(dune_df, on="transect", how="left")
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)  # Fill missing values with 0
    calculations_df["pctcov_all_dune"] = calculations_df["cor_length"] / calculations_df["dune_length"]
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # EVERYTHING OVER VEGETATED PORTION OF TRANSECT
    veg_df = transects_df[transects_df["veg"] == True] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    
    calculations_df = calculations_df.merge(veg_df, on="transect", how="left")
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)  # Fill missing values with 0
    calculations_df["pctcov_all_veg"] = calculations_df["cor_length"] / calculations_df["veg_length"]
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    
    #_______________TRANSECT WIDE_____
    
    # Convert codetype to string and replace NaN values with "Unknown"
    transects_df["codetype"] = transects_df["codetype"].astype(str).fillna("Unknown")
    # Get unique codetype values
    unique_codetypes = transects_df["codetype"].unique()
    
    # Loop through each codetype and calculate percent cover
    for codetype in unique_codetypes:
        codetype_clean = f"pctcov_{codetype.replace(' ', '')}_transect"  # Remove spaces for column name
        # filter transect_df to only include rows where codetype matches current iteration
        temp_df = transects_df[transects_df["codetype"] == codetype] \
            .groupby("transect", as_index=False)["cor_length"].sum() # sums the cor_length of each veg category for each transect
    
        # Merge with calculations_df
        calculations_df = calculations_df.merge(temp_df, on="transect", how="left")
        # Fill NaN values in 'cor_length' with 0 before calculating percent cover
        calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
        # Calculate percent cover for the codetype
        calculations_df[codetype_clean] = calculations_df["cor_length"] / calculations_df["tran_length"]
        # Drop 'cor_length' column
        calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # native/nonnative plants
    
    # Define column name for native terrestrial plant percent cover
    native_terrestrial_col = "pctcov_TerrestrialPlantNative_transect"
    # Filter for only native terrestrial plants
    native_terrestrial_df = transects_df[(transects_df["codetype"] == "Terrestrial Plant") & (transects_df["native"] == 1.0)] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    # Merge with calculations_df
    calculations_df = calculations_df.merge(native_terrestrial_df, on="transect", how="left")
    # Fill NaN values in 'cor_length' with 0 before calculating percent cover
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
    # Calculate percent cover for native terrestrial plants
    calculations_df[native_terrestrial_col] = calculations_df["cor_length"] / calculations_df["tran_length"]
    # Drop 'cor_length' column
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # Define column name for native terrestrial plant percent cover
    nonnative_terrestrial_col = "pctcov_TerrestrialPlantNonnative_transect"
    # Filter for only nonnative terrestrial plants
    nonnative_terrestrial_df = transects_df[(transects_df["codetype"] == "Terrestrial Plant") & (transects_df["native"] == 0.0)] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    # Merge with calculations_df
    calculations_df = calculations_df.merge(nonnative_terrestrial_df, on="transect", how="left")
    # Fill NaN values in 'cor_length' with 0 before calculating percent cover
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
    # Calculate percent cover for native terrestrial plants
    calculations_df[nonnative_terrestrial_col] = calculations_df["cor_length"] / calculations_df["tran_length"]
    # Drop 'cor_length' column
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    
    
    #--------DUNE----------
    
    # Loop to calculate percent cover for each codetype over the dune portion of the transect
    for codetype in unique_codetypes:
        codetype_clean_dune = f"pctcov_{codetype.replace(' ', '')}_dune"  # Clean column name for dune
        # filter transect_df to only include rows where codetype matches current iteration
        temp_df_dune = transects_df[(transects_df["codetype"] == codetype) & (transects_df["dune"] == True)] \
            .groupby("transect", as_index=False)["cor_length"].sum() # sums the cor_length of each veg category for each transect
    
        # Merge with calculations_df
        calculations_df = calculations_df.merge(temp_df_dune, on="transect", how="left")
        # Fill NaN values in 'cor_length' with 0 before calculating percent cover
        calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
        # Calculate percent cover for the dune portion
        calculations_df[codetype_clean_dune] = calculations_df["cor_length"] / calculations_df["dune_length"]
        # Drop 'cor_length' column
        calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # native/nonnative plants
    
    # Define column name for native terrestrial plant percent cover
    native_terrestrial_dune_col = "pctcov_TerrestrialPlantNative_dune"
    # Filter for only native terrestrial plants in the dune
    native_terrestrial_dune_df = transects_df[(transects_df["codetype"] == "Terrestrial Plant") & (transects_df["native"] == 1.0) & (transects_df["dune"]== True)] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    # Merge with calculations_df
    calculations_df = calculations_df.merge(native_terrestrial_dune_df, on="transect", how="left")
    # Fill NaN values in 'cor_length' with 0 before calculating percent cover
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
    # Calculate percent cover for native terrestrial plants
    calculations_df[native_terrestrial_dune_col] = calculations_df["cor_length"] / calculations_df["dune_length"]
    # Drop 'cor_length' column
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # Define column name for native terrestrial plant percent cover
    nonnative_terrestrial_dune_col = "pctcov_TerrestrialPlantNonnative_dune"
    # Filter for only nonnative terrestrial plants
    nonnative_terrestrial_dune_df = transects_df[(transects_df["codetype"] == "Terrestrial Plant") & (transects_df["native"] == 0.0) & (transects_df["dune"]== True)] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    # Merge with calculations_df
    calculations_df = calculations_df.merge(nonnative_terrestrial_dune_df, on="transect", how="left")
    # Fill NaN values in 'cor_length' with 0 before calculating percent cover
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
    # Calculate percent cover for native terrestrial plants
    calculations_df[nonnative_terrestrial_dune_col] = calculations_df["cor_length"] / calculations_df["dune_length"]
    # Drop 'cor_length' column
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    #------------VEGETATED PORTION-----------------
    
    # Loop to calculate percent cover for each codetype over the dune portion of the transect
    for codetype in unique_codetypes:
        codetype_clean_veg = f"pctcov_{codetype.replace(' ', '')}_veg"  # Clean column name for dune
        # filter transect_df to only include rows where codetype matches current iteration
        temp_df_veg = transects_df[(transects_df["codetype"] == codetype) & (transects_df["veg"] == True)] \
            .groupby("transect", as_index=False)["cor_length"].sum() # sums the cor_length of each veg category for each transect
    
        # Merge with calculations_df
        calculations_df = calculations_df.merge(temp_df_veg, on="transect", how="left")
        # Fill NaN values in 'cor_length' with 0 before calculating percent cover
        calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
        # Calculate percent cover for the dune portion
        calculations_df[codetype_clean_veg] = calculations_df["cor_length"] / calculations_df["veg_length"]
        # Drop 'cor_length' column
        calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # native/nonnative plants
    
    # Define column name for native terrestrial plant percent cover
    native_terrestrial_veg_col = "pctcov_TerrestrialPlantNative_veg"
    # Filter for only native terrestrial plants in the dune
    native_terrestrial_veg_df = transects_df[(transects_df["codetype"] == "Terrestrial Plant") & (transects_df["native"] == 1.0) & (transects_df["veg"]== True)] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    # Merge with calculations_df
    calculations_df = calculations_df.merge(native_terrestrial_veg_df, on="transect", how="left")
    # Fill NaN values in 'cor_length' with 0 before calculating percent cover
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
    # Calculate percent cover for native terrestrial plants
    calculations_df[native_terrestrial_veg_col] = calculations_df["cor_length"] / calculations_df["veg_length"]
    # Drop 'cor_length' column
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    # Define column name for native terrestrial plant percent cover
    nonnative_terrestrial_veg_col = "pctcov_TerrestrialPlantNonnative_veg"
    # Filter for only nonnative terrestrial plants
    nonnative_terrestrial_veg_df = transects_df[(transects_df["codetype"] == "Terrestrial Plant") & (transects_df["native"] == 0.0) & (transects_df["veg"]== True)] \
        .groupby("transect", as_index=False)["cor_length"].sum()
    # Merge with calculations_df
    calculations_df = calculations_df.merge(nonnative_terrestrial_veg_df, on="transect", how="left")
    # Fill NaN values in 'cor_length' with 0 before calculating percent cover
    calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
    # Calculate percent cover for native terrestrial plants
    calculations_df[nonnative_terrestrial_veg_col] = calculations_df["cor_length"] / calculations_df["veg_length"]
    # Drop 'cor_length' column
    calculations_df.drop(columns=["cor_length"], inplace=True)
    
    
    #______SPECIES SPECIFIC_____________
    
    # Get unique species names
    unique_species = transects_df["type"].dropna().unique()
    
    # Loop through each species
    for species in unique_species:
        species_clean = f"pctcov_{species.replace(' ', '')}_whole"  # Remove spaces for column name
        
        # Percent cover over entire transect
        temp_df = transects_df[transects_df["type"] == species] \
            .groupby("transect", as_index=False)["cor_length"].sum()
        
        calculations_df = calculations_df.merge(temp_df, on="transect", how="left")
        calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
        calculations_df[species_clean] = calculations_df["cor_length"] / calculations_df["tran_length"]
        calculations_df.drop(columns=["cor_length"], inplace=True)
    
        # Percent cover over dune portion
        species_clean_dune = f"pctcov_{species.replace(' ', '')}_dune"
        temp_df = transects_df[(transects_df["type"] == species) & (transects_df["dune"] == True)] \
            .groupby("transect", as_index=False)["cor_length"].sum()
        
        calculations_df = calculations_df.merge(temp_df, on="transect", how="left")
        calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
        calculations_df[species_clean_dune] = calculations_df["cor_length"] / calculations_df["dune_length"]
        calculations_df.drop(columns=["cor_length"], inplace=True)
    
        # Percent cover over vegetated portion
        species_clean_veg = f"pctcov_{species.replace(' ', '')}_veg"
        temp_df = transects_df[(transects_df["type"] == species) & (transects_df["veg"] == True)] \
            .groupby("transect", as_index=False)["cor_length"].sum()
        
        calculations_df = calculations_df.merge(temp_df, on="transect", how="left")
        calculations_df["cor_length"] = calculations_df["cor_length"].fillna(0)
        calculations_df[species_clean_veg] = calculations_df["cor_length"] / calculations_df["veg_length"]
        calculations_df.drop(columns=["cor_length"], inplace=True)


    
    # Display DataFrame
    st.subheader("Processed Transect Data")
    st.dataframe(calculations_df)

    zone_option = st.radio(
        "Select the transect portion to view percent cover for:",
        ("whole", "dune", "veg"),
        horizontal=True
    )

    # Step 1: Let user choose a site
    sites = calculations_df["sitename"].unique()
    selected_site = st.selectbox("Select a Site", sorted(sites))
    
    # Step 2: Let user choose a date from that site
    dates = calculations_df[calculations_df["sitename"] == selected_site]["date"].unique()
    selected_date = st.selectbox("Select a Survey Date", sorted(dates))
    
    # Step 3: Filter the dataframe
    filtered_df = calculations_df[
        (calculations_df["sitename"] == selected_site) &
        (calculations_df["date"] == selected_date)
    ]
    
    # Step 4: Define pastel colormap function
    def get_pastel_colors(n):
        base_cmap = cm.get_cmap('Pastel1' if n <= 9 else 'Pastel2')  # Pastel1: 9 colors, Pastel2: 8
        if n > base_cmap.N:
            return [base_cmap(i / n) for i in range(n)]
        else:
            return [base_cmap(i) for i in range(n)]
    
    # Step 5: Prepare the dataframe for plotting
    zone_suffix = f"_{zone_option}"
    stack_df = filtered_df[["transect"] + [col for col in filtered_df.columns if col.endswith(zone_suffix)]].copy()
    stack_df.columns = ["transect"] + [col.replace("pctcov_", "").replace(zone_suffix, "") for col in stack_df.columns[1:]]
    
    # Remove species columns with all zero percent cover
    nonzero_cols = [col for col in stack_df.columns[1:] if stack_df[col].sum() > 0]
    stack_df = stack_df[["transect"] + nonzero_cols]
    
    # Plot if there's data to show
    if len(stack_df.columns) > 1:
        stack_df.set_index("transect", inplace=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = get_pastel_colors(len(stack_df.columns))
        stack_df.plot(kind="barh", stacked=True, ax=ax, color=colors)
        ax.set_title(f"Species Composition – {selected_site}, {selected_date} ({zone_option.capitalize()})")
        ax.set_xlabel("Percent Cover")
        ax.set_ylabel("Transect")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No species with non-zero coverage for this selection.")



    # Allow user to download processed data
    st.subheader("Download Processed Data")
    csv = calculations_df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "processed_transect_data.csv", "text/csv")

