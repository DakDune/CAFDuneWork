import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import copy
from io import BytesIO

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
st.markdown("<p style='font-size:18px; color:#FDFD96;'>By Dakota Fee and Maya Bernstein (Awesome people)!! Let me know if there is a problem with the site (@dakotafee@ucsb.edu) and I will forward to Maya</p>", unsafe_allow_html=True)

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
    positional_df = pd.read_excel(file_path, sheet_name="PositionalCharacteristics")
    transects_df = pd.read_excel(file_path, sheet_name="Transects")
    elevation_df = pd.read_excel(file_path, sheet_name="Elevation")
    readme_df = pd.read_excel(file_path, sheet_name="ReadMe")
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

    pastel_palette = ["#cdb4db",  # light purple
                      "#b5ead7",  # light green
                      "#a0c4ff",  # ocean blue
                      "#ffe066",  # golden yellow
                      "#fbc4ab",  # optional coral-pink for variety
                      "#fdffb6",  # pale yellow
                      "#9bf6ff",  # light cyan
                      "#d0f4de"]  # mint


    # Filter columns based on zone
    zone_suffix = f"_{zone_option}"
    pctcov_cols = [col for col in calculations_df.columns if col.startswith("pctcov_") and col.endswith(zone_suffix)]
    
    # Build a dataframe of average percent cover
    avg_df = calculations_df[pctcov_cols].mean().reset_index()
    avg_df.columns = ["Species", "Percent Cover"]
    
    # Clean up species names
    avg_df["Species"] = avg_df["Species"].str.replace("pctcov_", "").str.replace(zone_suffix, "")
    avg_df["Species"] = avg_df["Species"].str.replace(r"([a-z])([A-Z])", r"\1 \2", regex=True)
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    avg_df.plot(kind="bar", x="Species", y="Percent Cover", ax=ax, legend=False, color=pastel_palette[:len(avg_df)])
    ax.set_title(f"Average Percent Cover by Species ({zone_option.capitalize()} Transects)")
    ax.set_ylabel("Percent Cover")
    ax.set_xlabel("Species")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    st.pyplot(fig)

    # Create a stacked bar dataframe
    stack_df = calculations_df[["transect"] + pctcov_cols].copy()
    stack_df.columns = ["transect"] + [col.replace("pctcov_", "").replace(zone_suffix, "") for col in pctcov_cols]
    
    # Set transect as index for plotting
    stack_df.set_index("transect", inplace=True)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    stack_df.plot(kind="bar", stacked=True, ax=ax2, colormap=pastel_palette[:stack_df.shape[1]])
    ax2.set_title(f"Species Composition by Transect ({zone_option.capitalize()} Transects)")
    ax2.set_ylabel("Percent Cover")
    ax2.set_xlabel("Transect")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    st.pyplot(fig2)



    # Allow user to download processed data
    st.subheader("Download Processed Data")
    csv = calculations_df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "processed_transect_data.csv", "text/csv")

