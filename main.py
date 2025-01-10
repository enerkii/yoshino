import streamlit as st
import pandas as pd
import csv
from app import calculate


# Set page config for a cleaner look
st.set_page_config(
    page_title="Battery Simulation",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Add custom CSS to improve the UI
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 20px;
    }
    .main {
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description



st.title("Battery Simulation")
st.markdown("This is a simulation for the optimal battery size considering a load and pv profile. Please upload the data from a SolarEdge project – leave the data as is. Adjust the parameters as you need them (they have standard values).")

uploaded_file = st.file_uploader("SolarEdge_Data.csv", accept_multiple_files=False, type="csv")



### INPUT PARAMETERS
#--------------------------------
st.divider()
row1 = st.container()
with row1:
    col1, col2 = st.columns(2)
    with col1:
        st.header("💸 Energy Prices")
        customer = st.text_input("Project Name", value="Dunder Mifflin")
        energy_price_grid = st.number_input(
            "Grid Price (ct/kWh)",
            min_value=0.0,
            max_value=100.0,
            value=15.0,
            step=0.5,
            help="Enter the grid electricity price our customer pays in cents per kilowatt-hour.",
            format="%.1f"
        )

        feed_in_tariff = st.number_input(
            "Feed-in Tariff (ct/kWh)",
            min_value=0.0,
            max_value=100.0,
            value=8.0,
            step=0.5,
            help="Enter the feed-in tariff in cents per kilowatt-hour."
        )

        energy_price_ppa = st.number_input(
            "PPA Price (ct/kWh)",
            min_value=0.0,
            max_value=1000.0,
            value=12.0,
            step=0.5,
            help="Enter the estimated PPA price in cents per kilowatt-hour.",
            format="%.1f"
        )


    with col2:
        st.header("🔌 Grid Fees")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**>=2500 h:**")
            above_2500_consumption_price = st.number_input(
                "Consumption (ct/kWh)",
                min_value=0.0,
                max_value=100.0,
                value=6.0,
                step=0.5,
                help="Enter the grid fees in cents per kilowatt-hour for consumption above 2500 kWh."
            )

            above_2500_power_price = st.number_input(
                "Power Price (€/kW)",
                min_value=0.0,
                max_value=500.0,
                value=180.0,
                step=0.5,
                help="Enter the power price for the peak load in cents per kilowatt for consumption above 2500 kWh."
            )



        with col2:
            st.markdown("**<2500 h:**")
            below_2500_consumption_price = st.number_input(
                "Consumption (ct/kWh)",
                min_value=0.0,
                max_value=100.0,
                value=7.0,
                step=0.5,
                help="Enter the grid fees in cents per kilowatt-hour for consumption below 2500 kWh."
            )

            below_2500_power_price = st.number_input(
                "Power Price (€/kW)",
                min_value=0.0,
                max_value=100.0,
                value=40.0,
                step=0.5,
                help="Enter the power price for the peak load in cents per kilowatt for consumption below 2500 kWh."
            )


        other_fees = st.number_input(
            "Other Fees (ct/kWh)",
            min_value=0.0,
            max_value=100.0,
            value=2.0,
            step=0.5,
            help="Enter the other fees in cents per kilowatt-hour."
            )

st.divider()
row2 = st.container()
with row2:
    col1, col2 = st.columns(2)
    with col1:
        st.header("🏦 Financials")
        battery_price = st.number_input(
            "Battery Price (€/kWh)",
            min_value=0.0,
            max_value=1000.0,
            value=400.0,
            step=25.0,
            help="Enter the battery price in €/kWh",
            format="%.0f"
        )

        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=3.5,
            step=0.5,
            help="Enter the interest rate in %"
        )

        equity_share = st.number_input(
            "Equity Share (%)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=0.5,
            help="Enter the equity share in %",
            format="%.0f"
        )

        credit_duration = st.number_input(
            "Credit Duration (years)",
            min_value=5.0,
            max_value=50.0,
            value=20.0,
            step=5.0,
            help="Enter the credit duration in years",
            format="%.0f"
        )

        peak_shaving_share = st.number_input(
            "Peak Shaving Share (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=10.0,
            help="Enter the peak shaving share in %"
        )

    with col2:
        st.header("🔋 Battery")
        battery_capacity = st.slider(
            "Battery Capacity Analysis (kWh)",
            min_value=0.0,
            max_value=1000.0,
            value=(100.0, 350.0),
            step=50.0,
            format="%g kWh"
        )

        capacity_step = st.number_input(
            "Capacity Step",
            min_value=10.0,
            max_value=10000.0,
            value=50.0,
            step=25.0,
            help="Steps between considered battery capacities",
            format="%.0f"
        )

        battery_duration = st.number_input(
            "Battery Duration",
            min_value=0.0,
            max_value=50.0,
            value=2.0,
            step=0.25,
            help="Enter the battery duration in years",
        )

        conversion_efficiency = st.number_input(
            "Conversion Efficiency (%)",
            min_value=0.0,
            max_value=100.0,
            value=96.0,
            step=0.1,
            help="Enter the conversion efficiency in %"
        )



#--------------------------------

if st.button("Start Simulation", type="primary"):
    try:
        if uploaded_file is not None:
            solaredgeData = pd.read_csv(uploaded_file, skiprows=2, header=None)
    except:
        print("Please upload a valid SolarEdge_Data.csv file.")
        st.info("Please upload a valid SolarEdge_Data.csv file.")
        st.stop()


    parameters = {
        "project_name": customer,
        "power_prices": {
            "ppa_price": energy_price_ppa / 100,  # Umrechnung von ct/kWh zu €/kWh
            "net_power_price": energy_price_grid / 100,  # ct -> €
            "feed_in_price": feed_in_tariff / 100  # ct -> €
        },
        "grid_fees": {
            "below_2500": {
                "consumption_price": below_2500_consumption_price / 100,  # ct -> €
                "power_price": below_2500_power_price,  # €/kW bleibt gleich
                "other_fees": other_fees / 100  # ct -> €
            },
            "above_2500": {
                "consumption_price": above_2500_consumption_price / 100,  # ct -> €
                "power_price": above_2500_power_price,  # €/kW bleibt gleich
                "other_fees": other_fees / 100  # ct -> €
            }
        },
        "battery": {
            "capacity_start": battery_capacity[0],  # Startwert aus Slider
            "capacity_end": battery_capacity[1],  # Endwert aus Slider
            "capacity_step": capacity_step,
            "duration": battery_duration,
            "conversion_efficiency": conversion_efficiency / 100  # Prozent -> Dezimal
        },
        "financials": {
            "battery_price": battery_price,
            "interest_rate": interest_rate / 100,  # Prozent -> Dezimal
            "equity_share": equity_share / 100,  # Prozent -> Dezimal
            "credit_duration": credit_duration,
            "peak_savings_share": peak_shaving_share / 100
        }
    }

    try:
        data = calculate(parameters, solaredgeData)
    except NameError:
        st.info("Please upload a valid csv file and try again.")
        st.stop()

    #### Visualisierung Eigenverbrauchsoptimierung auf Battery Capacity
    #--------------------------------

    st.divider()
    st.markdown("## Battery Simulation Results")
    st.markdown("#### Finding the optimal battery capacity:")

    # ADD: Load Profile with bar chart of monthly

    st.markdown("#### Finding the optimal battery capacity:")
    st.markdown("**Added Consumption from Battery per Battery Capacity**")
    # Create empty lists to hold the x and y values
    capacity_values = []
    total_self_consumption_values = []

    # Loop through the data to extract the necessary values
    for entry in data:
        capacity_values.append(entry['capacity'])
        total_self_consumption_values.append(entry['selfConsumption']['fromBattery'])

    # Create a DataFrame for easier plotting
    df = pd.DataFrame({
        'Capacity': capacity_values,
        'Additional Self Consumption': total_self_consumption_values
    })

    # Use Streamlit to display the bar chart
    st.bar_chart(df.set_index('Capacity')['Additional Self Consumption'], color='#1C754F')


    st.markdown("**Peak Shaving per Battery Capacity**")
    shaved_values = []

    # Loop through the data to extract the necessary values
    for entry in range(len(data)):
        shaved_values.append(data[entry]['peakShaving']['peakReduction'])

    # Create a DataFrame for easier plotting
    df = pd.DataFrame({
        'Capacity': capacity_values,
        'PeakShaving': shaved_values
    })

    st.bar_chart(df.set_index('Capacity')['PeakShaving'], color='#4E71EE')

    st.markdown("**Financials per Battery Capacity**")
    total_savings = []
    for entry in range(len(data)):
        savings = data[entry]['financial']['peakPriceSavings'] + data[entry]['financial']['newPpaRevenue'] - data[entry]['financial']['lostRevenue'] - data[entry]['financial']['annualInterest']
        total_savings.append(savings)

    df = pd.DataFrame({
        'Capacity': capacity_values,
        'Additional Profit': total_savings
    })

    st.bar_chart(df.set_index('Capacity')['Additional Profit'], color='#FEC240')

    st.markdown("**Customer Impact**")
    st.bar_chart()
    # Add graphs:
        # autarkie for customer
        # net impact battery for customer (savings from peak shaving + savings from delta ppa – grid price) show financials here

    st.markdown("#### All Results:")
    st.json(data)

    # TBD: Load Profile
        # durchschnitt unter der woche
        # maximal werte pro stunde
        # minimale werte pro Stunde


    # PV Produktion + battery energy profile

    # Laod Profile with peak shaving according to best battery capacity
