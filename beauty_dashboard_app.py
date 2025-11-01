# beauty_dashboard_final.py
"""
- Top tabs: Products | Live Analytics | Chatbot
- Sidebar filters + mood
- Save product -> Firestore (optional) OR local_product_clicks.json (fallback)
- Live Analytics reads saved interactions
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import plotly.graph_objects as go

# Try optional firebase-admin import
FIREBASE_AVAILABLE = False
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except Exception:
    FIREBASE_AVAILABLE = False

# ---------------- Page config ----------------
st.set_page_config(
    page_title="💄 Beauty Intelligence Dashboard",
    layout="wide",
    page_icon="💋"
)

# ---------------- Dark theme CSS & card styling ----------------
st.markdown(
    """
    <style>
    /* Page background */
    .css-18e3th9 {background-color: #0f1115;}
    .css-1d391kg {background-color: #0f1115;}
    /* Content text color */
    .stApp { color: #e9eef5; }
    /* Pink product card (light text adjusted for contrast) */
    .product-card {
        background: linear-gradient(180deg, #ffe9ef 0%, #ffe6eb 100%);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        color: #222222;
        box-shadow: 0 6px 18px rgba(0,0,0,0.45);
    }
    .product-title { font-size:20px; font-weight:700; color:#d63b67; margin-bottom:8px; }
    .product-desc { color:#2f2f2f; margin-bottom:8px; }
    .product-meta { color:#333333; font-weight:600; margin-bottom:6px; }
    .save-btn { background-color:#0b1220; color:white; border-radius:10px; padding:8px 12px; }
    .small-muted { color: #a8b0bd; font-size:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- Sample / real data setup ----------------
brands = ["The Ordinary", "Clinique", "Laneige", "Drunk Elephant", "Briogeo"]
# simulated average interest numbers
avg_interest = [57.8, 43.7, 26.1, 10.2, 4.8]
# simulated forecast placeholders (you used Prophet earlier)
forecast_values = [1369.9, 1475.1, 1399.9, 1386.5, 1417.1]

# Mock product database keyed by brand -> skin types
products = {
    "The Ordinary": {
        "Oily": {"name": "Niacinamide 10% + Zinc 1%", "price": 650, "desc": "Balances sebum and clears acne.", "img": ""},
        "Dry": {"name": "Hyaluronic Acid 2% + B5", "price": 750, "desc": "Hydrates dry, dull skin deeply.", "img": ""},
        "Combination": {"name": "Salicylic Acid 2% Masque", "price": 850, "desc": "Exfoliates and decongests pores.", "img": ""},
        "Sensitive": {"name": "Squalane Cleanser", "price": 900, "desc": "Gentle cleanser for sensitive skin.", "img": ""},
        "Normal": {"name": "Multi-Peptide Serum", "price": 1200, "desc": "General skin-strengthening serum.", "img": ""},
    },
    "Clinique": {
        "Sensitive": {"name": "Moisture Surge 100H Hydrator", "price": 3900, "desc": "Calms & hydrates sensitive skin.", "img": ""},
        "Normal": {"name": "Even Better Clinical", "price": 4200, "desc": "Brightening & evening serum.", "img": ""},
    },
    "Laneige": {
        "Dry": {"name": "Water Sleeping Mask EX", "price": 2400, "desc": "Overnight hydration for dry skin.", "img": ""},
        "Normal": {"name": "Lip Sleeping Mask", "price": 1200, "desc": "Hydrating lip treatment.", "img": ""},
    },
    "Drunk Elephant": {
        "Combination": {"name": "Protini Polypeptide Cream", "price": 5600, "desc": "Protein-rich moisturizer for balance.", "img": ""},
        "Normal": {"name": "C-Firma Day Serum", "price": 4200, "desc": "Vitamin C antioxidant serum.", "img": ""},
    },
    "Briogeo": {
        "Dry": {"name": "Don't Despair, Repair!", "price": 3600, "desc": "Nourishing mask for dry hair & scalp.", "img": ""},
        "Combination": {"name": "Scalp Revival", "price": 2200, "desc": "Scalp treatment for flakiness.", "img": ""},
    }
}

brand_data = {
    "The Ordinary": {"price": "Budget", "best_for": "Oily"},
    "Clinique": {"price": "Mid-range", "best_for": "Sensitive"},
    "Laneige": {"price": "Mid-range", "best_for": "Dry"},
    "Drunk Elephant": {"price": "Luxury", "best_for": "Combination"},
    "Briogeo": {"price": "Mid-range", "best_for": "Dry"},
}

# Helper function to extract price (moved to global scope)
def extract_price(p_val):
    """Safely extracts the integer price from a product dictionary value."""
    # Assuming p_val is an integer as per the 'products' mock data
    # If the mock data had strings (like "₹650"), we'd need string manipulation
    return int(p_val)

# ---------------- Sidebar (filters + nav fallback) ----------------
st.sidebar.header("Filters & Settings")
selected_brands = st.sidebar.multiselect("Select brands:", options=brands, default=brands)
skin_type = st.sidebar.selectbox("Skin type:", ["Oily", "Dry", "Combination", "Sensitive", "Normal"])
# Price range slider (numeric)
price_min, price_max = st.sidebar.slider(
    "💰 Price range (₹):",
    min_value=0,
    max_value=6000,
    value=(0, 6000),
    step=100
)

mood = st.sidebar.radio("Chatbot mood:", ["Sweet 💖", "Savage 😈", "Professional 💼"], index=2)

# Firebase init (optional) - searches for firebase-key.json in project folder
db = None
firebase_ready = False
if FIREBASE_AVAILABLE:
    possible_paths = [
        os.path.join(os.getcwd(), "firebase-key.json"),
        os.path.join(os.getcwd(), ".streamlit", "firebase-key.json"),
        os.path.join(os.path.expanduser("~"), "firebase-key.json"),
    ]
    key_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if key_path:
        try:
            cred = credentials.Certificate(key_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_ready = True
        except Exception as e:
            st.sidebar.error(f"Firestore init failed: {e}")
            firebase_ready = False
    else:
        st.sidebar.info("Optional: place your Firebase service account JSON as 'firebase-key.json' in the project folder to enable live saving.")
else:
    st.sidebar.info("Install 'firebase-admin' to enable Firestore live saving (optional).")

# ---------------- Top tabs for navigation ----------------
tab_products, tab_analytics, tab_chat = st.tabs(["💄 Products", "📊 Live Analytics", "💬 Chatbot"])

# --------------------- PRODUCTS TAB ---------------------
with tab_products:
    st.markdown("<h1 style='color:#f4f6f9; font-weight:800;'>Beauty Brand Insights</h1>", unsafe_allow_html=True)
    st.markdown("Explore data-driven product matches, quick insights, and save items for analysis.")

    # Row: Charts + Matches
    c1, c2 = st.columns([1.2, 1])

    with c1:
        st.subheader("Average Search Interest (simulated)")
        fig_interest = go.Figure()
        for i, b in enumerate(selected_brands):
            if b in brands:
                 # Check if the brand is in the main list to get its index
                fig_interest.add_trace(go.Bar(x=[b], y=[avg_interest[brands.index(b)]], name=b,
                                              marker=dict(color=["#ff7fa6","#ffb3c1","#ffd0e0","#ffc1b6","#fcd7e0"][i%5])))
        fig_interest.update_layout(template="plotly_dark", height=380, showlegend=False,
                                   margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig_interest, use_container_width=True)

    with c2:
        st.subheader("Best Matches for your filters")

        # Logic to find brands matching the selected skin type and price range
        matches = []
        for b in selected_brands:
            for sk, p in products.get(b, {}).items():
                # NOTE: p["price"] is an integer in the mock data, but we use the helper just in case the data changes
                price_val = extract_price(p["price"]) 
                if sk == skin_type and price_min <= price_val <= price_max:
                    matches.append(b)
                    break # Only need one match per brand

        if matches:
            st.success(f"💅 Best matches for **{skin_type}** skin in ₹{price_min}–₹{price_max} range: **{', '.join(sorted(list(set(matches))))}**") # Use set to ensure unique names
        else:
            st.info("No exact match — try adjusting filters. (The Ordinary is a versatile option.)")

    st.markdown("---")
    st.header("Personalized Product Recommendations")

    any_shown = False
    for brand in selected_brands:
        if brand in products and skin_type in products[brand]:
            any_shown = True
            p = products[brand][skin_type]
            
            # Check price filter again before display (though matches are shown above)
            price_val = extract_price(p['price'])
            if not (price_min <= price_val <= price_max):
                continue # Skip display if product is outside selected price range

            # Product card layout
            st.markdown(
                f"""<div class="product-card">
                        <div class="product-title">{p['name']}</div>
                        <div class="product-desc">{p['desc']}</div>
                        <div class="product-meta">💰 Price: ₹{p['price']} &nbsp;&nbsp; 🌸 Skin: {skin_type} &nbsp;&nbsp; 🏷️ Brand: {brand}</div>
                    </div>""",
                unsafe_allow_html=True
            )
            
            save_key = f"save_{brand}_{p['name'].replace(' ', '_')}" # Use product name for better key uniqueness
            if st.button(f"💗 Save {p['name']}", key=save_key):
                
                # Determine the current price range description for chatbot/analytics display
                if price_val < 1000:
                    price_range_desc = "Budget"
                elif price_val < 4000:
                    price_range_desc = "Mid-range"
                else:
                    price_range_desc = "Luxury"

                # save record to firestore or local json fallback
                rec = {
                    "brand": brand,
                    "product_name": p['name'],
                    "skin_type": skin_type,
                    "price_range": price_range_desc, # Use the derived description
                    "price_value": p['price'],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if firebase_ready and db:
                    try:
                        # Use firestore.SERVER_TIMESTAMP for accurate time in Firestore
                        db.collection("product_clicks").document().set({
                            "brand": rec["brand"],
                            "product_name": rec["product_name"],
                            "skin_type": rec["skin_type"],
                            "price_range": rec["price_range"],
                            "price_value": rec["price_value"],
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success(f"Saved to Firestore: {p['name']}")
                    except Exception as e:
                        st.error(f"Firestore save error: {e}")
                else:
                    # Fallback to local JSON file
                    local_file = "local_product_clicks.json"
                    try:
                        if os.path.exists(local_file):
                            with open(local_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                        else:
                            data = []
                    except Exception:
                        data = []
                        
                    data.append(rec)
                    with open(local_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    st.success(f"Saved locally: {p['name']}")

    if not any_shown:
        st.info("No product found for these filters. Try different skin type / brands / price range.")

    # Insights summary below products
    st.markdown("---")
    st.subheader("Insights Summary")
    sel_interest = [avg_interest[brands.index(b)] for b in selected_brands if b in brands] if selected_brands else []
    
    if sel_interest:
        # Find the max and min interest scores and their corresponding brands
        max_interest = max(sel_interest)
        min_interest = min(sel_interest)
        top_b_index = [brands.index(b) for b in selected_brands if b in brands and avg_interest[brands.index(b)] == max_interest][0]
        low_b_index = [brands.index(b) for b in selected_brands if b in brands and avg_interest[brands.index(b)] == min_interest][0]
        
        top_b = brands[top_b_index]
        low_b = brands[low_b_index]

        st.markdown(f"- 🌟 **{top_b}** leads in popularity (score **{max_interest}**).")
        st.markdown(f"- 💧 **{low_b}** shows the lowest interest (score **{min_interest}**).")
        st.markdown("- 📌 Consumers prefer performance & transparency over price for skincare products.")
    else:
        st.warning("Select brands to compute insights.")

# --------------------- LIVE ANALYTICS TAB ---------------------
with tab_analytics:
    st.header("Live Analytics — Saved Interactions")

    # Read saved interactions
    records = []
    if firebase_ready and db:
        try:
            # Note: The original code had a potential issue reading the server timestamp 
            # I'll keep the existing logic but recommend converting Firestore timestamps 
            # to a readable format *after* fetching documents in a real application.
            docs = db.collection("product_clicks").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1000).stream()
            for d in docs:
                r = d.to_dict()
                # Attempt to normalize Firestore timestamp object if present
                ts = r.get("timestamp")
                if ts and hasattr(ts, 'isoformat'): # Check if it's a datetime-like object
                     r["timestamp"] = ts.isoformat()
                elif ts and hasattr(ts, 'strftime'): # Handles datetime objects
                     r["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%S")
                # Otherwise, keep what's there (should be a string from local fallback or a Firestore ServerTimestamp)
                records.append(r)
        except Exception as e:
            st.error(f"Error reading Firestore: {e}")
            records = []
    else:
        local_file = "local_product_clicks.json"
        if os.path.exists(local_file):
            try:
                with open(local_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception as e:
                st.error(f"Failed to read local log: {e}")
                records = []
        else:
            records = []

    if not records:
        st.info("No saved interactions yet. Use the Products tab to save items (saved locally if Firestore not configured).")
    else:
        df_rec = pd.DataFrame(records)
        
        # Ensure timestamp column is datetime for sorting/display
        if "timestamp" in df_rec.columns:
            # Coerce errors to NaT if timestamp conversion fails (like for raw Firestore ServerTimestamp objects)
            df_rec["timestamp"] = pd.to_datetime(df_rec["timestamp"], errors='coerce')
        
        # Aggregations
        prod_counts = df_rec["product_name"].value_counts().reset_index()
        prod_counts.columns = ["product_name", "count"]

        brand_counts = df_rec["brand"].value_counts().reset_index()
        brand_counts.columns = ["brand", "count"]

        skin_counts = df_rec["skin_type"].value_counts().reset_index()
        skin_counts.columns = ["skin_type", "count"]

        # Layout analytics charts
        a1, a2 = st.columns(2)
        with a1:
            st.subheader("Most Saved Products")
            fig_p = go.Figure(go.Bar(x=prod_counts["count"].iloc[:10][::-1],
                                     y=prod_counts["product_name"].iloc[:10][::-1],
                                     orientation="h",
                                     marker=dict(color="#ffb3c1")))
            fig_p.update_layout(template="plotly_dark", height=350, margin=dict(l=120, r=10, t=30, b=30))
            st.plotly_chart(fig_p, use_container_width=True)
            st.write(prod_counts.head(10))

        with a2:
            st.subheader("Most Popular Brands")
            fig_b = go.Figure(go.Bar(x=brand_counts["brand"], y=brand_counts["count"], marker=dict(color="#ff7fa6")))
            fig_b.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=30, b=30))
            st.plotly_chart(fig_b, use_container_width=True)
            st.write(brand_counts.head(10))

        st.subheader("Top Skin Type Preferences")
        fig_s = go.Figure(go.Bar(x=skin_counts["skin_type"], y=skin_counts["count"], marker=dict(color="#ffc6d6")))
        fig_s.update_layout(template="plotly_dark", height=300, margin=dict(t=10))
        st.plotly_chart(fig_s, use_container_width=True)
        st.write(skin_counts)

        # Download CSV export
        csv = df_rec.to_csv(index=False).encode("utf-8")
        st.download_button(label="📥 Download saved interactions (CSV)", data=csv, file_name="saved_interactions.csv", mime="text/csv")

        st.markdown("---")
        st.subheader("Recent Saved Interactions")
        # Ensure 'timestamp' is present before sorting
        if "timestamp" in df_rec.columns:
            st.dataframe(df_rec.sort_values(by="timestamp", ascending=False).head(100), use_container_width=True)
        else:
            st.dataframe(df_rec.head(100), use_container_width=True) # Fallback to unsorted

# --------------------- CHATBOT TAB ---------------------
with tab_chat:
    st.header("Beauty Insights Assistant")
    st.markdown("Ask quick questions about trends, recommendations, or product picks. (Offline rule-based bot)")

    q = st.text_input("Ask a question (e.g., 'best for oily skin', 'forecast', 'popular brand')")

    def chatbot_answer(query, mood, skin):
        
        # Determine current price range from slider for the chatbot's generic recommendation logic
        current_price_range = ""
        if price_max < 1500:
            current_price_range = "Budget"
        elif price_max < 4500:
            current_price_range = "Mid-range"
        else:
            current_price_range = "Luxury"

        if not query:
            return "Ask me something about product recommendations, trends, or pricing."
            
        qq = query.lower()
        if "trend" in qq or "popular" in qq:
            resp = f"The Ordinary and Clinique show consistently high interest in our dataset. The Ordinary is strong among budget buyers."
        elif "forecast" in qq:
            resp = "Forecast models predict steady interest into early 2026 for ingredient-driven brands (simulated)."
        elif "recommend" in qq or "best" in qq:
            # Recommend based on the sidebar's current skin type and a price range derived from the slider
            candidates = [b for b in brands if brand_data[b]["best_for"] == skin and brand_data[b]["price"] == current_price_range]
            
            # If no direct match by best_for and price, try just best_for
            if not candidates:
                 candidates = [b for b in brands if brand_data[b]["best_for"] == skin]

            resp = f"Recommended for **{skin}** skin in the **{current_price_range}** price bracket: **{', '.join(candidates)}**." if candidates else "No exact match with current filters; consider The Ordinary for versatility."
            
        elif "price" in qq:
            resp = "Budget: The Ordinary | Mid-range: Clinique, Laneige, Briogeo | Luxury: Drunk Elephant"
        else:
            resp = "Try: 'best for dry skin', 'popular brands', or 'forecast'."

        if mood == "Sweet 💖":
            return "💖 " + resp + " You're glowing already!"
        if mood == "Savage 😈":
            return "😈 " + resp + " Do better or buy better."
        return "💼 " + resp

    if q:
        # Pass skin_type (skin) to the chatbot logic
        st.info(chatbot_answer(q, mood, skin_type)) 
    else:
        st.caption("Type a question and press Enter to get an answer.")

# ---------------- End of file ----------------