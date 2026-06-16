import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================
# GOOGLE SHEET URL
# ==========================



import gspread
import streamlit as st

gc = gspread.service_account_from_dict(
    st.secrets["gcp_service_account"]
)

sheet = gc.open("Juniper Project File")

worksheet = sheet.worksheet("Sales Data Non-Air 2026")

data = worksheet.get_all_records()

df = pd.DataFrame(data)

df.columns = df.columns.str.strip()

df["Agency Type"] = (
    df["Agency Type"]
    .astype(str)
    .str.strip()
)

df["Agency Type"] = (
    df["Agency Type"]
    .replace("", "Unknown")
    .fillna("Unknown")
)

df["Branch Name"] = (
    df["Branch Name"]
    .astype(str)
    .str.strip()
)

# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title="Juniper Sales Dashboard",
    page_icon="📈",
    layout="wide"
)

# ==========================
# CLEAN DATA
# ==========================

df["Sale'26"] = pd.to_numeric(df["Sale'26"], errors="coerce")
df.rename(columns={"Sale'26": "Sale (€)"}, inplace=True)
df["Month Number"] = pd.to_numeric(df["Month Number"], errors="coerce")

# ==========================
# KPIs
# ==========================

df["Date Convert"] = pd.to_datetime(df["Date Convert"], errors="coerce")

# ==========================
# SIDEBAR FILTERS
# ==========================

st.sidebar.header("Filters")

selected_branch = st.sidebar.multiselect(
    "Branch",
    sorted(df["Branch Name"].dropna().unique())
)

month = st.sidebar.multiselect(
    "Month",
    options=sorted(df["Month Number"].dropna().unique()),
    default=sorted(df["Month Number"].dropna().unique())
)

print_mode = st.sidebar.checkbox("🖨️ Print Friendly Report")

agency_filter = st.session_state.get("agency_filter", "All")

filtered_df = df[
    df["Month Number"].isin(month)
]

if agency_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Agency Type"] == agency_filter
    ]

if selected_branch:
    filtered_df = filtered_df[
        filtered_df["Branch Name"].isin(selected_branch)
    ]

# KPI values from COMPLETE sheet

latest_date = df["Date Convert"].dt.date.max()

daily_sale = df.loc[
    df["Date Convert"].dt.date == latest_date,
    "Sale (€)"
].sum()

latest_month = df["Month Number"].max()

mtd_sale = df.loc[
    df["Month Number"] == latest_month,
    "Sale (€)"
].sum()

ytd_sale = df["Sale (€)"].sum()

bookings = len(df)

# ==========================
# HEADER
# ==========================

st.title("📈 Juniper Sales Dashboard")

st.markdown("""
<style>
.main .block-container {
    max-width: 95%;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.kpi-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.kpi-title {
    font-size: 16px;
    font-weight: 700;
    color: #555;
}
.kpi-value {
    font-size: 42px;
    font-weight: 800;
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Last Day Sale</div>
        <div class="kpi-value">€{daily_sale:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">MTD Sale</div>
        <div class="kpi-value">€{mtd_sale:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Sale</div>
        <div class="kpi-value">€{ytd_sale:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Bookings</div>
        <div class="kpi-value">{bookings:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# ==========================
# MONTHLY SALES TREND
# ==========================

st.markdown("## 📊 Monthly Sales Trend")

monthly_sale = (
    filtered_df.groupby("Month Number")["Sale (€)"]
    .sum()
    .reset_index()
    .sort_values("Month Number")
)

month_map = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}

monthly_sale["Month"] = monthly_sale["Month Number"].map(month_map)

fig = px.bar(
    monthly_sale,
    x="Month",
    y="Sale (€)",
    text="Sale (€)",
    title="Monthly Sales Trend"
)

fig.update_traces(
    texttemplate='€%{text:,.0f}',
    textposition='outside',
    textfont=dict(
        size=13,
        color='black',
        family='Arial Black'
    ),
    cliponaxis=False
)

fig.update_layout(
    template="plotly_white",
    height=420,
    margin=dict(l=40, r=40, t=60, b=40),
    bargap=0.35,
    font=dict(
        size=13,
        color="black"
    )
)

fig.update_layout(uniformtext_minsize=10, uniformtext_mode='hide')

fig.update_xaxes(
    automargin=True,
    fixedrange=True,
    tickfont=dict(
        size=14,
        color="black"
    )
)


fig.update_yaxes(
    fixedrange=True,
    tickfont=dict(
        size=13,
        color="black"
    ),
    range=[0, monthly_sale["Sale (€)"].max() * 1.20]
)



if print_mode:
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h")
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    
)

agency_sale = (
    df.groupby("Agency Type")["Sale (€)"]
    .sum()
    .reset_index()
)


# ===========================
# BRANCH SALE               #
# ==========================


#st.markdown("## 🏢 Branch Sale")

branch_sale = (
    filtered_df.groupby("Branch Name")["Sale (€)"]
    .sum()
    .reset_index()
    .sort_values("Sale (€)", ascending=False)
    .head(10)
)

fig_branch = px.bar(
    branch_sale,
    x="Branch Name",
    y="Sale (€)",
    text="Sale (€)",
    title="Top 10 Branches"
)

fig_branch.update_traces(
    texttemplate='€%{text:,.0f}',
    textposition='outside',
    textfont=dict(
        size=13,
        color='black',
        family='Arial Black'
    ),
    cliponaxis=False
)

fig_branch.update_layout(
    template="plotly_white",
    height=650,
    showlegend=False,
    margin=dict(l=40, r=40, t=40, b=40),
    bargap=0.25,
    font=dict(
        size=13,
        color="black"
    )
)

fig_branch.update_xaxes(
    tickfont=dict(
        size=13,
        color="black"
    )
)

fig_branch.update_yaxes(
    tickfont=dict(
        size=13,
        color="black"
    )
)

# ==========================
# BRANCH & AGENCY SALE
# ==========================

st.markdown("## 🧭 Branch & Agency Sale")



agency_filter = st.radio(
    "Agency Type",
    ["All", "B2B", "HQ"],
    horizontal=False,
    key="agency_filter"
)

fig_branch.update_layout(
    template="plotly_white",
    height=450,
    margin=dict(l=20, r=20, t=40, b=40)
)

st.plotly_chart(
    fig_branch,
    use_container_width=True
)


# ==========================
# DONUT CHART
# ==========================

total_agency_sale = ytd_sale

fig_agency = px.pie(
    agency_sale,
    names="Agency Type",
    values="Sale (€)",
    hole=0.65,
    color="Agency Type",
    color_discrete_map={
        "B2B": "#636EFA",
        "HQ": "#EF553B"
    }
)

fig_agency.update_traces(
    textinfo="percent",
    textfont_size=18,
    textfont_color="white",
    hovertemplate=
    "%{label}<br>" +
    "Sale: €%{value:,.0f}<br>" +
    "Share: %{percent}"
)

fig_agency.update_layout(
    template="plotly_white",
    height=450,
    showlegend=True,
    margin=dict(l=20, r=20, t=20, b=20),
    annotations=[
        dict(
            text=f"€{total_agency_sale:,.0f}",
            x=0.5,
            y=0.5,
            font_size=30,
            showarrow=False,
            font_color="#000000"
        )
    ]
)

b2b_sale = agency_sale.loc[
    agency_sale["Agency Type"] == "B2B",
    "Sale (€)"
].sum()

hq_sale = agency_sale.loc[
    agency_sale["Agency Type"] == "HQ",
    "Sale (€)"
].sum()

col1, col2 = st.columns([3,1])

with col1:
    st.plotly_chart(
        fig_agency,
        use_container_width=True
    )

with col2:
    st.metric(
        "🔵 B2B Sale",
        f"€{b2b_sale:,.0f}"
    )

    st.metric(
        "🔴 HQ Sale",
        f"€{hq_sale:,.0f}"
    )

# ==========================
# TOP 10 SUPPLIERS
# ==========================

st.markdown("## 🏆 Top 10 Suppliers")

supplier_sale = (
    filtered_df.groupby("Supplier Name")["Sale (€)"]
    .sum()
    .reset_index()
    .sort_values("Sale (€)", ascending=False)
    .head(10)
)

fig_supplier = px.bar(
    supplier_sale,
    x="Supplier Name",
    y="Sale (€)",
    text="Sale (€)",
    title="Top 10 Suppliers"
)

fig_supplier.update_traces(
    texttemplate='€%{text:,.0f}',
    textposition='outside',
    textfont=dict(
        size=13,
        color='black',
        family='Arial Black'
    ),
    cliponaxis=False
)

fig_supplier.update_layout(
    template="plotly_white",
    height=500,
    showlegend=False,
    margin=dict(l=40, r=40, t=40, b=80),
    bargap=0.25,
    font=dict(
        size=13,
        color="black"
    )
)

fig_supplier.update_xaxes(
    tickangle=-20,
    tickfont=dict(
        size=14,
        color="black"
    )
)

fig_supplier.update_yaxes(
    title="Sale (€)"
)

st.plotly_chart(
    fig_supplier,
    use_container_width=True
)


# ==========================
# TOP 10 DESTINATIONS
# ==========================

st.markdown("## 🌍 Top 10 Destinations")

destination_sale = (
    filtered_df.groupby("Product's Country")["Sale (€)"]
    .sum()
    .reset_index()
    .sort_values("Sale (€)", ascending=False)
    .head(10)
)

fig_destination = px.bar(
    destination_sale,
    x="Product's Country",
    y="Sale (€)",
    text="Sale (€)",
    title="Top 10 Destinations"
)

fig_destination.update_traces(
    texttemplate='€%{text:,.0f}',
    textposition='outside',
    textfont=dict(
        size=13,
        color='black',
        family='Arial Black'
    ),
    cliponaxis=False
)

fig_destination.update_layout(
    template="plotly_white",
    height=500,
    showlegend=False,
    margin=dict(l=40, r=40, t=40, b=80),
    bargap=0.25,
    font=dict(
        size=13,
        color="black"
    )
)

fig_destination.update_xaxes(
    tickangle=-20,
    tickfont=dict(
        size=13,
        color="black"
    )
)

fig_destination.update_yaxes(
    title="Sale (€)",
    range=[
        0,
        destination_sale["Sale (€)"].max() * 1.20
    ]
)

st.plotly_chart(
    fig_destination,
    use_container_width=True
)

st.markdown("##### 🌍 Destination Filter")

destination_list = sorted(
    filtered_df["Product's Country"]
    .dropna()
    .unique()
)

selected_destination = st.selectbox(
    "",
    ["All Destinations"] + destination_list,
    key="destination_filter"
)


#####

destination_df = filtered_df.copy()

if selected_destination != "All Destinations":
    destination_df = destination_df[
        destination_df["Product's Country"]
        == selected_destination
    ]


destination_df["Room Nights"] = (
    destination_df["No. of nights"]
    * destination_df["No. of Rooms"]
)



# ==========================
# TOP HOTELS BY TOTAL ROOM NIGHTS
# ==========================

st.markdown("## 🏨 Top 10 Hotels by Total Room Nights")

# Calculate Room Nights
filtered_df["Room Nights"] = (
    pd.to_numeric(
        filtered_df["No. of nights"],
        errors="coerce"
    ).fillna(0)
    *
    pd.to_numeric(
        filtered_df["No. of Rooms"],
        errors="coerce"
    ).fillna(0)
)

hotel_sale = (
    destination_df[
        destination_df["Description"].notna()
    ]
    .groupby("Description")["Room Nights"]
    .sum()
    .reset_index()
    .sort_values("Room Nights", ascending=False)
    .head(10)
)

fig_hotel = px.bar(
    hotel_sale,
    x="Description",
    y="Room Nights",
    text="Room Nights",
    title="Top 10 Hotels by Total Room Nights"
)

fig_hotel.update_traces(
    texttemplate='%{text:,.0f}',
    textposition='outside',
    textfont=dict(
        size=13,
        color='black',
        family='Arial Black'
    ),
    cliponaxis=False
)

fig_hotel.update_layout(
    template="plotly_white",
    height=600,
    showlegend=False,
    margin=dict(
        l=40,
        r=40,
        t=40,
        b=180
    ),
    bargap=0.25,
    font=dict(
        size=13,
        color="black"
    )
)

fig_hotel.update_xaxes(
    tickangle=-45,
    tickfont=dict(
        size=11,
        color="black"
    )
)

fig_hotel.update_yaxes(
    title="Total Room Nights",
    range=[
        0,
        hotel_sale["Room Nights"].max() * 1.20
    ]
)

st.plotly_chart(
    fig_hotel,
    use_container_width=True
)


# ==========================
# BRANCH WISE DETAIL
# ==========================

st.markdown("## 📋 Branch Wise Detail")

branch_table = (
    filtered_df.groupby("Branch Name")["Sale (€)"]
    .sum()
    .reset_index()
    .sort_values(
        by="Sale (€)",
        ascending=False
    )
)

branch_table["Sale (€)"] = (
    branch_table["Sale (€)"]
    .apply(lambda x: f"€{x:,.0f}")
)

csv = branch_table.to_csv(index=False)

col1, col2 = st.columns([4, 1])

with col1:
    search_branch = st.text_input(
        "🔍 Search Branch",
        placeholder="STTS MCT"
    )

with col2:
    st.download_button(
        "📥 Download",
        csv,
        "branch_report.csv",
        "text/csv"
    )

if search_branch:
    search_result = branch_table[
        branch_table["Branch Name"]
        .str.contains(search_branch, case=False, na=False)
    ]

    if not search_result.empty:
        st.success(f"Found {len(search_result)} branch(es)")
        st.dataframe(
            search_result,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("Branch not found")

st.dataframe(
    branch_table,
    use_container_width=True,
    hide_index=True
)