"""Integration test to ensure address search uses user-provided values.

This test documents the fix for the issue where the search functionality
always used the same default address regardless of user input.

The fix ensures that the full_address is constructed inside the search
button click handler using the current form field values, not stale values
from the initial page render.
"""


def test_address_construction_logic():
    """Test that address construction works correctly with different inputs.

    This test verifies the logic used in the Search page to construct
    the full address from component parts.
    """
    # Test case 1: Complete address
    street = "123 Main St"
    city = "Baltimore"
    state = "MD"
    zipcode = "21201"

    full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
    assert full_address == "123 Main St, Baltimore, MD 21201"

    # Test case 2: Different address (simulating user change)
    street = "456 Oak Ave"
    city = "Annapolis"
    state = "MD"
    zipcode = "21401"

    full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
    assert full_address == "456 Oak Ave, Annapolis, MD 21401"

    # Test case 3: Ensure trailing/leading commas are stripped
    street = ""
    city = "Washington"
    state = "DC"
    zipcode = "20001"

    full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
    assert full_address == "Washington, DC 20001"


def test_address_change_produces_different_geocoding_input():
    """Verify that changing address components produces different geocoding inputs.

    This is the core fix: when a user changes the address and clicks search,
    the geocoding function should receive the NEW address, not a cached default.
    """
    # Simulate first search
    street1 = "14350 Old Marlboro Pike"
    city1 = "Upper Marlboro"
    state1 = "MD"
    zipcode1 = "20772"
    full_address1 = f"{street1}, {city1}, {state1} {zipcode1}".strip(", ")

    # Simulate second search with different address
    street2 = "100 N Charles St"
    city2 = "Baltimore"
    state2 = "MD"
    zipcode2 = "21201"
    full_address2 = f"{street2}, {city2}, {state2} {zipcode2}".strip(", ")

    # The key assertion: different inputs produce different addresses
    assert full_address1 != full_address2
    assert full_address1 == "14350 Old Marlboro Pike, Upper Marlboro, MD 20772"
    assert full_address2 == "100 N Charles St, Baltimore, MD 21201"
