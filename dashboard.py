import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import openpyxl
from urllib.request import urlopen
import json

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PACE Enrollment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Styling (Premium Look)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }

    /* Cards/Metrics */
    .css-1r6slb0, .css-1wivap2 {
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """Lengths the combined enrollment data from Excel."""
    file_path = 'outputs/Combined enrollment.xlsx'
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_geojson():
    """Loads CA Counties GeoJSON."""
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/california-counties.geojson'
    with urlopen(url) as response:
        geojson = json.load(response)
    return geojson

# -----------------------------------------------------------------------------
# Data Processing
# -----------------------------------------------------------------------------
def process_data(df):
    """Aggregates data for the stacked bar chart."""
    if df.empty:
        return df, []

    # Rank by total enrollment sum across all dates.
    county_totals = df.groupby('COUNTY')['ENROLLED'].sum().sort_values(ascending=False)
    top_counties = county_totals.head(7).index.tolist()
    
    # Assign group
    df['County_Grouped'] = df['COUNTY'].apply(lambda x: x if x in top_counties else 'Others')
    
    # Aggregate
    df_grouped = df.groupby(['DATE', 'County_Grouped'])['ENROLLED'].sum().reset_index()
    
    return df_grouped, top_counties

# -----------------------------------------------------------------------------
# Main Dashboard
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Main Dashboard
# -----------------------------------------------------------------------------
def main():
    # --- Sidebar Navigation ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Methodology", "Enrollment Trends", "Geographic Distribution", "Provider Insights" , "Strategy Write-up"])
    
    df = load_data()
    if df.empty:
        st.warning("No enrollment data available. Please check the 'outputs' folder.")
        # Continue anyway to show Provider page if possible, but usually main loop depends on it.
        # Let's ensure at least basic layout works.

    # --- Page 1: Methodology ---
    if page == "Methodology":
        st.title("📐 Methodology")
        
        st.subheader("📈 Data")
        st.markdown("""
        - 2023 Medicare Provider Data
        - Monthly MA enrollment data as published by CMS
        - Geographic reference tables to get zip to county mapping
        """)

        st.subheader("⚙️ Process")
        st.markdown("""
        1. **Data Pipeline**: Wrote Python scripts to download, extract, and standardize monthly CMS enrollment data and provider records.
        2. **Geospatial Mapping**: Integrated external Zip-to-County crosswalks to align provider locations with enrollment markets.
        3. **Strategic Analysis**: Identified top 10 counties by PACE volume and calculated specific KPIs (e.g., Provider Density per 100 MA Enrollees, Cost vs. State Benchmarks).
        4. **Visualization**: Built an interactive Streamlit dashboard to explore trends, network gaps, and specialty costs.
        """)

        st.subheader("🔨 Tools Used")
        st.markdown("""
        - **Python**: Coding backbone
        - **Pandas / NumPy**: Data processing
        - **Streamlit**: Dashboard framework
        - **Plotly**: Interactive visualizations
        - **GitHub**: Version control
        - **PyCharm**: IDE
        - **Google Antigravity**: Agentic IDE
        """)

    # --- Page 2: Enrollment Trends ---
    if page == "Enrollment Trends":
        if df.empty: return
        st.title("📊 PACE Enrollment Trends")
        st.markdown("Visualize enrollment growth over time by county.")

        # Optional: Date Range Filter
        min_date = df['DATE'].min()
        max_date = df['DATE'].max()
        
        start_date, end_date = st.sidebar.date_input(
            "Select Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        # Filter data based on date
        mask = (df['DATE'] >= pd.to_datetime(start_date)) & (df['DATE'] <= pd.to_datetime(end_date))
        filtered_df = df.loc[mask]

        st.subheader("📊 Enrollment Over Time by County")
        
        chart_data, top_counties = process_data(filtered_df)
        
        fig_bar = px.bar(
            chart_data,
            x='DATE',
            y='ENROLLED',
            color='County_Grouped',
            title="Enrollment Growth",
            template="plotly_dark",
            labels={
                'ENROLLED': 'Enrolled Members', 
                'DATE': 'Year Mth',
                'County_Grouped': 'County'
            }, 
            hover_data={
                "DATE": "|%b %Y",
                "ENROLLED": ":,",
                "County_Grouped": True
            },
            color_discrete_sequence=px.colors.qualitative.Pastel,
            category_orders={"County_Grouped": top_counties + ["Others"]}
        )
        
        fig_bar.update_layout(
            legend_title_text='County',
            xaxis_title="Date",
            yaxis_title="Enrolled Members",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=40, b=0),
            height=600
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Page 3: Geographic Distribution ---
    elif page == "Geographic Distribution":
        if df.empty: return
        st.title("🗺️ Geographic Distribution")
        st.markdown("View enrollment by county across California.")

        # Slider for Date Selection
        # Get unique dates sorted
        dates = df['DATE'].sort_values().unique()
        # Convert to datetime objects for display if needed, but slider works with timestamps
        
        # Select Slider
        selected_date = st.select_slider(
            "Select Date",
            options=dates,
            format_func=lambda x: pd.to_datetime(x).strftime('%b %Y'),
            value=dates[-1] # Default to latest
        )
        
        st.info(f"Showing data for: **{pd.to_datetime(selected_date).strftime('%B %Y')}**")
        
        # Filter for selected date
        latest_df = df[df['DATE'] == selected_date]
        
        # Load GeoJSON to get ALL counties
        try:
            geojson = load_geojson()
            
            # Extract all county names from GeoJSON
            all_counties = [feature['properties']['name'] for feature in geojson['features']]
            all_counties_df = pd.DataFrame({'COUNTY': all_counties})
            
            # Merge with enrollment data
            # Use left join to ensure all counties are present
            map_data = pd.merge(all_counties_df, latest_df, on='COUNTY', how='left')
            
            # Fill NaN values with 0 for enrollment
            map_data['ENROLLED'] = map_data['ENROLLED'].fillna(0)
            
            # Calculate global range for consistent coloring
            max_enrolled = df['ENROLLED'].max()
            
            fig_map = px.choropleth(
                map_data,
                geojson=geojson,
                locations='COUNTY',
                featureidkey="properties.name",
                color='ENROLLED',
                color_continuous_scale="Viridis",
                range_color=[0, max_enrolled], # Fixed scale
                scope="usa", 
                title=f"Enrollment by County ({pd.to_datetime(selected_date).strftime('%b %Y')})",
                template="plotly_dark",
                labels={
                    'COUNTY': 'County',
                    'ENROLLED': 'Enrolled Members'
                },
                hover_data={"COUNTY": True, "ENROLLED": ":,"}
            )
            
            # center on CA and zoom in
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(
                margin={"r":0,"t":40,"l":0,"b":0}, 
                height=800, # Increased height
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
            
        except Exception as e:
            st.error(f"Could not load map: {e}")
            st.dataframe(latest_df)

    # --- Page 4: Provider Insights ---
    elif page == "Provider Insights":
        st.title("🩺 Provider Network Insights")
        st.markdown("Strategic assessment of Medicare providers in key PACE counties.")
        
        # Load detailed data and benchmarks
        try:
            prov_df = pd.read_csv('outputs/provider_data_detailed.csv')
            state_benchmarks = pd.read_csv('outputs/kpi_state_benchmarks.csv')
            # Load MA Enrollment for Gap Analysis
            ma_enrl_df = pd.read_csv('outputs/ma_county_enrollment.csv')
        except FileNotFoundError:
            st.error("KPI Data not found. Please run `process_provider_data.py` first.")
            return

        # --- Interactivity: County Filter ---
        available_counties = sorted(prov_df['county'].unique())
        selected_counties = st.multiselect(
            "Filter by County",
            options=available_counties,
            default=available_counties,
            help="Select one or more counties to update the analysis."
        )
        
        if not selected_counties:
            st.warning("Please select at least one county.")
            return

        # Filter Data
        filtered_prov = prov_df[prov_df['county'].isin(selected_counties)]
        
        # --- DYNAMIC CALCS ---
        
        # 1. KPI Cards
        col1, col2, col3 = st.columns(3)
        total_spend = filtered_prov['Tot_Mdcr_Pymt_Amt'].sum()
        total_benes = filtered_prov['Tot_Benes'].sum()
        
        # Top specialty in selection
        if not filtered_prov.empty:
            top_spec = filtered_prov.groupby('Rndrng_Prvdr_Type')['Tot_Mdcr_Pymt_Amt'].sum().idxmax()
        else:
            top_spec = "N/A"
            
        with col1:
            st.metric("Total Medicare Spend (Selection)", f"${total_spend/1e9:.2f}B")
        with col2:
            st.metric("Total Benes in Selection", f"{total_benes:,.0f}")
        with col3:
            st.metric("Top Specialty", top_spec)
        
        st.divider()
        
        if filtered_prov.empty:
            st.warning("No providers found for selection.")
            return

        # 2. Top Specialties Chart (Dynamic) - Scatter Plot
        st.subheader("Specialty Landscapes: Volume vs. Intensity")
        st.markdown("**Size of Bubble = Total Medicare Spend**")
        
        # Group by Specialty
        spec_metrics = filtered_prov.groupby('Rndrng_Prvdr_Type')[['Tot_Mdcr_Pymt_Amt', 'Tot_Benes']].sum().reset_index()
        
        # Calculate Intensity (Avg Cost per Bene)
        spec_metrics['Avg_Cost_Per_Bene'] = spec_metrics['Tot_Mdcr_Pymt_Amt'] / spec_metrics['Tot_Benes']
        
        # Filter to relevant specialties (e.g., Top 20 by Spend)
        top_spec_metrics = spec_metrics.sort_values('Tot_Mdcr_Pymt_Amt', ascending=False).head(20)
        
        fig_spec = px.scatter(
            top_spec_metrics,
            x='Tot_Benes',
            y='Avg_Cost_Per_Bene',
            size='Tot_Mdcr_Pymt_Amt',
            color='Rndrng_Prvdr_Type', # Different color for each for distinction
            hover_name='Rndrng_Prvdr_Type',
            title="Volume (Benes) vs. Intensity (Cost/Bene)",
            template="plotly_dark",
            labels={
                'Tot_Benes': 'Total Beneficiaries (Volume)', 
                'Avg_Cost_Per_Bene': 'Avg Cost per Bene (Intensity)',
                'Tot_Mdcr_Pymt_Amt': 'Total Spend',
                'Rndrng_Prvdr_Type': 'Specialty'
            },
            height=600
        )

        fig_spec.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b><br><br>"
                "<b>Total Beneficiaries:</b> %{x:.2s}<br>"
                "<b>Avg Cost per Bene:</b> $%{y:,.0f}<br>"
                "<b>Total Spend:</b> $%{marker.size:,.2s}<br>"
                "<extra></extra>"
            )
        )

        
        # Add Quadrant Lines (Median)
        x_med = top_spec_metrics['Tot_Benes'].median()
        y_med = top_spec_metrics['Avg_Cost_Per_Bene'].median()
        
        fig_spec.add_hline(y=y_med, line_dash="dot", annotation_text="Median Intensity", annotation_position="bottom right")
        fig_spec.add_vline(x=x_med, line_dash="dot", annotation_text="Median Volume", annotation_position="top right")
        
        st.plotly_chart(fig_spec, use_container_width=True)
        
        # 3. Cost Benchmarks (Dynamic vs State) - TOP 10 BY VOLUME
        st.subheader("💰 Cost Benchmarks: Selected Counties vs CA Avg")
        st.markdown("Comparison for Top 10 High-Volume Specialties")
        
        # Filter Benchmarks to Top 10 by VOLUME
        top_vol_specs = spec_metrics.sort_values('Tot_Mdcr_Pymt_Amt', ascending=False).head(10)['Rndrng_Prvdr_Type'].tolist()
        
        # Calculate local avg cost per bene
        spec_metrics['Selected_Avg_Cost'] = spec_metrics['Tot_Mdcr_Pymt_Amt'] / spec_metrics['Tot_Benes']
        
        # Merge with State Benchmarks
        bench_df = pd.merge(spec_metrics[['Rndrng_Prvdr_Type', 'Selected_Avg_Cost']], 
                            state_benchmarks, 
                            on='Rndrng_Prvdr_Type', how='inner')
        
        # Filter to top volume specs
        bench_df = bench_df[bench_df['Rndrng_Prvdr_Type'].isin(top_vol_specs)]
        
        # Melt for plot
        bench_melt = bench_df.melt(id_vars='Rndrng_Prvdr_Type', 
                                   value_vars=['Selected_Avg_Cost', 'State_Avg_Cost'],
                                   var_name='Metric', value_name='Cost_Per_Bene')
        
        fig_bench = px.bar(
            bench_melt,
            x='Rndrng_Prvdr_Type',
            y='Cost_Per_Bene',
            color='Metric',
            barmode='group',
            title="Cost per Beneficiary (Top 10 High-Volume Specialties)",
            template="plotly_dark",
            labels={
                'Cost_Per_Bene': 'Avg Cost ($)', 
                'Rndrng_Prvdr_Type': 'Specialty',
                'State_Avg_Cost': 'State Avg Cost ($)',
                'Selected_Avg_Cost': 'Counties Avg Cost ($)'
                }
        )

        fig_bench.update_traces(
            hovertemplate=(
                "<b>Specialty:</b> %{x}<br>"
                "<b>Avg Cost:</b> $%{y:,.0f}<br>"
                "<extra></extra>"
            )
        )

        fig_bench.for_each_trace(
            lambda t: t.update(
                name="Selected Counties Avg"
                if t.name == "Selected_Avg_Cost"
                else "CA State Avg"
            )
        )

        st.plotly_chart(fig_bench, use_container_width=True)
        
        # 4. Gap Analysis (Dynamic) - USING TOTAL MA ENROLLMENT
        st.subheader("📍 Network Gaps: Provider Density (Selection)")
        st.markdown("Providers per 100 Total MA Enrollees")
        
        # --- Specialty Filter for Gap Analysis ---
        # Get unique list of ALL specialties or just from selection? 
        # Using selection ensures we don't pick something with 0 providers.
        gap_specialties = sorted(filtered_prov['Rndrng_Prvdr_Type'].unique().tolist())
        gap_specialties.insert(0, "All Specialties")
        
        selected_gap_spec = st.selectbox("Filter Gap Analysis by Specialty", gap_specialties)
        
        if selected_gap_spec == "All Specialties":
            gap_filtered_prov = filtered_prov
            title_suffix = "(All Specialties)"
        else:
            gap_filtered_prov = filtered_prov[filtered_prov['Rndrng_Prvdr_Type'] == selected_gap_spec]
            title_suffix = f"({selected_gap_spec})"
        
        # Calculate Provider Counts per County (in selection)
        prov_counts = gap_filtered_prov.groupby('county')['Rndrng_NPI'].nunique().reset_index(name='Provider_Count')
        
        # Merge with Total MA Enrollment
        gap_df = pd.merge(prov_counts, ma_enrl_df, left_on='county', right_on='COUNTY', how='left')
        gap_df['MA_ENROLLED'] = gap_df['MA_ENROLLED'].fillna(0) # Avoid div by zero issues if any
        
        # Calc Density
        gap_df['Providers_Per_100_MA_Enrolled'] = (gap_df['Provider_Count'] / gap_df['MA_ENROLLED']) * 100
        # Handle Inf if enrollment is 0
        gap_df = gap_df[gap_df['MA_ENROLLED'] > 0]
        
        gap_df = gap_df.sort_values('Providers_Per_100_MA_Enrolled', ascending=True)
        
        fig_gap = px.bar(
            gap_df,
            x='Providers_Per_100_MA_Enrolled',
            y='county',
            orientation='h',
            title=f"Provider Density per 100 MA Enrollees {title_suffix}",
            template="plotly_dark",
            color='Providers_Per_100_MA_Enrolled',
            color_continuous_scale='Redor',
            labels={'county': 'County', 'Providers_Per_100_MA_Enrolled': 'Providers per 100 MA Enrollees'}
        )

        fig_gap.update_traces(
            hovertemplate=(
                "<b>County:</b> %{y}<br>"
                "<b>Providers per 100 MA Enrollees:</b> %{x:.2f}<br>"
                "<extra></extra>"
            )
        )
        
        # --- Add National Benchmark Line ---
        # Only if "All Specialties" is selected (since we only calc national total count)
        if selected_gap_spec == "All Specialties":
            try:
                nat_stats = pd.read_csv('outputs/national_stats.csv')
                nat_prov_count = nat_stats.loc[nat_stats['Metric'] == 'National_Provider_Count', 'Value'].values[0]
                
                nat_enrl = pd.read_csv('outputs/MA_Enrollment_National.csv')
                latest_nat_enrl = nat_enrl.sort_values('DATE').iloc[-1]['NATIONAL_MA_ENROLLED']
                
                nat_density = (nat_prov_count / latest_nat_enrl) * 100
                
                fig_gap.add_vline(x=nat_density, line_dash="dash", line_color="green", annotation_text=f"National Avg ({nat_density:.1f}) | Total Providers: {nat_prov_count:,.0f} | Total MA: {latest_nat_enrl:,.0f}", annotation_position="top right")
            except Exception as e:
                # st.warning(f"Could not load National Benchmarks: {e}")
                pass
        # -----------------------------------
        
        st.plotly_chart(fig_gap, use_container_width=True)

    # --- Page 6: Strategy Write-up ---
    if page == "Strategy Write-up":
        st.title("🧭 Strategy Write-up")

        st.markdown("""
        ## 1. Quality Control Steps for a New Analytics Request

        **1. Confirm understanding of the request**  
        First, I align with the requester to make sure we are solving the right problem. Specifically, I confirm:
        - What question they are trying to answer, and why it matters  
        - Why existing information is insufficient  
        - The preferred deliverable format (e.g., dashboard, table, slide, ad hoc analysis)  
        - Whether this is a one-off request or something likely to recur  
        - The expected delivery timeline (e.g., same day, one week)  
        - Expectations around feasibility and limitations  

        **2. Check for existing work**  
        I verify whether similar analyses already exist or if there is prior work I can build upon, avoiding unnecessary duplication.

        **3. Identify required data and stakeholders**  
        I determine which data sources are needed, SMEs that should be consulted, and what/if other teams should be involved.

        **4. Gather and assess the data**  
        If I am not already familiar with the data, I explore it to understand:
        - Data structure and completeness  
        - Overall quality and reliability  
        - Whether the data is sufficient to answer the request  
        - Any data cleaning or transformations needed before building the analysis

        **5. Build the analysis and format**  
        I build the analyses in whatever modality the customer is looking for adapting the information into an easily digestible format.
        
        **6. Gut-check and iterate**  
        I gut-check the results for reasonableness and consistency.

        **7. Validate results**  
        If possible, I leverage other analyses or SMEs to confirm the figures make sense and are logically sound.

        **8. Deliver and refinement**  
        Finally, I deliver the analysis, collect feedback, and iterate from there.


        ---

        ## 2. Actions of a VP of Data Analytics to Ensure a Productive and Efficient Team

        I view the most essential function of a VP of Data Analytics as deeply understanding both the needs of the business and the capabilities of the analytics organization, which stems frequent engagement with senior leadership and key stakeholders.

        This involves setting expectations in terms of timing and feasibility, as well as pushing back when certain analytics requests may be a poor use of resources. Then the VP can leverage their experience to help analytics and engineering set out a roadmap for accomplishing goals that can lead to the highest return for the business.
        
        Additionally, the VP of Data Analytics can help ensure proper cross collaboration between engineering and analytics to prevent duplicative work, ensure smooth production timelines, and circumvent any bottlenecks.
        
        Lastly, I think it is important to build team cohesion and culture, helping people feel motivated and giving them a north star to rally behind.

        ---

        ## 3. Hardest Lessons Learned as an Analyst

        **Early career lesson**  
        A quick, hard lesson at the beginning of my career is, I presented some results from an analysis where the numbers were simply 100x of what they should’ve been. I forgot to make the adjustment when putting the numbers in the table. This was a very embarrassing lesson. It taught me to walk away from an analysis once it is done, open it up again, and likely any obvious mistakes will be readily apparent. It also taught me to also gut check all numbers make logical sense. Thankfully I was just presenting to a manager and no one else, but I will never forget it.

        **Later career lesson**  
        A hard lesson later in my career is related to some analytics I was providing as part of a contract negotiation. It was a relatively large negotiation, where getting things right was extremely important. There was a mistake I made in some of the complex calculations that led to the reported percentage increase seem larger than it was. It was a mistake that was very difficult to see on the surface. What this taught me is to build in logic for automated checks as much as possible. Some mistakes can be hidden deep beneath the surface, but if you take the time to build out automated checks, you can bring those mistakes to the surface. Thankfully this situation worked out in the end, as the negotiation landed in a decent spot, but it could have been much worse.
        """)


if __name__ == "__main__":
    main()

