import streamlit as st

st.set_page_config(page_title="How Selection Works", page_icon="🛠️", layout="wide")

st.markdown("# How Provider Selection Works")

st.markdown(
    """
The Provider Recommender uses a sophisticated scoring algorithm to find the best medical service provider for your client.
It analyzes **geographic proximity**, **referral distribution**, **referral relationships**, and **preferred provider status**
to deliver data-driven recommendations that balance client convenience with provider capacity.

The system processes historical referral data from Filevine, geocodes provider locations, and applies configurable
weighting to rank providers based on your priorities.
"""
)

st.markdown("## 🔄 Complete Workflow")

st.markdown("**From Raw Data to Recommendation in 6 Steps:**")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**📥 1. Data Collection**
- Export referral data from Filevine to CSV
- Includes provider contacts, referral counts, and dates
- Raw file stored in S3 bucket

**🧹 2. Data Cleaning & Processing**
- Split into inbound/outbound referral datasets
- Normalize addresses and phone numbers
- Deduplicate providers by (name, address)
- Parse and validate coordinate data

**🗺️ 3. Geocoding & Enrichment**
- Geocode missing coordinates via Nominatim (OpenStreetMap)
- Fallback to Google Maps API if available
- Validate coordinate ranges (-90 to 90 lat, -180 to 180 lon)
- Cache geocoding results for 24 hours
"""
    )

with col2:
    st.markdown(
        """
**💾 4. Data Optimization**
- Save cleaned data as CSV files (cached for 24 hours)
- Create aggregated provider dataset with referral counts
- Store in `data/processed/` for application use

**🔎 5. Search & Scoring**
- User enters client address and preferences
- System geocodes client location
- Calculates distances using haversine formula
- Applies configurable scoring algorithm
- Filters by radius and minimum referrals

**🏆 6. Recommendation Delivery**
- Rank providers by score (higher = better)
- Display top recommendation with full contact details
- Show complete ranked list with export options
- Visualize results on interactive map
"""
    )

st.markdown("## 🎯 How Scoring Works")

st.markdown("**The scoring algorithm combines four normalized factors:**")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**📏 1. Distance (Geographic Proximity)**
- Calculates straight-line distance using haversine formula
- Accounts for Earth's curvature for accuracy
- Normalized to 0-1 range (closer = higher score)
- Results displayed in miles for practical interpretation

**📊 2. Outbound Referrals (Workload Balance)**
- Counts referrals FROM firm TO provider
- Higher counts indicate more experienced providers
- **Direct normalization**: More referrals = HIGHER score (preferred)
- Helps identify experienced providers with proven track records
"""
    )

with col2:
    st.markdown(
        """
**🤝 3. Inbound Referrals (Relationship Strength)**
- Counts referrals FROM provider TO firm
- Higher counts indicate stronger partnerships
- Higher referrals = HIGHER score (preferred)
- Strengthens reciprocal referral relationships

**⭐ 4. Preferred Provider Status**
- Binary flag for firm's preferred providers
- Preferred status increases score (improves ranking)
- Optional weighting via slider control
- Helps prioritize strategic partnerships
"""
    )

st.markdown(
    """
### Combined Score Formula

```
Final Score = α × Distance_norm + β × Outbound_norm + γ × Inbound_norm + δ × Preferred_norm
```

**Where:**
- **α, β, γ, δ** = Your configured weights (automatically normalized to sum to 1.0)
- **Distance_norm** = Inverted distance (0 = farthest, 1 = closest)
- **Outbound_norm** = Direct referral count (more referrals = higher value = better score)
- **Inbound_norm** = Min-max normalized inbound referrals (more = higher score)
- **Preferred_norm** = Binary preferred provider flag (adds to score)
- **Higher final scores = better matches**

The system automatically normalizes your slider values so you don't have to worry about making them sum to 100%!
"""
)

st.markdown("## 🎛️ Customizing Your Search")

st.markdown("**Adjust these settings to match your referral scenario:**")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**📍 Distance Weight**
- **High (0.6-0.8)**: Prioritize providers closest to client
- **Medium (0.3-0.5)**: Balance distance with other factors
- **Low (0.1-0.2)**: Geography less important than relationships

**📊 Outbound Referral Weight**
- **High (0.6-0.8)**: Strongly prefer providers with more experience
- **Medium (0.3-0.5)**: Consider experience but don't dominate decision
- **Low (0.1-0.2)**: Experience level less of a priority
"""
    )

with col2:
    st.markdown(
        """
**🤝 Inbound Referral Weight**
- **High (0.4-0.6)**: Strongly favor providers who refer to us
- **Medium (0.2-0.4)**: Consider referral relationships moderately
- **Low (0.0-0.1)**: Mutual referrals nice but not essential

**⭐ Preferred Provider Weight**
- **High (0.3-0.5)**: Strong preference for designated providers
- **Medium (0.1-0.3)**: Moderate preference for preferred list
- **Low/Off (0.0)**: Treat all providers equally
"""
    )

st.markdown(
    """
**⚙️ Additional Filters:**
- **Minimum Referrals**: Ensures provider has experience (default: 1)
- **Maximum Radius**: Sets geographic boundary in miles (default: 50)
- **Time Period**: Focus on recent vs. all-time referral activity
"""
)

st.markdown("## 📋 Common Referral Scenarios")

st.markdown("**Pre-configured weight suggestions for different situations:**")

scenario_col1, scenario_col2 = st.columns([1, 1])

with scenario_col1:
    st.markdown(
        """
**🚗 Client Needs Someone Nearby**
- Distance: 0.7 (High importance)
- Outbound: 0.2 (Low importance)
- Inbound: 0.1 (Low importance)
- *Best for: Elderly clients, transportation limitations, local convenience*

**⚖️ Distribute Workload Fairly**
- Distance: 0.2 (Low importance)
- Outbound: 0.1 (Very low - don't prioritize experience here)
- Inbound: 0.7 (High importance - focus on relationships)
- *Best for: Busy periods, balancing referral relationships*

**🤝 Strengthen Referral Partnerships**
- Distance: 0.2 (Low importance)
- Outbound: 0.2 (Low importance)
- Inbound: 0.6 (High importance)
- *Best for: Building reciprocal relationships, strategic partnerships*
"""
    )

with scenario_col2:
    st.markdown(
        """
**🎯 Balanced Approach (Default)**
- Distance: 0.4 (Medium importance)
- Outbound: 0.4 (Medium importance)
- Inbound: 0.2 (Low importance)
- *Best for: Most typical referral situations, general use*

**⭐ Preferred Providers First**
- Distance: 0.3 (Medium importance)
- Outbound: 0.2 (Low importance)
- Preferred: 0.5 (High importance)
- *Best for: Utilizing preferred provider network, strategic partnerships*

**📊 Data-Driven Optimization**
- Use the **Data Dashboard** to analyze current workload
- Check provider activity trends over time
- Identify underutilized providers
- Adjust weights based on recent referral patterns
"""
    )

st.markdown(
    """
💡 **Pro Tip**: Don't worry about making weights sum to 100% - the system automatically normalizes them!
Focus on relative importance (e.g., "distance twice as important as workload").
"""
)

st.markdown("## ✅ Data Quality & Reliability")

qa_col1, qa_col2 = st.columns([1, 1])

with qa_col1:
    st.markdown(
        """
**🔍 Comprehensive Validation**
- Address validation before geocoding
- Coordinate range checking (-90 to 90, -180 to 180)
- Phone number format normalization
- Minimum referral threshold enforcement
- Duplicate provider detection and removal

**📊 Current & Accurate Data**
- Sourced from Filevine exports
- Regular data refresh cycles
- Real-time workload calculations
- Historical referral tracking
- Missing geocode identification and resolution
"""
    )

with qa_col2:
    st.markdown(
        """
**🎯 Consistent & Transparent Results**
- Deterministic scoring (same input = same output)
- Clear tie-breaking rules (distance → referrals → name)
- Session state preservation of preferences
- Exportable results for record-keeping
- Complete provider rankings available

**🧪 Extensively Tested**
- 70+ automated tests covering all core functionality
- Haversine distance validation against known city pairs
- Scoring algorithm verification with edge cases
- Data cleaning and deduplication tests
- Geocoding fallback testing
"""
    )

with st.expander("🔧 Technical Details", expanded=False):
    st.markdown("### Scoring Formula Breakdown")

    st.markdown("**Full scoring equation when all data is available:**")
    st.latex(
        r"\text{Score} = \alpha \times D_{norm} + \beta \times O_{norm} + \gamma \times I_{norm} + \delta \times P_{norm}"
    )

    st.markdown("**When only outbound referral data exists:**")
    st.latex(r"\text{Score} = \alpha \times D_{norm} + \beta \times O_{norm}")

    st.markdown(
        """
        **Variable Definitions:**
        - **α, β, γ, δ**: User-configured weights, automatically normalized so α + β + γ + δ = 1.0
        - **D_norm**: Distance normalized to [0, 1] range via inverted min-max scaling (closer = higher value)
        - **O_norm**: Outbound referral count normalized to [0, 1] (direct: more referrals = higher score)
        - **I_norm**: Inbound referral count normalized to [0, 1] (more referrals = higher score)
        - **P_norm**: Preferred provider binary flag (1 for preferred, 0 otherwise)
        - **Final Score**: Higher values indicate better matches (descending sort)

        ### Implementation Algorithms

        **Distance Calculation (Haversine Formula):**
        ```python
        # Accounts for Earth's spherical shape
        a = sin²(Δlat/2) + cos(lat₁) × cos(lat₂) × sin²(Δlon/2)
        c = 2 × arcsin(√a)
        distance_miles = 3958.8 × c  # Earth radius in miles
        ```

        **Min-Max Normalization:**
        ```python
        # Scales values to [0, 1] range for fair comparison
        normalized = (value - min) / (max - min)
        ```

        **Geocoding Strategy:**
        - **Primary**: OpenStreetMap Nominatim (free, rate-limited to 1 req/sec)
        - **Fallback**: Google Maps Geocoding API (requires API key)
        - **Caching**: 24-hour TTL to minimize API calls
        - **User-Agent**: Required for Nominatim compliance

        **Data Processing Pipeline:**
        ```
        1. Raw Excel Export (Filevine)
           ↓
        2. Data Cleaning (normalize addresses, phone numbers)
           ↓
        3. Deduplication (by normalized_name + normalized_address)
           ↓
        4. Geocoding (fill missing lat/lon coordinates)
           ↓
        5. Parquet Optimization (10x faster loading)
           ↓
        6. Application Loading (via DataIngestionManager)
           ↓
        7. Runtime Scoring & Filtering
           ↓
        8. Results Ranking & Display
        ```
"""
    )

    st.markdown("### Performance Optimizations")
    st.markdown(
        """
        - **Vectorized Operations**: NumPy arrays for distance calculations (100x faster than loops)
        - **Streamlit Caching**: `@st.cache_data` for data loading (1-hour TTL)
        - **Parquet Format**: Columnar storage ~10x faster than Excel
        - **Geocoding Cache**: 24-hour persistence to avoid redundant API calls
        - **Session State**: Preserves user preferences and search results
        - **Lazy Loading**: Data loaded only when needed, not on app startup

        **Typical Performance:**
        - Data loading: <500ms (Parquet) vs 5-10s (Excel)
        - Distance calculation: <50ms for 100 providers
        - Geocoding (cached): <10ms
        - Geocoding (fresh): 1-3s (Nominatim), <500ms (Google)
        - Full search cycle: <1s for typical datasets
        """
    )

    st.markdown("### Data Integrity")
    st.markdown(
        """
        **Deduplication Strategy:**
        - **Key**: `(normalized_name, normalized_address)`
        - **Name normalization**: Lowercase, remove punctuation, strip whitespace
        - **Address normalization**: Standardize abbreviations, remove suite/unit numbers

        **Validation Rules:**
        - Latitude: -90 to 90 degrees
        - Longitude: -180 to 180 degrees
        - Zipcode: 5 digits or 5+4 format (XXXXX or XXXXX-XXXX)
        - Phone: 10 or 11 digits (formatted to (XXX) XXX-XXXX)
        - State: Full name or 2-letter abbreviation (mapped to abbreviation)

        **Missing Data Handling:**
        - Missing coordinates: Provider excluded from distance-based scoring
        - Missing referral counts: Treated as 0 (eligible but ranked lower)
        - Missing addresses: Provider excluded from results
        - Partial addresses: Geocoding attempted with available components
        """
    )

st.markdown("---")

st.markdown("## 🚀 Quick Start Guide")

start_col1, start_col2 = st.columns([1, 1])

with start_col1:
    st.markdown(
        """
**Ready to find the right provider?**

1. **📍 Go to Search Page**
   - Enter your client's full address
   - System will geocode the location

2. **⚖️ Configure Preferences**
   - Adjust importance sliders based on scenario
   - Set minimum referral threshold (experience level)
   - Set maximum search radius (miles)

3. **🔎 Execute Search**
   - Click "Find Providers" button
   - System filters and scores all providers
   - Results load in <1 second
"""
    )

with start_col2:
    st.markdown(
        """
**Explore your results:**

4. **🏆 Review Top Recommendation**
   - See best-match provider with full contact details
   - Review distance, referral counts, score

5. **📊 Analyze Full Rankings**
   - Browse complete provider list sorted by score
   - Export results to CSV/Excel
   - View providers on interactive map

6. **🔄 Refine if Needed**
   - Adjust weights and re-search
   - Try different scenarios
   - Compare results side-by-side
"""
    )

st.markdown("### 📚 Additional Resources")

st.markdown(
    """
- **📊 Data Dashboard**: Explore provider workload trends, referral patterns, and data quality metrics
- **🔄 Update Data**: Refresh provider database with latest Filevine exports
- **🏠 Home**: Project overview and navigation guide
- **💾 Export Options**: Download search results for record-keeping and sharing

**Questions or need help?** Contact the Data Operations team for support and training.
"""
)

st.success(
    "💡 **Pro Tip**: Start with the **Data Dashboard** to understand current provider capacity and referral patterns before searching!"
)
