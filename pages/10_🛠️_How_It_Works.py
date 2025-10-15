import streamlit as st

st.set_page_config(page_title="How Selection Works", page_icon="🛠️", layout="wide")

st.markdown("# How Provider Selection Works")

st.markdown(
    """
The Provider Recommender finds the best medical service provider for your client by combining location, referral history, and your preferences.

At a glance:
- Input: client address and simple preference sliders
- Data source: secure AWS S3 bucket (single source of truth)
- Output: ranked provider recommendations with contact details and distance
- Primary benefit: faster, consistent, data-driven referrals that balance client convenience and provider experience

No technical setup is required to run a search — enter an address, adjust sliders, and the system returns ranked matches.
"""
)

st.markdown("## ✅ Summary (Non-technical)")
st.markdown(
    """
- Quickly find nearby providers tailored to client needs
- Prioritizes distance, referral experience, reciprocity, and preferred providers
- Uses secure S3-hosted data that updates automatically when new files are added
"""
)

st.markdown("## 🔄 Complete Workflow")

st.markdown("**From S3 Data Source to Recommendation in 6 Steps:**")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(
        """
**☁️ 1. S3 Data Sourcing (Automatic)**
- App connects to AWS S3 bucket on launch
- Downloads the latest referral and preferred provider data from configured S3 folders
- Automatically selects the most recent file by timestamp
- S3 is the **only** data source—no local Parquet or Excel files are used for ingestion
- Data updates automatically when new files are uploaded to S3

**🧹 2. Data Cleaning & Processing**
- Split into inbound/outbound referral datasets
- Normalize addresses and phone numbers
- Deduplicate providers by (name, address)
- Parse and validate coordinate data
- Create aggregated provider dataset with referral counts

**🗺️ 3. Geocoding & Enrichment**
- Geocode missing coordinates via Nominatim (OpenStreetMap)
- Rate-limited to 1 request/second for API compliance
- Validate coordinate ranges (-90 to 90 lat, -180 to 180 lon)
- Cache geocoding results for 1 hour via Streamlit cache
"""
    )

with col2:
    st.markdown(
        """
**💾 4. Data Optimization**
- All data is processed in-memory after download from S3
- No local Parquet or Excel files are used as data sources
- S3 remains the canonical source for all data

**🔎 5. Search & Scoring**
- User enters client address and preferences
- System geocodes client location using cached rate-limited API
- Calculates distances using vectorized haversine formula
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
- Sourced directly from S3 bucket (single source of truth)
- Automatic updates when new files uploaded to S3
- Real-time workload calculations
- Historical referral tracking
- Missing geocode identification and resolution
"""
    )

with qa_col2:
    st.markdown(
        """
**🔄 S3-Only Architecture**
- AWS S3 is the canonical data source
- No local Parquet or Excel files are used for ingestion
- Automatic file selection (most recent by timestamp)
- Secure credential management via Streamlit secrets
- Connection pooling for optimal S3 performance

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

with st.expander("🔧 Technical Details (for developers)", expanded=False):
    st.markdown("### ☁️ S3 Data Architecture")

    st.markdown(
        """
        **AWS S3 as Single Source of Truth:**

        The application uses AWS S3 exclusively as the canonical data source. All data is downloaded from S3 on app launch and used directly for processing and recommendations. No local Parquet or Excel files are used for ingestion or as a source of truth.

        **S3 Bucket Structure:**
        ```
        jlg-provider-recommender-bucket/
        ├── 990046944/                              # Referrals folder
        │   ├── Referrals_App_Full_Contacts_2024-01-15.csv
        │   ├── Referrals_App_Full_Contacts_2024-02-10.csv
        │   └── Referrals_App_Full_Contacts_2024-03-01.csv  (latest)
        └── 990047553/                              # Preferred providers folder
            ├── Preferred_Providers_2024-01-15.csv
            └── Preferred_Providers_2024-03-01.csv  (latest)
        ```

        **S3 Configuration (`.streamlit/secrets.toml`):**
        ```toml
        [s3]
        aws_access_key_id = "YOUR_ACCESS_KEY"
        aws_secret_access_key = "YOUR_SECRET_KEY"
        bucket_name = "jlg-provider-recommender-bucket"
        region_name = "us-east-1"
        referrals_folder = "990046944"
        preferred_providers_folder = "990047553"
        ```

        **Auto-Update Workflow:**
        1. App launches and checks S3 configuration
        2. Connects to S3 bucket using boto3 client with connection pooling
        3. Lists files in configured folders (referrals and preferred providers)
        4. Selects most recent file based on timestamp in filename or S3 LastModified
        5. Downloads file for processing
        6. Triggers data cleaning pipeline
        7. Data ready for application use

        **S3 Client Optimizations:**
        - **Connection pooling**: Reuses boto3 session and client across requests
        - **Max pool connections**: 10 concurrent connections
        - **Adaptive retries**: Up to 3 retries with exponential backoff
        - **Parallel operations**: Downloads multiple files concurrently using ThreadPoolExecutor
        - **Efficient file selection**: Uses S3 ListObjects pagination for large folders
        """
    )

    st.markdown("### 🌐 API Integration Details")

    st.markdown(
        """
        **Geocoding API (Nominatim/OpenStreetMap):**

        The application uses the free Nominatim geocoding service with strict rate limiting:

        - **Service**: OpenStreetMap Nominatim API
        - **Rate limit**: 1 request per second (enforced by geopy.RateLimiter)
        - **Timeout**: 10 seconds per request
        - **Max retries**: 3 attempts with exponential backoff
        - **User agent**: "provider_recommender" (required by Nominatim ToS)
        - **Cache TTL**: 1 hour (Streamlit @st.cache_data decorator)
        - **Fallback behavior**: Returns None if service unavailable

        **Geocoding Request Flow:**
        ```python
        # Cached geocoding function with rate limiting
        @st.cache_data(ttl=3600)
        def geocode_address_with_cache(address: str) -> Optional[Tuple[float, float]]:
            geocode_fn = _get_rate_limited_geocoder()  # 1 req/sec limiter
            location = geocode_fn(address, timeout=10)
            return (location.latitude, location.longitude) if location else None
        ```

        **Error Handling:**
        - **GeocoderTimedOut**: Retry with exponential backoff (up to 3 times)
        - **GeocoderServiceError**: Display user-friendly warning, return None
        - **GeocoderUnavailable**: Service down, graceful degradation
        - **Network errors**: Connection issues detected and reported to user
        - **Rate limit exceeded**: Automatic throttling via RateLimiter

        **Cache Strategy:**
        - First geocode: API call (1-3 seconds depending on network)
        - Subsequent requests: Cached result (<10ms)
        - Cache invalidation: After 1 hour or on app restart
        - Cache key: Full address string (case-sensitive)

        **Performance Metrics:**
        - Uncached geocode: 1-3 seconds
        - Cached geocode: <10ms
        - Batch geocoding (100 addresses): ~200 seconds with rate limiting
        - Typical search page load: <1 second (cached data + cached geocode)
        """
    )

    st.markdown("### 📊 Data Ingestion Pipeline")

    st.markdown(
        """
        **DataIngestionManager Architecture:**

        Centralized data loading system with S3-only ingestion and intelligent caching.

        **Data Sources (Enum-based type safety):**
        ```python
        class DataSource(Enum):
            INBOUND_REFERRALS = "inbound"        # Referrals TO the firm
            OUTBOUND_REFERRALS = "outbound"      # Referrals FROM firm to providers
            ALL_REFERRALS = "all_referrals"      # Combined dataset
            PROVIDER_DATA = "provider"           # Aggregated unique providers
            PREFERRED_PROVIDERS = "preferred"    # Preferred provider contacts
        ```

        **File Loading Priority:**
        1. **S3 CSV** (latest file in each folder) - Always used for ingestion

        **Loading Strategy:**
        ```python
        manager = DataIngestionManager()
        df = manager.load_data(DataSource.OUTBOUND_REFERRALS)
        # Downloads latest file from S3
        # Applies source-specific transformations
        # Returns clean, validated DataFrame
        ```

        **Post-Processing by Source:**
        - **OUTBOUND_REFERRALS**: No additional processing (already clean)
        - **PROVIDER_DATA**: Aggregates by (name, address), sums referral counts
        - **PREFERRED_PROVIDERS**: Validates phone/address formats
        - **ALL_REFERRALS**: Combines inbound + outbound with deduplication

        **Caching Strategy:**
        - Streamlit `@st.cache_data` decorator with 1-hour TTL
        - Cache key includes data source and S3 file modification time
        - Cache invalidation on S3 file changes or manual refresh
        """
    )

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

        **Data Processing Pipeline:**
        ```
        1. S3 Download (boto3 with connection pooling)
           ↓
        2. CSV Parsing (pandas.read_csv with dtype optimization)
           ↓
        3. Data Cleaning (normalize addresses, phone numbers)
           ↓
        4. Deduplication (by normalized_name + normalized_address)
           ↓
        5. Geocoding (Nominatim API with rate limiting & caching)
           ↓
    6. Optional local caching to speed repeated loads (cache only; S3 is source of truth)
           ↓
        7. Application Loading (DataIngestionManager with cache)
           ↓
        8. Runtime Scoring & Filtering (vectorized NumPy operations)
           ↓
        9. Results Ranking & Display
        ```
"""
    )

    st.markdown("### Performance Optimizations")
    st.markdown(
        """
        - **Vectorized Operations**: NumPy arrays for distance calculations (much faster than Python loops)
        - **Streamlit Caching**: `@st.cache_data` for data loading (1-hour TTL)
        - **S3-Only Data Source**: All data is loaded directly from S3 (no local Parquet/Excel ingestion)
        - **Geocoding Cache**: 1-hour persistence to avoid redundant API calls
        - **Session State**: Preserves user preferences and search results
        - **S3 Connection Pooling**: Reuses boto3 clients (max 10 concurrent connections)
        - **Lazy Loading**: Data loaded only when needed, not on app startup

        **Typical Performance:**
        - S3 download (first time): 2-5 seconds for ~5MB CSV
        - S3 download (cached): <100ms (local file check)
        - Data loading (from S3): ~1-2 seconds for 10k rows
        - Distance calculation: <50ms for 100 providers (vectorized)
        - Geocoding (cached): <10ms
        - Geocoding (fresh): 1-3s (Nominatim with rate limiting)
        - Full search cycle: <1s for typical datasets (with caching)
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

st.markdown("## ☁️ S3 & API Architecture (Technical)")

st.markdown(
    """
This section provides technical details about the app's cloud infrastructure and external API integrations,
intended for developers, DevOps engineers, and technical stakeholders.
"""
)

tech_col1, tech_col2 = st.columns([1, 1])

with tech_col1:
    st.markdown(
        """
### 🗄️ AWS S3 Data Source

**Architecture Overview:**
- **Single Source of Truth**: S3 bucket contains all canonical data
- **Local Files**: Cache only (gitignored, auto-generated)
- **Auto-Update**: Downloads latest data on app launch
- **File Selection**: Automatic selection of most recent file by timestamp

**S3 Client Implementation:**
```python
# Optimized S3 client with connection pooling
from boto3 import Session
from botocore.config import Config

config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    max_pool_connections=10
)
client = session.client('s3', config=config)
```

**Required IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

**S3 Configuration Variables:**
- `aws_access_key_id`: AWS access key
- `aws_secret_access_key`: AWS secret key
- `bucket_name`: S3 bucket name
- `region_name`: AWS region (e.g., us-east-1)
- `referrals_folder`: Folder ID for referral data
- `preferred_providers_folder`: Folder ID for preferred providers
"""
    )

with tech_col2:
    st.markdown(
        """
### 🌐 Geocoding API Integration

**Service Provider:**
- **Primary**: Nominatim (OpenStreetMap)
- **Cost**: Free (community-supported)
- **Rate Limit**: 1 request/second (strictly enforced)
- **Terms**: User-Agent header required

**API Request Example:**
```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

geolocator = Nominatim(
    user_agent="provider_recommender"
)
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1.0,
    max_retries=3
)
location = geocode("123 Main St, City, State")
# Returns: (latitude, longitude) or None
```

**Response Format:**
```json
{
  "latitude": 34.0522,
  "longitude": -118.2437,
  "display_name": "123 Main St, Los Angeles, CA",
  "boundingbox": [...],
  "importance": 0.5
}
```

**Error Handling Strategy:**
- **Timeout**: Retry up to 3 times with exponential backoff
- **Service Unavailable**: Return None, log warning
- **Rate Limit**: Enforced client-side via RateLimiter
- **Invalid Address**: Return None, cache negative result
- **Network Error**: Display user-friendly message, retry

**Caching Implementation:**
```python
@st.cache_data(ttl=3600)  # 1-hour cache
def geocode_address_with_cache(address: str):
    # First call: API request (~1-3s)
    # Subsequent calls: Cached (<10ms)
    return geocode_fn(address, timeout=10)
```
"""
    )

st.markdown("### 🔒 Security & Configuration")

security_col1, security_col2 = st.columns([1, 1])

with security_col1:
    st.markdown(
        """
**Secrets Management:**

All sensitive credentials stored in `.streamlit/secrets.toml` (gitignored):

```toml
[s3]
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
bucket_name = "jlg-provider-recommender-bucket"
region_name = "us-east-1"
referrals_folder = "990046944"
preferred_providers_folder = "990047553"
```

**Production Deployment:**
- Use environment variables or cloud secrets manager
- Never commit secrets to version control
- Rotate credentials regularly
- Use least-privilege IAM policies
- Enable S3 bucket versioning for data recovery
"""
    )

with security_col2:
    st.markdown(
        """
**Network & Performance:**

**Connection Pooling:**
- Max 10 concurrent S3 connections
- Session reuse across requests
- Adaptive retry strategy (3 attempts)

**API Rate Limits:**
- Nominatim: 1 req/sec (client-side enforced)
- S3: No hard limit (but optimized for efficiency)

**Performance Monitoring:**
- S3 download time: Logged for each file
- Geocoding response time: Tracked per request
- Cache hit rate: Monitored via Streamlit metrics
- Data load time: Displayed in Data Dashboard

**Failure Recovery:**
- S3 unavailable: Use cached local files
- Geocoding failure: Continue with providers having coordinates
- Missing data: Graceful degradation with clear user messaging
"""
    )

st.markdown("### 📊 Data Flow Diagram")

st.markdown(
    """
```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS S3 Bucket                            │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │  Referrals Folder    │    │  Preferred Providers Folder  │  │
│  │  (990046944)         │    │  (990047553)                 │  │
│  │  - Latest CSV files  │    │  - Latest CSV files          │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────────────┘
                      │ boto3 client (connection pooling)
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Data Cleaning Pipeline                         │
│  - Cleans and processes S3 CSV data                             │
└─────────────────────┬────────────────────────────────────────────┘
                      │ DataIngestionManager
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Application Runtime                           │
│  - Search Page: Geocoding + Scoring + Filtering                 │
│  - Data Dashboard: Analytics + Visualization                    │
│  - Update Data: Manual S3 refresh trigger                       │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **S3 → App**: Automatic on app launch, manual refresh available
- **All data is loaded directly from S3**
- **Geocoding**: External API call with 1-hour result cache
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
    - Use available export options to download results
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
