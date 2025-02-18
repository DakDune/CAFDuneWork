# CAFDuneWork

A place to work on collaborative code for the **California Climate Action Fund Project** with the **Coastal Dune Network**. Code written by Maya Bernstein, App made by Dakota Fee

---
# USAGE

The code is being hosted on a cloud, meaning simply use this link and it should work. No need to code or download anything. Optionally, if you want to get it running locally following the instructions below (**NOT** Necessary). 

**LINK**: https://cafdunework-monitoringplantcov.streamlit.app/#ecological-transect-data-processor

---

# Ecology Streamlit App

This **Streamlit** app processes ecological data for transects and vegetation to calculate coverage statistics. It is built using **Python** and a package called **Streamlit**. The code and app running is hosted via Github Gist, so it does **not** work to download the whole respository as is. 



For Python installation, you can download it from the official website: [Python](https://www.python.org/downloads/)

In order to manage and work in an environment you also need conda: (https://docs.anaconda.com/miniconda/install/#quick-command-line-install). Go to quick start and find the type you need for your computer. Then copy and paste into your terminal. 

---

## Installation

To run this app, you'll need to install the following dependencies into a Python environment.

1. **Create a Python Environment**:
   
   To create a new environment, run the following in your terminal:
   
   ```bash
   conda create --name env
   ```

2. **Activate the Environment**:

   Once the environment is created, activate it with:
   
   ```bash
   conda activate env
   ```

3. **Install Dependencies**:

   After activating your environment, install all the required dependencies by running (need this file downloaded and in working directory):
   
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Once the environment is set up and dependencies are installed, you can run the app by executing the following command:

```bash
streamlit run https://gist.githubusercontent.com/DakDune/0a749546c7e6bd287dcdffc256dde835/raw/9a65be10c1bd65955f38e345439892f390052710/ecology_app.py
```

You can then **upload your `.xml` file**  to the app. The app will process the file, generate a graph, and produce an output file.
























