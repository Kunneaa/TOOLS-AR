# C-Level AR Dashboard

A fully interactive Accounts Receivable (AR) Dashboard built entirely in Python using **Streamlit**, **Pandas**, and **Plotly**. This application consolidates complex financial data into a clean, modern, and high-performance UI tailored for C-Level executives and AR Managers.

## Key Features

1. **Automated Data Pipeline (ETL)**:
   - Automatically ingests all monthly and daily Excel files from the `data/` directory.
   - Intelligently extracts the reporting date from the filename (e.g., `AR_DATA_MONTH_7_DAY_15.xlsx`).
   - Cleans and casts numerical data, fixing common Excel date-parsing glitches in headers (e.g., converting accidental `13-Jul` datetime objects back to `7 - 13` day buckets).

2. **Advanced Filtering & Cascading Logic**:
   - Selecting a specific "AR Person" dynamically updates the available options for "Sales Person", which in turn updates the available "Customer" list.
   - **Cross-Filtering Exception**: The 10 Trend Analysis charts explicitly ignore the "Report Month" slicer, ensuring you always see the full 7-month historical context for your selected filters (similar to "Edit Interactions" in Power BI).

## Project Structure

```text
AR_DASHBOARD/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── start_app.sh            # One-click execution script (Mac/Linux)
├── README.md               # Documentation
└── data/                   # Directory for Excel data files
    ├── assign_ar_team.xlsx # AR/Sales mapping file (SCD format)
    └── AR_DATA_MONTH_*.xlsx# Raw AR Data files
```

## How to Run Locally

### Prerequisites
- Python 3.9+
- pip (Python package installer)

### Running the App
1. Open a terminal and navigate to the project directory:
   ```bash
   cd /path/to/AR_DASHBOARD
   ```
2. Run the start script:
   ```bash
   ./start_app.sh
   ```
   *(This script will automatically install missing requirements and start the Streamlit server).*

3. The application will automatically open in your default browser at `http://localhost:8501`.

## How to Deploy to Streamlit Community Cloud (Free)

To share this interactive dashboard with your team via a public URL:
1. Push this entire repository (including the `data/` folder) to your personal **GitHub** account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
3. Click **New app**.
4. Select your repository, the `main` branch, and set the Main file path to `app.py`.
5. Click **Deploy!**
6. Once deployed, you can share the generated URL with your colleagues (e.g., `https://your-ar-dashboard.streamlit.app`).
