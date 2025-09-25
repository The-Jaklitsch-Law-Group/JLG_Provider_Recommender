import datetime as dt
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from src.app_logic import filter_providers_by_radius  # re-export for tests
from src.app_logic import apply_time_filtering, load_application_data, run_recommendation, validate_provider_data
from src.utils.addressing import validate_address, validate_address_input
from src.utils.io_utils import get_word_bytes, sanitize_filename

# Maintain backward-compatible geocoding fallback expected by tests
try:
    import geopy  # noqa: F401

    GEOPY_AVAILABLE = True
    from src.utils.geocoding import geocode_address_with_cache  # real implementation
except Exception:  # pragma: no cover - environment dependent
    GEOPY_AVAILABLE = False

    def geocode_address_with_cache(address: str) -> Optional[Tuple[float, float]]:  # type: ignore
        """Fallback geocode function used when geopy isn't available.

        Returns None to indicate geocoding unavailable.
        """
        st.warning("geopy package not available. Geocoding disabled (returns None). Install with: pip install geopy")
        return None


st.set_page_config(page_title="Provider Recommender", page_icon=":hospital:", layout="wide")

__all__ = ["filter_providers_by_radius", "geocode_address_with_cache", "GEOPY_AVAILABLE"]

st.title("Provider Recommender")
st.caption("Enter client address and preferences below, then run Search. Results will appear below.")

with st.spinner("Loading provider data..."):
    provider_df, detailed_referrals_df = load_application_data()

if provider_df.empty:
    st.warning("No provider data loaded. Please verify data files.")

data_valid, data_msg = validate_provider_data(provider_df) if not provider_df.empty else (False, "")
if data_msg and not data_valid:
    st.warning(data_msg)

# Top-level expanders: search on top (expanded) and results below (expanded)
if st.session_state.get("search_expanded", True):
    with st.expander("Search", expanded=True):
        st.header("Search Parameters")

        street = str(st.text_input("Street", st.session_state.get("street", "14350 Old Marlboro Pike") or ""))
        city = str(st.text_input("City", st.session_state.get("city", "Upper Marlboro") or ""))
        state = str(st.text_input("State", st.session_state.get("state", "MD") or ""))
        zipcode = str(st.text_input("Zip", st.session_state.get("zipcode", "20772") or ""))

        full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
        if len(full_address) > 5:
            ok, msg = validate_address(full_address)
            if ok:
                st.caption("Address format OK.")
            elif msg:
                st.warning(msg)

        has_inbound = ("Inbound Referral Count" in provider_df.columns) if not provider_df.empty else False

        st.subheader("Scoring Weights")
        distance_weight = st.slider(
            "Distance Importance",
            0.0,
            1.0,
            st.session_state.get("distance_weight", 0.4 if has_inbound else 0.6),
            0.05,
        )
        outbound_weight = st.slider(
            "Outbound Referral Importance",
            0.0,
            1.0,
            st.session_state.get("outbound_weight", 0.4),
            0.05,
        )
        inbound_weight = 0.0
        if has_inbound:
            inbound_weight = st.slider(
                "Inbound Referral Importance",
                0.0,
                1.0,
                st.session_state.get("inbound_weight", 0.2),
                0.05,
            )
        total = distance_weight + outbound_weight + (inbound_weight if has_inbound else 0)
        if total == 0:
            st.error("At least one weight must be > 0.")
        alpha = distance_weight / total if total else 0.5
        beta = outbound_weight / total if total else 0.5
        gamma = inbound_weight / total if has_inbound and total else 0.0
        st.caption(
            f"Normalized Weights: Distance {alpha:.2f} | Outbound {beta:.2f}"
            + (f" | Inbound {gamma:.2f}" if has_inbound else "")
        )

        min_referrals = st.number_input(
            "Minimum Outbound Referral Count", 0, value=st.session_state.get("min_referrals", 0)
        )
        time_period = st.date_input(
            "Time Period",
            value=st.session_state.get("time_period", [dt.date.today() - dt.timedelta(days=365), dt.date.today()]),
        )
        use_time_filter = st.checkbox(
            "Enable time-based filtering", value=st.session_state.get("use_time_filter", True)
        )
        max_radius_miles = st.slider("Maximum Radius (miles)", 1, 200, st.session_state.get("max_radius_miles", 25))

        search_button = st.button("Search", type="primary")

        if search_button:
            addr_valid, addr_msg = validate_address_input(street, city, state, zipcode)
            if not addr_valid:
                st.error("Fix address issues before searching.")
                if addr_msg:
                    st.info(addr_msg)
                st.stop()
            if not GEOPY_AVAILABLE:
                st.error("Geocoding unavailable (geopy not installed).")
                st.stop()
            coords = geocode_address_with_cache(full_address) if GEOPY_AVAILABLE else None
            if not coords or not isinstance(coords, (list, tuple)):
                st.error("Could not geocode address.")
                st.stop()
            user_lat, user_lon = float(coords[0]), float(coords[1])
            # store search parameters in session state
            st.session_state["street"] = street
            st.session_state["city"] = city
            st.session_state["state"] = state
            st.session_state["zipcode"] = zipcode
            st.session_state["user_lat"] = float(user_lat)
            st.session_state["user_lon"] = float(user_lon)
            st.session_state["alpha"] = float(alpha)
            st.session_state["beta"] = float(beta)
            st.session_state["gamma"] = float(gamma)
            st.session_state["distance_weight"] = float(distance_weight)
            st.session_state["outbound_weight"] = float(outbound_weight)
            st.session_state["inbound_weight"] = float(inbound_weight)
            st.session_state["min_referrals"] = int(min_referrals)
            st.session_state["time_period"] = time_period
            st.session_state["use_time_filter"] = bool(use_time_filter)
            st.session_state["max_radius_miles"] = int(max_radius_miles)

            # Run recommendation immediately and store results
            with st.spinner("Scoring providers..."):
                best, scored_df = run_recommendation(
                    provider_df,
                    st.session_state["user_lat"],
                    st.session_state["user_lon"],
                    min_referrals=st.session_state["min_referrals"],
                    max_radius_miles=st.session_state["max_radius_miles"],
                    alpha=st.session_state["alpha"],
                    beta=st.session_state["beta"],
                    gamma=st.session_state.get("gamma", 0.0),
                )
                st.session_state["last_best"] = best
                st.session_state["last_scored_df"] = scored_df
            # collapse the search expander and ensure results are visible
            st.session_state["search_expanded"] = False
            st.session_state["results_expanded"] = True
            # immediately rerun so the UI reflects the collapsed state
            _rerun = getattr(st, "experimental_rerun", None)
            if callable(_rerun):
                try:
                    _rerun()
                except Exception:
                    pass
else:
    if st.button("Show Search"):
        st.session_state["search_expanded"] = True
        _rerun = getattr(st, "experimental_rerun", None)
        if callable(_rerun):
            try:
                _rerun()
            except Exception:
                pass

if st.session_state.get("results_expanded", True):
    with st.expander("Results", expanded=True):
        st.header("Recommended Provider")
        # Attempt to retrieve previous results from session state
        best = st.session_state.get("last_best")
        scored_df = st.session_state.get("last_scored_df")
        # rest of results block follows

        # If time filtering is enabled, provide a lightweight re-filter option
        if (
            st.session_state.get("use_time_filter")
            and isinstance(st.session_state.get("time_period"), list)
            and len(st.session_state["time_period"]) == 2
        ):
            start_date, end_date = st.session_state["time_period"]
            provider_for_display = apply_time_filtering(provider_df, detailed_referrals_df, start_date, end_date)
        else:
            provider_for_display = provider_df

        valid, msg = validate_provider_data(provider_for_display)
        if not valid and msg:
            st.warning(msg)

        if best is None or scored_df is None or (isinstance(scored_df, pd.DataFrame) and scored_df.empty):
            st.info("No results yet. Enter search parameters above and click Search.")
        else:
            provider_name = (
                best.get("Full Name", "Unknown Provider") if isinstance(best, pd.Series) else "Unknown Provider"
            )
            st.subheader(provider_name)

            if isinstance(best, pd.Series):
                if "Full Address" in best and best["Full Address"]:
                    st.write("Address:", best["Full Address"])
                if "Phone Number" in best and best["Phone Number"]:
                    st.write("Phone:", best["Phone Number"])

            cols = ["Full Name", "Full Address", "Distance (Miles)", "Referral Count"]
            if "Inbound Referral Count" in scored_df.columns:
                cols.append("Inbound Referral Count")
            if "Score" in scored_df.columns:
                cols.append("Score")
            available = [c for c in cols if c in scored_df.columns] if isinstance(scored_df, pd.DataFrame) else []
            if available:
                display_df = (
                    scored_df[available]
                    .drop_duplicates(subset=["Full Name"], keep="first")
                    .sort_values(by="Score" if "Score" in available else available[0])
                )
                with st.expander("View full scored list", expanded=True):
                    st.dataframe(display_df, hide_index=False, width="stretch")
            else:
                st.error("No displayable columns in results.")

            # Export selected provider as Word
            try:
                base_filename = f"Provider_{sanitize_filename(provider_name)}"
                with st.expander("Export / Share"):
                    st.download_button(
                        "Export Selected Provider (Word)",
                        data=get_word_bytes(best),
                        file_name=f"{base_filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
            except Exception as e:
                st.error(f"Export failed: {e}")

        with st.expander("Scoring Details", expanded=False):
            alpha = st.session_state.get("alpha", 0.5)
            beta = st.session_state.get("beta", 0.5)
            gamma = st.session_state.get("gamma", 0.0)
            st.markdown(
                f"Weighted score = Distance*{alpha:.2f} + Outbound*{beta:.2f}"
                + (f" + Inbound*{gamma:.2f}" if gamma > 0 else "")
            )
else:
    if st.button("Show Results"):
        st.session_state["results_expanded"] = True
        _rerun = getattr(st, "experimental_rerun", None)
        if callable(_rerun):
            try:
                _rerun()
            except Exception:
                pass
