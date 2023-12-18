'''
Name: Julian Yu
Section: CS230
Dataset: Boston Trash Schedule
URL:

'''
import pandas as pd
import streamlit as st
import pydeck as pdk
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

# Function to read data
def read_data(file_path):
    return pd.read_csv(file_path)

# Function to handle user input and filter data by neighborhood
def filter_data_by_neighborhoods(df, column_name):
    st.sidebar.header("Neighborhood Selection")
    selected_neighborhoods = st.sidebar.multiselect('Select Neighborhoods', df[column_name].unique())
    if selected_neighborhoods:
        filtered_data = df[df[column_name].isin(selected_neighborhoods)]
    else:
        filtered_data = pd.DataFrame(columns=df.columns)  # Empty DataFrame if no selection
    return selected_neighborhoods, filtered_data

def calculate_frequency(df, column_name, new_column_name):
    def count_days(day_str):
        return sum(day in day_str for day in ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']) if isinstance(day_str, str) else 0

    df[new_column_name] = df[column_name].apply(count_days)

def get_color(frequency, is_recycle=False):
    if is_recycle:
        return [0, 255, 0, 160] if frequency == 1 else [0, 0, 255, 160]  # Green for 1 collection, Blue for 2 or more
    else:
        return [255, 255, 0, 160] if frequency == 1 else [255, 0, 0, 160]  # Yellow and red for trash

def create_map(df, column_name, selected_neighborhood=None):
    df['color'] = df[column_name].apply(lambda freq: get_color(freq, column_name == 'RecycleFrequency'))

    map_data = df[['Neighborhood', 'y_coord', 'x_coord', 'color']]
    view_state = pdk.ViewState(latitude=df['y_coord'].mean(), longitude=df['x_coord'].mean(), zoom=11)

    if selected_neighborhood and not df[df['Neighborhood'] == selected_neighborhood].empty:
        focus = df[df['Neighborhood'] == selected_neighborhood].iloc[0]
        view_state = pdk.ViewState(latitude=focus['y_coord'], longitude=focus['x_coord'], zoom=15)

    r = pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer", map_data, get_position='[x_coord, y_coord]', get_color='color', get_radius=50, pickable=True)],
        initial_view_state=view_state,
        map_provider="mapbox",
        map_style=pdk.map_styles.SATELLITE,
        tooltip={"html": "<b>Neighborhood:</b> {Neighborhood}", "style": {"color": "white"}}
    )

    st.pydeck_chart(r)

def create_collection_chart(df, sort_order, data_type):
    column_name = 'RecycleFrequency' if data_type == 'recycling' else 'Frequency'

    total_collections = df.groupby('Neighborhood')[[column_name]].sum().reset_index()
    sorted_data = total_collections.sort_values(by=column_name, ascending=(sort_order == 'Ascending'))

    plt.figure(figsize=(10, 6))
    chart = sns.barplot(x=column_name, y='Neighborhood', data=sorted_data)
    title = 'Total Recycling Collections by Neighborhood' if data_type == 'recycling' else 'Total Trash Collections by Neighborhood'
    chart.set_title(title)
    chart.set_xlabel('Total Collections')
    chart.set_ylabel('Neighborhood')

    return plt.gcf()

def split_days(day_str):
    days = []
    if not isinstance(day_str, str):
        return days

    # Check for multi-character day abbreviations first
    day_mapping = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'TH': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'SU': 'Sunday'}
    for multi_day in ['TH', 'SU']:
        if multi_day in day_str:
            days.append(day_mapping[multi_day])
            day_str = day_str.replace(multi_day, '')

    # Check for single-character day abbreviations
    for single_day in ['M', 'T', 'W', 'F', 'S']:
        if single_day in day_str:
            days.append(day_mapping[single_day])

    return days

def create_trashday_bar_chart(df):
    # Expand trashday column into separate rows for each day
    df['ExpandedDays'] = df['trashday'].apply(split_days)
    expanded_df = df.explode('ExpandedDays')

    day_count = expanded_df.groupby(['Neighborhood', 'ExpandedDays']).size().reset_index(name='Count')

    # Custom order for days of the week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Create the seaborn bar chart
    plt.figure(figsize=(12, 8))
    chart = sns.barplot(x='ExpandedDays', y='Count', hue='Neighborhood', data=day_count, order=day_order)
    chart.set_title('Trash Collection Days Frequency by Neighborhood')
    chart.set_xlabel('Day')
    chart.set_ylabel('Frequency')
    plt.xticks(rotation=45)

    st.pyplot(plt)
def display_charts_and_summary_table(df, sort_order):
    # Display charts
    st.write("Total Trash Collections by Neighborhood")
    fig = create_collection_chart(df, sort_order, 'trash')
    st.pyplot(fig)

    st.write("Total Recycling Collections by Neighborhood")
    recycle_fig = create_collection_chart(df, sort_order, 'recycling')
    st.pyplot(recycle_fig)

    # Display the sorted total collections data
    st.write("Total Trash and Recycling Collections by Neighborhood")
    st.table(df.groupby('Neighborhood')[['Frequency', 'RecycleFrequency']].sum().reset_index())

def display_maps_and_detailed_table(df):
    st.sidebar.header("Map Filter Options")
    show_one_collection = st.sidebar.checkbox('Show Locations with One Collection', True)
    show_two_or_more_collections = st.sidebar.checkbox('Show Locations with Two or More Collections', True)
    selected_neighborhoods, _ = filter_data_by_neighborhoods(df, 'Neighborhood')

    if selected_neighborhoods:
        # Combine conditions based on checkboxes
        neighborhood_data = df[df['Neighborhood'].isin(selected_neighborhoods)]
        if show_one_collection and not show_two_or_more_collections:
            filtered_data = neighborhood_data[neighborhood_data['Frequency'] == 1]
        elif show_two_or_more_collections and not show_one_collection:
            filtered_data = neighborhood_data[neighborhood_data['Frequency'] >= 2]
        elif show_one_collection and show_two_or_more_collections:
            filtered_data = neighborhood_data
        else:
            filtered_data = pd.DataFrame(columns=df.columns)  # Empty DataFrame if no boxes are checked

        # Display maps for the filtered data
        if not filtered_data.empty:
            st.subheader("Trash Collection Map")
            create_map(filtered_data, 'Frequency', None)

            st.subheader("Recycling Collection Map")
            create_map(filtered_data, 'RecycleFrequency', None)

def main():
    file_path = r'E:\pythin\FinalProject\trashschedulesbyaddress_7000_sample.csv'
    df = read_data(file_path)

    # Process data
    df.rename(columns={
        'sam_address_id': 'Address ID',
        'full_address': 'Full Address',
        'mailing_neighborhood': 'Neighborhood',
        'state': 'State',
        'recollect': 'Recycle Date',
        'latitude': 'y_coord',
        'longitude': 'x_coord',
    }, inplace=True)
    calculate_frequency(df, 'trashday', 'Frequency')
    calculate_frequency(df, 'Recycle Date', 'RecycleFrequency')

    st.title("🚯Trash Schedule Explorer🚯")
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Choose a page", ["Welcome", "Total Collection Weekly", "Trash Collection Map View"])

    if page == "Welcome":
        st.header("Welcome to the Boston Trash Collection Schedule Explorer")
        st.write("""
                This application provides insights into trash and recycling collection schedules across different neighborhoods.
                - Use the **Total Collection Weekly** page to view the frequency of trash and recycling collection in a tabular and graphical format.
                - The **Trash Collection Map View** page displays interactive maps showing collection locations.
                Explore the application using the sidebar options to navigate between different views.
            """)
        image_path = 'E:\pythin\FinalProject\maxresdefault.jpg'
        image = Image.open(image_path)
        st.image(image)

    elif page == "Total Collection Weekly":
        sort_order = st.sidebar.selectbox('Select Sorting Order for Total Collections', ['Ascending', 'Descending'])
        display_charts_and_summary_table(df, sort_order)
        st.write("Trash Collection Days Frequency by Neighborhood")
        create_trashday_bar_chart(df)

    elif page == "Trash Collection Map View":
        display_maps_and_detailed_table(df)


if __name__ == "__main__":
    main()