import streamlit as st

st.set_page_config(page_title="How Selection Works", page_icon="🛠️", layout="wide")

st.markdown("# How Provider Selection Works")

st.markdown(
    """
The Provider Recommender helps you find the best provider for your client by considering three important factors:
**how close they are**, **how busy they've been**, and **how well they work with us**.
The system automatically balances these factors to give you the most suitable recommendation.
"""
)

st.markdown("## 🎯 How It Works")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**🏠 1. Find Your Client's Location**
- Enter the client's address (street, city, state, zip)
- The system looks up the exact coordinates
- This helps calculate accurate distances to providers

**📏 2. Measure Distance**
- Calculates driving distance to each provider
- Shows results in miles for easy understanding
- Closer providers generally get higher priority

**⚖️ 3. Consider Workload Balance**
- Looks at how many referrals each provider has received
- Prefers providers who aren't overwhelmed with cases
- Helps ensure fair distribution of work
"""
    )

with col2:
    st.markdown(
        """
**🤝 4. Check Referral Relationships**
- Reviews which providers have sent us referrals
- Gives preference to providers who work with us regularly
- Strengthens mutual referral partnerships

**🏆 5. Calculate Final Score**
- Combines all factors using your chosen preferences
- Lower scores mean better matches
- Shows you the top recommendation first

**📋 6. Present Results**
- Displays the best provider with contact information
- Shows a ranked list of all qualified providers
- Provides export options for easy reference
"""
    )

st.markdown("## 🎛️ Customizing Your Search")

st.markdown("**You can adjust these settings to match your needs:**")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**📍 Distance Importance**
- High: Prioritizes providers closest to your client
- Medium: Balances distance with other factors
- Low: Distance is less important than relationships and workload

**📊 Outbound Referral Importance** 
- High: Strongly prefers providers with fewer recent cases
- Medium: Considers workload but doesn't dominate decision
- Low: Workload balance is less of a concern
"""
    )

with col2:
    st.markdown(
        """
**🤝 Inbound Referral Importance** *(when available)*
- High: Strongly favors providers who refer cases to us
- Medium: Considers referral relationships moderately
- Low: Mutual referrals are nice but not essential

**⚙️ Additional Filters**
- **Minimum referrals**: Ensures provider has experience
- **Time period**: Focus on recent referral activity
- **Maximum radius**: Set geographic boundaries
"""
    )

st.markdown("## 📋 Common Scenarios")

st.markdown("**Choose settings based on your situation:**")

scenario_col1, scenario_col2 = st.columns([1, 1])

with scenario_col1:
    st.markdown(
        """
**🚗 Client needs someone nearby**
- Distance: High importance (0.6-0.8)
- Outbound referrals: Medium importance (0.2-0.4)
- *Best for: Elderly clients, transportation issues*

**⚖️ Spread the workload fairly**
- Distance: Medium importance (0.2-0.4) 
- Outbound referrals: High importance (0.6-0.8)
- *Best for: Busy periods, managing capacity*

**🤝 Strengthen referral relationships**
- Distance: Lower importance (0.2)
- Outbound referrals: Medium importance (0.3)
- Inbound referrals: High importance (0.5)
- *Best for: Building long-term partnerships*
"""
    )

with scenario_col2:
    st.markdown(
        """
**🎯 Balanced approach (recommended)**
- Distance: Medium importance (0.4)
- Outbound referrals: Medium importance (0.4)
- Inbound referrals: Lower importance (0.2)
- *Best for: Most typical situations*

**📊 Data-driven decisions**
- Use the Data Dashboard to see current workload
- Check provider activity over time
- Adjust settings based on recent patterns

**� Quick tip**
Don't worry about exact numbers - the system automatically balances your choices to always total 100%!
"""
    )

st.markdown("## ✅ What Makes This Reliable")

qa_col1, qa_col2 = st.columns([1, 1])

with qa_col1:
    st.markdown(
        """
**🔍 Quality Checks**
- Validates all addresses before calculating distances
- Ensures providers have sufficient experience
- Checks data freshness and completeness

**📊 Current Data**  
- Uses the latest referral information
- Updates workload calculations in real-time
- Reflects recent provider activity patterns
"""
    )

with qa_col2:
    st.markdown(
        """
**🎯 Consistent Results**
- Same search criteria always produce same results
- Clear ranking system with transparent tie-breaking
- Saves your preferences during the session

**📈 Continuous Improvement**
- Data Dashboard shows system performance
- Regular data updates keep information current
- Feedback helps refine recommendations
"""
    )

with st.expander("🔧 Technical Details", expanded=False):
    st.markdown("### Scoring Formulas")
    
    st.markdown("**When inbound referral data is available:**")
    st.latex(r"Score = \alpha \times Distance_{norm} + \beta \times (1-Outbound_{norm}) + \gamma \times Inbound_{norm}")
    
    st.markdown("**When only outbound referral data is available:**")
    st.latex(r"Score = \alpha \times Distance_{norm} + \beta \times (1-Outbound_{norm})")
    
    st.markdown(
        """
        **Formula Explanation:**
        - **α, β, γ**: Normalized weights that always sum to 1.0
        - **Distance_norm**: Distance scaled to 0-1 range (closer = lower value)
        - **Outbound_norm**: Referral count scaled to 0-1 range (fewer referrals = lower value, preferred)
        - **Inbound_norm**: Inbound referral count scaled to 0-1 range (more referrals = higher value, preferred)
        - **Final Score**: Lower scores indicate better recommendations
        
        ### Implementation Details
        
        **Address Geocoding:**
        - Uses OpenStreetMap's Nominatim geocoding service
        - Implements 24-hour caching to improve performance
        - Graceful fallback for partial or invalid addresses
        
        **Distance Calculation:**
        - Haversine formula accounts for Earth's curvature
        - Vectorized calculations using NumPy for efficiency
        - Results provided in miles for practical interpretation
        
        **Data Processing:**
        - Min-max normalization ensures fair factor comparison
        - Deterministic tie-breaking using multiple sort criteria
        - Real-time filtering based on user-specified criteria
        
        **Performance Optimizations:**
        - Streamlit caching for data loading and geocoding operations
        - Efficient pandas operations for large dataset processing  
        - Session state management preserves user preferences
        
        **Data Pipeline:**
        1. Raw referral data imported from Lead Docket exports
        2. Data cleaning, deduplication, and provider aggregation
        3. Address geocoding and coordinate enrichment
        4. Runtime scoring and filtering based on search criteria
        5. Results ranking and presentation with export capabilities
        """
    )

st.markdown("---")

st.markdown("## 🚀 Getting Started")
st.markdown(
    """
**Ready to find the right provider for your client?**

1. **Go to Search**: Click the Search page to enter your client's address
2. **Set your preferences**: Adjust the importance sliders based on your priorities  
3. **Apply filters**: Set minimum experience and geographic limits as needed
4. **Get results**: View the recommended provider with full contact details
5. **Export if needed**: Download provider information for your records

**Questions or suggestions?** Contact the Data Operations team for support.
"""
)

st.info("💡 **Pro tip**: Try the Data Dashboard to explore current provider activity and referral patterns before searching!")
