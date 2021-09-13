import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")

with st.sidebar:
    '''
    # Occupancy Spreadsheet Explorer
    '''
    csv_file = st.file_uploader("Choose file to upload")

def startup_screen():
    st.write('''
    ## Welcome to the occupancy spreadsheet explorer. 
    To begin, use the file uploader feature in the sidebar to the left.

    Upload an occupancy spreadsheet saved as .xlsx to load the explorer. 
    
    For the most recent data, open up the occupancy spreadsheet and from the menu select "Download as Microsoft Excel (.xlsx)". Sheet concatenation, typo corrections, and vacancy aggregations will be done automatically.
    ''')

def main():
    df = pd.read_csv(csv_file)

    # df.replace(["UCX3", "UCX9"], "UCXX", inplace=True)
    df.dropna(thresh=2,inplace=True)

    '''## All offices, all locations'''
    df2 = df[df["Type"] != "Storage"].dropna().reset_index(drop=True)
    df2 = df2[~df2["Location"].isin(["CPL","NHO","UMA","DTH+PARKING INFO","FWD","HUP","MB2"])]
    df2["Vacancy"] = df2["Status"]
    df2["Vacancy"].replace(
        ["Occupied", "Notice", "Pre-Leased"], "Occupied", inplace=True)
    df2["Vacancy"].replace(["WS | COWORKING", "WS | STAFF"],
                        "Unavailable", inplace=True)
    df2["Vacancy"].replace(["MIR Process", "Available"], "Vacant", inplace=True)

    df2
    f'''Note: there are {df2.shape[0]} offices with {df2.shape[1]} columns of data in this sheet. If that number seems off, check for possible discrepancies.'''

    vacant = df2[df2["Vacancy"].isin(["Vacant"])]

    '''### Summary statistics'''

    '''#### Offices per location'''
    st.text(df2.groupby(["Location"]).size())
    '''#### Offices by suite name'''
    st.text(df2.groupby(["Suite"]).size())
    '''#### Offices by type'''
    st.text(df2.groupby(["Type"]).size())
    '''#### Offices by status'''
    st.text(df2.groupby(["Status"]).size())
    '''#### Offices by vacancy'''
    st.text(df2.groupby(["Vacancy"]).size())

    col1, col2 = st.beta_columns(2)
    with col1:
        '''#### Total offices by desk count'''
        st.bar_chart(df2.groupby(["Desks"]).size())
    with col2:
        '''#### Vacant offices by desk count'''
        st.bar_chart(vacant.groupby(["Desks"]).size())
    
    st.write(f'''
    There are **{vacant.shape[0]}** vacant offices and **{df2.shape[0]-vacant.shape[0]}** not vacant offices out of **{df2.shape[0]}** total offices.
    That gives an office occupancy rate of **{round((df2.shape[0]-vacant.shape[0])/df2.shape[0],3)*100}%**.
    There are **{vacant["Desks"].sum()}** vacant desks and **{df2["Desks"].sum()-vacant["Desks"].sum()}** not vacant desks out of **{df2["Desks"].sum()}** total desks.
    That gives a desk occupancy rate of **{round((df2["Desks"].sum()-vacant["Desks"].sum())/df2["Desks"].sum(),3)*100}%**.
    ''')

    # st.write(alt.Chart(df2[["Location", "Desks", "Vacancy"]]).mark_bar().encode(
    #     x='Location',
    #     y='Desks',
    #     color='Vacancy'
    # ).interactive())

    st.altair_chart(alt.Chart(df2[["Type", "Desks", "Vacancy"]]).mark_bar().encode(
            x='sum(Desks)',
            y='Type',
            color='Vacancy'
        ).interactive())


    col3, col4 = st.beta_columns(2)
    with col3:
        '''#### Total offices by desk count by vacancy status'''
        st.altair_chart(alt.Chart(df2[df2["Vacancy"] != "Unavailable"][["Desks", "Office #","Vacancy"]]).mark_bar().encode(
            x=alt.X('Desks', title='# of Desks'),
            y=alt.Y('count(Office #)', title="# of Offices"),
            color='Vacancy'
        ).interactive())
    with col4: 
        '''#### Total desks by desk count per office by vacancy status'''
        st.altair_chart(alt.Chart(df2[df2["Vacancy"] != "Unavailable"][["Desks", "Office #","Vacancy"]]).mark_bar().encode(
            x=alt.X('Desks', title='# of Desks per Office'),
            y=alt.Y('sum(Desks)', title="Total # of Desks"),
            color='Vacancy'
        ).interactive())


    '''
    ### Office status by office type
    Count of offices by type given their current status. Helpful for understanding inventory mix and availability.
    '''
    df_c = df2.pivot_table(index='Type', columns='Vacancy', values='Desks', aggfunc='count')
    df_c.drop(columns=["Unavailable"],inplace=True)
    df_c.fillna(0,inplace=True)
    df_c["Total"] = df_c["Occupied"] + df_c["Vacant"]
    df_c["Occupancy"] = df_c["Occupied"] / df_c["Total"]
    df_c


    '''
    ### Offices by size (desk count) and vacancy status for all locations
    % of Total shows the percentage of all vacant offices by size of office. 
    '''
    df_d = df2.pivot_table(index=['Desks'], columns='Vacancy', values='Office #', aggfunc='count')
    df_d.reset_index(inplace=True)
    df_d = df_d.rename(columns = {'index':'Desks'})
    df_d.drop(columns=["Unavailable"],inplace=True)
    df_d.fillna(0,inplace=True)
    df_d["Total"] = df_d["Occupied"] + df_d["Vacant"]
    df_d["Occupancy"] = df_d["Occupied"] / df_d["Total"]

    df_d["% of Total"] = round((df_d["Total"] / df_d["Total"].sum()) * 100,1)

    df_d
    f'''Note: there are {df_d["Total"].sum()} available offices included in the above table. Unavailable offices, including staff, coworking, and storage, were excluded.'''


    df_x = df2.pivot_table(index=['Location','Desks'], columns='Vacancy', values='Office #', aggfunc='count')
    df_x.drop(columns=["Unavailable"],inplace=True)
    df_x.fillna(0,inplace=True)
    df_x.reset_index(inplace=True)
    df_x = df_x.rename(columns={'Location':'Location'})
    df_x["Total"] = df_x["Occupied"] + df_x["Vacant"]
    df_x["Occupancy"] = df_x["Occupied"] / df_x["Total"]

    df_x["% of Total"] = df_x["Total"] / df_x["Total"].sum()

    '''
    ### Offices by desk count for all locations
    '''
    df_x

    locations = list(set(df_x["Location"]))

    '''
    ### Offices by desk count for a single location
    Select a location to view a breakdown of offices by desk count.
    '''
    x = st.selectbox(options=locations, label="Location")
    z = df_x.loc[df_x["Location"] == x]
    z


    '''
    ### Offices by location for a single office size (desk count)
    Select a number of desks to view statistics on offices by location
    '''
    desks = df_x[["Desks"]]
    x = st.selectbox(options=desks, label="Desks")

    Z = df_x.loc[df_x["Desks"] == x]
    Z

if __name__ == "__main__":
    main()