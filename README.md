# CAFDuneWork

A place to work on collaborative code for the **California Climate Action Fund Project** with the **Coastal Dune Network**.

---

# Ecology Streamlit App

This **Streamlit** app processes ecological data for transects and vegetation to calculate coverage statistics. It is built using **Python**.

For Python installation, you can download it from the official website: [Python](https://www.python.org/downloads/)

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

   After activating your environment, install all the required dependencies by running:
   
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Once the environment is set up and dependencies are installed, you can run the app by executing the following command:

```bash
streamlit run https://gist.github.com/DakDune/0a749546c7e6bd287dcdffc256dde835
```

You can then **upload your `.xml` file**  to the app. The app will process the file, generate a graph, and produce an output file.
























