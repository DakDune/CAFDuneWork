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
st.markdown("<p style='font-size:18px; color:#FDFD96;'>By Dakota Fee and Maya Bernstein!! Let me know if there is a problem with the site @dakotafee@ucsb.edu</p>", unsafe_allow_html=True)

st.write("")  # Adds a small space

#FOR THE INTERACTIVE DATA INPUT AND TEMPLATE FILE DOWNLOAD
# Load the template file (ensure this path is correct)
template_path = "new_dune_data_blank.xlsx"
sheets_dict = pd.read_excel(template_path, sheet_name=None)  # Load all sheets

# Section: Download Template File
st.header("Download Template")
with open(template_path, "rb") as file:
    st.download_button("Download Template (xlsx)", file, file_name="template.xlsx")

# Section: Interactive Data Entry
st.subheader("Or Input Data Manually")

if st.button("Enter Data"):
    st.session_state.show_table = True

if st.session_state.get("show_table", False):
    # Let the user pick a sheet
    sheet_names = list(sheets_dict.keys())
    selected_sheet = st.selectbox("Select a sheet to edit:", sheet_names)

    # Initialize session state for storing table data (deep copy to prevent unintended resets)
    if "input_tables" not in st.session_state:
        st.session_state.input_tables = copy.deepcopy(sheets_dict)

    # Retrieve current table data
    current_df = st.session_state.input_tables[selected_sheet]

    # Display interactive table
    edited_df = st.data_editor(
        current_df, 
        num_rows="dynamic",
        height=400,  # Adjust height (default is 300)
        width=800,   # Adjust width (optional)
        key="data_editor"  # Unique key prevents unnecessary resets
    )

    # Button to apply changes (prevents live updates from triggering reruns)
    if st.button("Save Changes"):
        st.session_state.input_tables[selected_sheet] = edited_df
        st.success("Changes saved!")

    # Convert dataframe to .xlsx for download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet, df in st.session_state.input_tables.items():
            df.to_excel(writer, index=False, sheet_name=sheet)
        writer.close()
    output.seek(0)

    st.download_button(
        "Download Entered Data as .xlsx",
        output,
        file_name="entered_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

#FOR THE DRAG AND DROP
# Upload the Excel file
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    # Load the data from sheets
    positional_df = pd.read_excel(uploaded_file, sheet_name="PositionalCharacteristics")
    transects_df = pd.read_excel(uploaded_file, sheet_name="Transects")
    readme_df = pd.read_excel(uploaded_file, sheet_name="ReadMe")
    calculations_df = pd.DataFrame()
    # Strip leading/trailing spaces to ensure clean matching
    transects_df['type'] = transects_df['type'].str.strip()
    readme_df['name'] = readme_df['name'].str.strip()
    
    # Create a mapping from 'name' to 'native' from readme_df
    name_to_native = readme_df.set_index('name')['native']
    
    # Add 'native' column to transects_df based on 'type' matching 'name'
    transects_df['native'] = transects_df['type'].map(name_to_native)
    
    # Add a new column indicating if 'type' is vegetation (4 or 5 characters long)
    transects_df['vegetation'] = transects_df['type'].str.len().isin([4, 5])
    
    # Create a mapping for positional information (toe_sea, toe_in, lowest_veg)
    positional_mapping = positional_df.set_index('transect')[['toe_sea', 'toe_in', 'lowest_veg']]
    
    # Map the positional values to transects_df
    transects_df = transects_df.join(positional_mapping, on='transect')
    
    # Identify if the start and end positions are within the dune
    transects_df['start_within_dune'] = (transects_df['start'] <= transects_df['toe_sea']) & (transects_df['start'] >= transects_df['toe_in'])
    transects_df['end_within_dune'] = (transects_df['end'] >= transects_df['toe_in']) & (transects_df['end'] <= transects_df['toe_sea'])
    
    # Create the final 'dune' column by checking if either start or end is within the dune
    transects_df['dune'] = transects_df['start_within_dune'] | transects_df['end_within_dune']
    
    # Identify if the row is within the vegetated portion of the dune
    transects_df['veg'] = transects_df['start'] <= transects_df['lowest_veg']

    #transect letter
    calculations_df["transect"] = positional_df["transect"]
    
    # transect length
    calculations_df["tran_length"] = positional_df["HTS"]  
    
    # dune length
    dune_length = positional_df["toe_sea"] - positional_df["toe_in"]
    calculations_df["dune_length"] = dune_length
    
    #vegeted length
    calculations_df["veg_length"] = positional_df["lowest_veg"]  
    
    #percent cover of everything over entire transect length
    pct_cover_all_whole = transects_df.groupby("transect")["cor_length"].sum() / calculations_df.set_index("transect")["tran_length"]
    calculations_df["pct_cover_all_whole"] = calculations_df["transect"].map(pct_cover_all_whole)
    
    #----- veg over whole transect
    
    # Filter the rows where 'type' contains a four or five letter code
    vegetation_df = transects_df[transects_df['type'].str.len().isin([4, 5])]
    
    # Sum the 'cor_length' for those rows
    veg_cover_sum = vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of vegetation over the entire transect
    pct_cover_veg_whole = veg_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_veg_whole"] = calculations_df["transect"].map(pct_cover_veg_whole)
    
    #----- native veg whole transect
    
    # Filter the rows where 'type' contains a four or five letter code and 'native' is 1.0
    native_vegetation_df = transects_df[(transects_df['type'].str.len().isin([4, 5])) & (transects_df['native'] == 1.0)]
    
    # Sum the 'cor_length' for those rows
    native_veg_cover_sum = native_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of native vegetation over the entire transect
    pct_cover_native_veg_whole = native_veg_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_native_veg_whole"] = calculations_df["transect"].map(pct_cover_native_veg_whole)
    
    #----- nonnative veg whole transect
    
    # Filter the rows where 'type' contains a four or five letter code and 'native' is 0.0
    non_native_vegetation_df = transects_df[(transects_df['type'].str.len().isin([4, 5])) & (transects_df['native'] == 0.0)]
    
    # Sum the 'cor_length' for those rows
    non_native_veg_cover_sum = non_native_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of non-native vegetation over the entire transect
    pct_cover_non_native_veg_whole = non_native_veg_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_non_native_veg_whole"] = calculations_df["transect"].map(pct_cover_non_native_veg_whole)
    
    #------- all cover along dune
    
    # Filter for rows where 'dune' is True
    dune_df = transects_df[transects_df["dune"] == True]
    
    # Sum the 'cor_length' for each transect
    dune_cover_sum = dune_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'dune_length' from calculations_df
    pct_cover_dune = dune_cover_sum / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_dune"] = calculations_df["transect"].map(pct_cover_dune)
    
    #----- veg cover dune
    
    # Filter for rows where both 'vegetation' and 'dune' are True
    dune_vegetation_df = transects_df[(transects_df["vegetation"] == True) & (transects_df["dune"] == True)]
    
    # Sum the 'cor_length' for each transect for only vegetation in the dune portion
    veg_cover_dune_sum = dune_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'dune_length' from calculations_df
    pct_cover_veg_dune = veg_cover_dune_sum / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_veg_dune"] = calculations_df["transect"].map(pct_cover_veg_dune)
    
    # ------ native cover dune
    # Filter for rows where 'vegetation' is True, 'dune' is True, and 'native' is 1.0
    native_dune_veg_df = transects_df[(transects_df["vegetation"] == True) & 
                                      (transects_df["dune"] == True) & 
                                      (transects_df["native"] == 1.0)]
    
    # Sum the 'cor_length' for each transect for only native vegetation in the dune portion
    native_veg_cover_dune_sum = native_dune_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'dune_length' from calculations_df
    pct_cover_native_veg_dune = native_veg_cover_dune_sum / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_native_veg_dune"] = calculations_df["transect"].map(pct_cover_native_veg_dune)
    
    # ------ nonnative cover dune
    # Filter for rows where 'vegetation' is True, 'dune' is True, and 'native' is 0.0 (nonnative)
    nonnative_dune_veg_df = transects_df[(transects_df["vegetation"] == True) & 
                                      (transects_df["dune"] == True) & 
                                      (transects_df["native"] == 0.0)]
    
    # Sum the 'cor_length' for each transect for only native vegetation in the dune portion
    nonnative_veg_cover_dune_sum = nonnative_dune_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'dune_length' from calculations_df
    pct_cover_nonnative_veg_dune = nonnative_veg_cover_dune_sum / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_nonnative_veg_dune"] = calculations_df["transect"].map(pct_cover_nonnative_veg_dune)
    
    #---------vegetated-----------
    
    #------- all cover along veg
    
    # Filter for rows where 'veg' is True
    veg_df = transects_df[transects_df["veg"] == True]
    
    # Sum the 'cor_length' for each transect
    veg_cover_sum = veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'veg_length' from calculations_df
    pct_cover_veg = veg_cover_sum / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_veg"] = calculations_df["transect"].map(pct_cover_veg)
    
    #----- veg cover veg
    
    # Filter for rows where both 'vegetation' and 'veg' are True
    veg_vegetation_df = transects_df[(transects_df["vegetation"] == True) & (transects_df["veg"] == True)]
    
    # Sum the 'cor_length' for each transect for only vegetation in the veg portion
    veg_cover_veg_sum = veg_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'veg_length' from calculations_df
    pct_cover_veg_veg = veg_cover_veg_sum / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_veg_veg"] = calculations_df["transect"].map(pct_cover_veg_veg)
    
    # ------ native cover veg
    # Filter for rows where 'vegetation' is True, 'veg' is True, and 'native' is 1.0
    native_veg_veg_df = transects_df[(transects_df["vegetation"] == True) & 
                                      (transects_df["veg"] == True) & 
                                      (transects_df["native"] == 1.0)]
    
    # Sum the 'cor_length' for each transect for only native vegetation in the veg portion
    native_veg_cover_veg_sum = native_veg_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'veg_length' from calculations_df
    pct_cover_native_veg_veg = native_veg_cover_veg_sum / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_native_veg_veg"] = calculations_df["transect"].map(pct_cover_native_veg_veg)
    
    # ------ nonnative cover veg
    # Filter for rows where 'vegetation' is True, 'veg' is True, and 'native' is 0.0 (nonnative)
    nonnative_veg_veg_df = transects_df[(transects_df["vegetation"] == True) & 
                                      (transects_df["veg"] == True) & 
                                      (transects_df["native"] == 0.0)]
    
    # Sum the 'cor_length' for each transect for only native vegetation in the veg portion
    nonnative_veg_cover_veg_sum = nonnative_veg_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover by dividing by 'veg_length' from calculations_df
    pct_cover_nonnative_veg_veg = nonnative_veg_cover_veg_sum / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to calculations_df
    calculations_df["pct_cover_nonnative_veg_veg"] = calculations_df["transect"].map(pct_cover_nonnative_veg_veg)
    
    #------------species specific-----------------
    
    
    #species over whole transect
    
    #abma whole 
    
    # Filter the transects_df for rows where the 'type' is 'ABMA'
    abma_vegetation_df = transects_df[transects_df['type'] == 'ABMA']
    
    # Sum the 'cor_length' for those rows
    abma_cover_sum = abma_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of ABMA over the entire transect
    pct_cover_abma_whole = abma_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_abma_whole"] = calculations_df["transect"].map(pct_cover_abma_whole)
    
    # amch whole 
    
    # Filter the transects_df for rows where the 'type' is 'ABMA'
    amch_vegetation_df = transects_df[transects_df['type'] == 'AMCH']
    
    # Sum the 'cor_length' for those rows
    amch_cover_sum = amch_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of AMCH over the entire transect
    pct_cover_amch_whole = amch_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_amch_whole"] = calculations_df["transect"].map(pct_cover_amch_whole)
    
    # cach whole
    
    # Filter the transects_df for rows where the 'type' is 'CACH'
    cach_vegetation_df = transects_df[transects_df['type'] == 'CACH']
    
    # Sum the 'cor_length' for those rows
    cach_cover_sum = cach_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of CACH over the entire transect
    pct_cover_cach_whole = cach_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_cach_whole"] = calculations_df["transect"].map(pct_cover_cach_whole)
    
    #atle whole
    
    # Filter the transects_df for rows where the 'type' is 'ATLE'
    atle_vegetation_df = transects_df[transects_df['type'] == 'ATLE']
    
    # Sum the 'cor_length' for those rows
    atle_cover_sum = atle_vegetation_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of ATLE over the entire transect
    pct_cover_atle_whole = atle_cover_sum / calculations_df.set_index("transect")["tran_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_atle_whole"] = calculations_df["transect"].map(pct_cover_atle_whole)
    
    # species over dune
    
    #abma dune 
    
    # Filter the transects_df for rows where the 'type' is 'ABMA' and the 'dune' column is True
    abma_vegetation_dune_df = transects_df[(transects_df['type'] == 'ABMA') & (transects_df['dune'] == True)]
    
    # Sum the 'cor_length' for those rows
    abma_cover_sum_dune = abma_vegetation_dune_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of ABMA over the dune portion of the transect
    pct_cover_abma_dune = abma_cover_sum_dune / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_abma_dune"] = calculations_df["transect"].map(pct_cover_abma_dune)
    
    #amch dune 
    
    # Filter the transects_df for rows where the 'type' is 'AMCH' and the 'dune' column is True
    amch_vegetation_dune_df = transects_df[(transects_df['type'] == 'AMCH') & (transects_df['dune'] == True)]
    
    # Sum the 'cor_length' for those rows
    amch_cover_sum_dune = amch_vegetation_dune_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of AMCH over the dune portion of the transect
    pct_cover_amch_dune = amch_cover_sum_dune / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_amch_dune"] = calculations_df["transect"].map(pct_cover_amch_dune)
    
    #cach dune 
    
    # Filter the transects_df for rows where the 'type' is 'CACH' and the 'dune' column is True
    cach_vegetation_dune_df = transects_df[(transects_df['type'] == 'CACH') & (transects_df['dune'] == True)]
    
    # Sum the 'cor_length' for those rows
    cach_cover_sum_dune = cach_vegetation_dune_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of CACH over the dune portion of the transect
    pct_cover_cach_dune = cach_cover_sum_dune / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_cach_dune"] = calculations_df["transect"].map(pct_cover_cach_dune)
    
    #atle dune 
    
    # Filter the transects_df for rows where the 'type' is 'ATLE' and the 'dune' column is True
    atle_vegetation_dune_df = transects_df[(transects_df['type'] == 'ATLE') & (transects_df['dune'] == True)]
    
    # Sum the 'cor_length' for those rows
    atle_cover_sum_dune = atle_vegetation_dune_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of ATLE over the dune portion of the transect
    pct_cover_atle_dune = atle_cover_sum_dune / calculations_df.set_index("transect")["dune_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_atle_dune"] = calculations_df["transect"].map(pct_cover_atle_dune)
    
    #species over veg poriton 
    
    #abma veg 
    
    # Filter the transects_df for rows where the 'type' is 'ABMA' and the 'veg' column is True
    abma_vegetation_veg_df = transects_df[(transects_df['type'] == 'ABMA') & (transects_df['veg'] == True)]
    
    # Sum the 'cor_length' for those rows
    abma_cover_sum_veg = abma_vegetation_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of ABMA over the veg portion of the transect
    pct_cover_abma_veg = abma_cover_sum_veg / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_abma_veg"] = calculations_df["transect"].map(pct_cover_abma_veg)
    
    #amch veg 
    
    # Filter the transects_df for rows where the 'type' is 'AMCH' and the 'veg' column is True
    amch_vegetation_veg_df = transects_df[(transects_df['type'] == 'AMCH') & (transects_df['veg'] == True)]
    
    # Sum the 'cor_length' for those rows
    amch_cover_sum_veg = amch_vegetation_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of AMCH over the veg portion of the transect
    pct_cover_amch_veg = amch_cover_sum_veg / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_amch_veg"] = calculations_df["transect"].map(pct_cover_amch_veg)
    
    #cach veg 
    
    # Filter the transects_df for rows where the 'type' is 'CACH' and the 'veg' column is True
    cach_vegetation_veg_df = transects_df[(transects_df['type'] == 'CACH') & (transects_df['veg'] == True)]
    
    # Sum the 'cor_length' for those rows
    cach_cover_sum_veg = cach_vegetation_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of CACH over the veg portion of the transect
    pct_cover_cach_veg = cach_cover_sum_veg / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_cach_veg"] = calculations_df["transect"].map(pct_cover_cach_veg)
    
    #atle veg 
    
    # Filter the transects_df for rows where the 'type' is 'ATLE' and the 'veg' column is True
    atle_vegetation_veg_df = transects_df[(transects_df['type'] == 'ATLE') & (transects_df['veg'] == True)]
    
    # Sum the 'cor_length' for those rows
    atle_cover_sum_veg = atle_vegetation_veg_df.groupby("transect")["cor_length"].sum()
    
    # Calculate the percent cover of ATLE over the veg portion of the transect
    pct_cover_atle_veg = atle_cover_sum_veg / calculations_df.set_index("transect")["veg_length"]
    
    # Add this calculation to the 'calculations_df'
    calculations_df["pct_cover_atle_veg"] = calculations_df["transect"].map(pct_cover_atle_veg)

    
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

