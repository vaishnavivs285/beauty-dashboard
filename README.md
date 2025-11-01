# Beauty Brand Insights Dashboard

A professional Streamlit + Plotly dashboard that visualizes beauty brand trends, consumer behavior, and product performance across price segments and skin types.  

---

## 1. Overview

The **Beauty Brand Insights Dashboard** provides an interactive interface for analyzing market data and user preferences within the global beauty industry.  
It helps identify top-performing brands, forecast market trends, and uncover insights across customer demographics such as **skin type** and **price sensitivity**.

---

## 2. Key Features

### a. Trend Analytics
- Visualizes average search interest (Google Trends-style data)
- Displays time-series trends for brand popularity
- Includes forecast modeling for future growth predictions

### b. Consumer Insights
- Analyzes popularity by **skin type** (Dry, Oily, Combination)
- Segments product data by **price range** (Budget, Mid-range, Luxury)
- Generates AI-based narrative insights (contextual analysis)

### c. Market Intelligence Dashboard
- Dedicated **Live Analytics** page showing:
  - Most saved products
  - Most popular brands
  - Top skin type preferences
- Filterable, interactive graphs for business reporting

### d. Utility Features
- Downloadable CSV reports for data export
- Responsive UI with dark theme design
- Streamlined sidebar filters for easy exploration

---

## 3. Tech Stack

| Component | Technology |
|------------|-------------|
| **Frontend Framework** | Streamlit |
| **Visualization Library** | Plotly |
| **Data Processing** | Pandas, NumPy |
| **AI / Analytics Layer** | OpenAI API (optional) |
| **Forecasting Model** | Prophet-style time series simulation |

---

## 4. Project Structure
beauty_project/
│
├── beauty_dashboard_app.py # Main Streamlit app
├── data/ # Optional data folder (CSV files)
├── .streamlit/
│ └── secrets.toml # API key (if using AI insights)
└── README.md # Project documentation

---

## 5. Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/beauty-brand-dashboard.git
   cd beauty-brand-dashboard

2. Install Dependencies
  pip install -r requirements.txt

 3. Run the application
    streamlit run beauty_dashboard_app.py

  4.  Access the Dashboard
       The app will open automatically in your browser at:
       http://localhost:8501
  
  
  ##Optional: AI Insights Configuration
              To enable AI-generated insights, create a file at:
               .streamlit/secrets.toml
     Add your API key:
     OPENAI_API_KEY = "your_openai_api_key_here"
      If you don’t have an API key, you can disable that section in the code (the dashboard will still work normally).

  ###7. Future Enhancements
        Integration with real Google Trends data
        Brand sentiment analysis via social media data
        Product review mining and clustering
        Recommendation engine for personalized beauty suggestions
