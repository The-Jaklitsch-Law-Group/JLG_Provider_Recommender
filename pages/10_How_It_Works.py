import streamlit as st

st.set_page_config(page_title="How Selection Works", page_icon="🧠", layout="wide")

st.markdown("# How Provider Selection Works")

st.markdown(
    """
Our provider recommendation system uses a sophisticated algorithm that balances multiple key factors:
**geographic proximity**, **outbound referral load balancing**, and **inbound referral patterns**
to ensure optimal client care and fair distribution across our provider network.
"""
)

st.markdown("## 🔄 Algorithm Steps")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**1. Address Geocoding**
- Converts client address to latitude/longitude coordinates
- Uses OpenStreetMap's Nominatim service
- Implements fallback strategies for partial addresses

**2. Distance Calculation**
- Uses Haversine formula for accurate geographic distances
- Accounts for Earth's curvature
- Results in miles for easy interpretation

**3. Data Normalization**
- Distance: Min-max normalization to [0,1] scale
- Outbound Referral Count: Min-max normalization to [0,1] scale
- Inbound Referral Count: Min-max normalization to [0,1] scale (when available)
- Ensures fair comparison between different metrics
"""
    )

with col2:
    st.markdown(
        """
**4. Weighted Scoring**
- Combines normalized distance, outbound referrals, and inbound referrals
- Three-factor formula: `Score = α × Distance + β × Outbound_Referrals + γ × Inbound_Referrals`
- Two-factor fallback: `Score = α × Distance + β × Referral_Count`
- Lower scores indicate better recommendations

**5. Ranking & Selection**
- Sorts providers by composite score (ascending)
- Applies deterministic tie-breaking rules
- Returns top recommendation with rationale

**6. Load Balancing**
- Prefers providers with fewer recent referrals
- Helps distribute workload evenly across network
- Maintains quality while optimizing capacity
"""
    )

st.markdown("## 📊 Scoring Formulas")

st.markdown("**Three-Factor Scoring (when inbound data is available):**")
st.latex(r"Score = \\alpha \\times Distance_{norm} + \\beta \\times (1-Outbound_{norm}) + \\gamma \\times Inbound_{norm}")

st.markdown("**Two-Factor Scoring (fallback):**")
st.latex(r"Score = \\alpha \\times Distance_{norm} + \\beta \\times (1-Outbound_{norm})")

st.markdown(
    """
Where:
- **α (alpha)**: Distance weight (normalized to 0.0-1.0, with all weights summing to 1.0)
- **β (beta)**: Outbound referral count weight (normalized to 0.0-1.0)
- **γ (gamma)**: Inbound referral count weight (normalized to 0.0-1.0, three-factor only)
- **α + β + γ = 1.0** for three-factor scoring
- **α + β = 1.0** for two-factor scoring
- Weights represent relative importance/priority of each factor
- Lower outbound referrals are preferred (load balancing)
- Higher inbound referrals are preferred (mutual referral relationships)
"""
)

st.markdown("## ⚖️ Weight Selection Guide")

st.markdown("**Three-Factor Scoring Options:**")
st.markdown(
    """
Set the relative importance of each factor (weights will be automatically normalized to sum to 1.0):

- **Distance-Priority**: Distance(0.6) + Outbound(0.3) + Inbound(0.1) → (60%, 30%, 10%)
- **Balanced**: Distance(0.4) + Outbound(0.4) + Inbound(0.2) → (40%, 40%, 20%)
- **Relationship-Focus**: Distance(0.2) + Outbound(0.3) + Inbound(0.5) → (20%, 30%, 50%)
- **Load-Balancing**: Distance(0.2) + Outbound(0.6) + Inbound(0.2) → (20%, 60%, 20%)
- **Equal Weight**: Distance(0.33) + Outbound(0.33) + Inbound(0.33) → (33%, 33%, 33%)

💡 **Tip**: Higher raw values = more importance. The system automatically normalizes to percentages.
"""
)

st.markdown("**Two-Factor Scoring Options:**")
st.markdown(
    """
For two-factor scoring, set the relative importance (automatically normalized):

- **Distance Priority**: Distance(0.8) + Outbound(0.2) → (80%, 20%)
- **Balanced**: Distance(0.5) + Outbound(0.5) → (50%, 50%)
- **Load Balancing Priority**: Distance(0.2) + Outbound(0.8) → (20%, 80%)
- **Distance Only**: Distance(1.0) + Outbound(0.0) → (100%, 0%)
- **Load Balancing Only**: Distance(0.0) + Outbound(1.0) → (0%, 100%)

💡 **Tip**: The final weights always sum to 100% for consistent, interpretable scoring.
"""
)

st.markdown("## ✅ Quality Assurance Features")

qa_col1, qa_col2 = st.columns([1, 1])

with qa_col1:
    st.markdown(
        """
**Data Validation**
- Minimum referral thresholds ensure provider experience
- Geographic coordinate validation
- Address standardization and cleaning
"""
    )

with qa_col2:
    st.markdown(
        """
**Consistent Results**
- Deterministic tie-breaking for reproducible outcomes
- Cached geocoding for performance and consistency
- Session state preservation during user interaction
"""
    )

with st.expander("🔧 Technical Implementation Details", expanded=False):
    st.markdown(
        """
**Geocoding Service**: OpenStreetMap Nominatim API
- Free, reliable geocoding service
- Rate-limited to respect service terms
- 24-hour caching for performance optimization

**Distance Calculation**: Haversine Formula
```python
# Simplified version of our distance calculation
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth's radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * arcsin(sqrt(a))
    return R * c
```

**Performance Optimizations**:
- Vectorized distance calculations using NumPy
- Streamlit caching for data loading and geocoding
- Efficient pandas operations for data processing

**Data Pipeline**:
1. Raw referral data from Lead Docket exports
2. Data cleaning and provider aggregation
3. Geocoding and coordinate enrichment
4. Runtime filtering and scoring
"""
    )

st.markdown("---")
st.markdown("*For technical questions or suggestions, contact the Data Operations team.*")
