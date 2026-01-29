#!/usr/bin/env python3
"""
Demo Load Test Dashboard with Sample Data

This is a demonstration version that works with sample data 
when the database is not available.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import random

# Configure page
st.set_page_config(
    page_title="Load Test Results Dashboard (Demo)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def generate_sample_data():
    """Generate sample data for demonstration"""
    np.random.seed(42)
    random.seed(42)

    # Sample configurations
    setup_ids = ["setup_hetzner_1", "setup_hetzner_2", "setup_nuvolos_1"]
    hostnames = ["test-host-01", "test-host-02", "test-host-03", "test-host-04"]
    test_names = [
        "fio_random_read_write",
        "clone_cnc_repo",
        "install_pandas",
        "load_pandas",
    ]

    # Generate load test data
    load_test_data = []
    fio_data = []

    base_time = datetime.now() - timedelta(days=7)

    for i in range(500):  # 500 test runs over 7 days
        time_offset = timedelta(minutes=random.randint(0, 7 * 24 * 60))
        timestamp = base_time + time_offset

        setup_id = random.choice(setup_ids)
        hostname = random.choice(hostnames)
        test_name = random.choice(test_names)

        # Simulate different performance characteristics
        base_time_multiplier = {
            "fio_random_read_write": 1.0,
            "clone_cnc_repo": 3.0,
            "install_pandas": 5.0,
            "load_pandas": 2.0,
        }

        exec_time = np.random.normal(
            base_time_multiplier[test_name] * 10, base_time_multiplier[test_name] * 2
        )
        exec_time = max(0.1, exec_time)  # Ensure positive time

        success = random.random() > 0.05  # 95% success rate

        load_test_data.append(
            {
                "test_result_id": i + 1,
                "setup_id": setup_id,
                "hostname": hostname,
                "test_name": test_name,
                "start_time": timestamp,
                "execution_time_seconds": round(exec_time, 3),
                "success": success,
                "error_message": None if success else "Sample error message",
                "created_at": timestamp,
            }
        )

        # Generate FIO metrics for FIO tests
        if test_name == "fio_random_read_write":
            # Simulate performance variations by setup
            setup_multiplier = {
                "setup_hetzner_1": 1.0,
                "setup_hetzner_2": 0.8,
                "setup_nuvolos_1": 1.2,
            }

            base_read_iops = 1000 * setup_multiplier[setup_id]
            base_write_iops = 800 * setup_multiplier[setup_id]

            fio_data.append(
                {
                    "test_result_id": i + 1,
                    "setup_id": setup_id,
                    "hostname": hostname,
                    "test_name": test_name,
                    "start_time": timestamp,
                    "read_iops": round(
                        np.random.normal(base_read_iops, base_read_iops * 0.1), 2
                    ),
                    "write_iops": round(
                        np.random.normal(base_write_iops, base_write_iops * 0.1), 2
                    ),
                    "read_bw_kbps": round(
                        np.random.normal(base_read_iops * 4, base_read_iops * 0.4), 2
                    ),
                    "write_bw_kbps": round(
                        np.random.normal(base_write_iops * 4, base_write_iops * 0.4), 2
                    ),
                    "created_at": timestamp,
                }
            )

    load_test_df = pd.DataFrame(load_test_data)
    fio_df = pd.DataFrame(fio_data)

    return load_test_df, fio_df


def aggregate_data(df, group_by_fields, time_column="start_time", value_columns=None):
    """Aggregate data by specified fields, averaging over unspecified fields"""
    if df is None or df.empty:
        return df

    # Convert start_time to datetime if it's not already
    df[time_column] = pd.to_datetime(df[time_column])

    # Determine grouping columns
    available_group_fields = ["test_result_id", "setup_id", "hostname", "test_name"]
    group_columns = [
        field
        for field in group_by_fields
        if field in available_group_fields and field in df.columns
    ]

    # Add time binning for better aggregation (hourly bins)
    df["time_bin"] = df[time_column].dt.floor("H")
    group_columns.append("time_bin")

    # Define value columns to aggregate
    if value_columns is None:
        value_columns = ["execution_time_seconds"]
        fio_columns = ["read_iops", "write_iops", "read_bw_kbps", "write_bw_kbps"]
        value_columns.extend([col for col in fio_columns if col in df.columns])

    value_columns = [col for col in value_columns if col in df.columns]

    if not value_columns:
        return df

    # Group and aggregate
    agg_dict = {col: "mean" for col in value_columns}
    if "success" in df.columns:
        agg_dict["success"] = "mean"

    try:
        grouped_df = df.groupby(group_columns).agg(agg_dict).reset_index()
        grouped_df["start_time"] = grouped_df["time_bin"]
        grouped_df = grouped_df.drop("time_bin", axis=1)
        return grouped_df.sort_values("start_time")
    except Exception as e:
        st.error(f"Error aggregating data: {e}")
        return df


def create_time_series_chart(df, metric_column, title, group_by_fields):
    """Create a time series chart for the specified metric"""
    if df is None or df.empty:
        st.warning("No data available for the chart")
        return None

    color_column = None
    if len(group_by_fields) > 0:
        for field in ["test_name", "hostname", "setup_id", "test_result_id"]:
            if field in group_by_fields and field in df.columns:
                color_column = field
                break

    try:
        if color_column:
            if color_column == "test_result_id":
                df[color_column] = df[color_column].astype(str)

            fig = px.line(
                df,
                x="start_time",
                y=metric_column,
                color=color_column,
                title=title,
                hover_data=group_by_fields,
            )
        else:
            fig = px.line(df, x="start_time", y=metric_column, title=title)

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title=metric_column.replace("_", " ").title(),
            hovermode="x unified",
        )

        return fig
    except Exception as e:
        st.error(f"Error creating chart: {e}")
        return None


def main():
    """Main dashboard application"""
    st.title("📊 Load Test Results Dashboard (Demo)")
    st.markdown(
        "**Demo Mode**: This dashboard is using sample data for demonstration purposes."
    )

    # Generate sample data
    with st.spinner("Generating sample data..."):
        load_test_df, fio_df = generate_sample_data()

    # Sidebar for filters
    st.sidebar.header("🔍 Filters")

    # Get unique values for filters
    setup_ids = sorted(load_test_df["setup_id"].unique().tolist())
    hostnames = sorted(load_test_df["hostname"].unique().tolist())
    test_names = sorted(load_test_df["test_name"].unique().tolist())

    # Date range filter
    min_date = load_test_df["start_time"].min().date()
    max_date = load_test_df["start_time"].max().date()

    date_col1, date_col2 = st.sidebar.columns(2)
    with date_col1:
        start_date = st.date_input(
            "Start Date", value=min_date, min_value=min_date, max_value=max_date
        )
    with date_col2:
        end_date = st.date_input(
            "End Date", value=max_date, min_value=min_date, max_value=max_date
        )

    # Grouping options
    st.sidebar.subheader("📊 Grouping Options")
    group_by_options = {
        "test_result_id": st.sidebar.checkbox("Group by Test Result ID", value=False),
        "setup_id": st.sidebar.checkbox("Group by Setup ID", value=True),
        "hostname": st.sidebar.checkbox("Group by Hostname", value=False),
        "test_name": st.sidebar.checkbox("Group by Test Name", value=True),
    }

    selected_groups = [
        field for field, selected in group_by_options.items() if selected
    ]

    # Filter options
    st.sidebar.subheader("🔽 Data Filters")
    selected_setups = st.sidebar.multiselect(
        "Setup IDs", options=setup_ids, default=setup_ids
    )
    selected_hosts = st.sidebar.multiselect(
        "Hostnames", options=hostnames, default=hostnames
    )
    selected_tests = st.sidebar.multiselect(
        "Test Names", options=test_names, default=test_names
    )

    # Data source selection
    st.sidebar.subheader("📈 Metrics to Display")
    show_load_tests = st.sidebar.checkbox("Load Test Results", value=True)
    show_fio_metrics = st.sidebar.checkbox("FIO Performance Metrics", value=True)

    # Apply filters
    filtered_load_df = load_test_df[
        (load_test_df["setup_id"].isin(selected_setups))
        & (load_test_df["hostname"].isin(selected_hosts))
        & (load_test_df["test_name"].isin(selected_tests))
        & (pd.to_datetime(load_test_df["start_time"]).dt.date >= start_date)
        & (pd.to_datetime(load_test_df["start_time"]).dt.date <= end_date)
    ]

    filtered_fio_df = fio_df[
        (fio_df["setup_id"].isin(selected_setups))
        & (fio_df["hostname"].isin(selected_hosts))
        & (fio_df["test_name"].isin(selected_tests))
        & (pd.to_datetime(fio_df["start_time"]).dt.date >= start_date)
        & (pd.to_datetime(fio_df["start_time"]).dt.date <= end_date)
    ]

    # Main content layout
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("📋 Summary")
        st.metric("Total Test Runs", len(filtered_load_df))
        success_rate = (
            (filtered_load_df["success"].mean() * 100)
            if not filtered_load_df.empty
            else 0
        )
        st.metric("Success Rate", f"{success_rate:.1f}%")

        if not filtered_load_df.empty:
            avg_time = filtered_load_df["execution_time_seconds"].mean()
            st.metric("Avg Execution Time", f"{avg_time:.2f}s")

        if not filtered_fio_df.empty:
            st.metric("FIO Test Runs", len(filtered_fio_df))
            avg_read_iops = filtered_fio_df["read_iops"].mean()
            st.metric("Avg Read IOPS", f"{avg_read_iops:.0f}")

    # Main charts area
    with col1:
        if show_load_tests and not filtered_load_df.empty:
            st.subheader("⏱️ Load Test Performance")

            # Aggregate data based on selected groupings
            agg_load_df = aggregate_data(filtered_load_df, selected_groups)

            if not agg_load_df.empty:
                # Execution time chart
                exec_time_chart = create_time_series_chart(
                    agg_load_df,
                    "execution_time_seconds",
                    "Execution Time Over Time (Hourly Average)",
                    selected_groups,
                )
                if exec_time_chart:
                    st.plotly_chart(exec_time_chart, use_container_width=True)

                # Success rate chart
                if "success" in agg_load_df.columns:
                    success_chart = create_time_series_chart(
                        agg_load_df,
                        "success",
                        "Success Rate Over Time",
                        selected_groups,
                    )
                    if success_chart:
                        st.plotly_chart(success_chart, use_container_width=True)

        if show_fio_metrics and not filtered_fio_df.empty:
            st.subheader("💾 FIO Performance Metrics")

            # Aggregate FIO data
            agg_fio_df = aggregate_data(
                filtered_fio_df,
                selected_groups,
                value_columns=[
                    "read_iops",
                    "write_iops",
                    "read_bw_kbps",
                    "write_bw_kbps",
                ],
            )

            if not agg_fio_df.empty:
                # IOPS charts
                fio_col1, fio_col2 = st.columns(2)

                with fio_col1:
                    read_iops_chart = create_time_series_chart(
                        agg_fio_df,
                        "read_iops",
                        "Read IOPS Over Time (Hourly Average)",
                        selected_groups,
                    )
                    if read_iops_chart:
                        st.plotly_chart(read_iops_chart, use_container_width=True)

                with fio_col2:
                    write_iops_chart = create_time_series_chart(
                        agg_fio_df,
                        "write_iops",
                        "Write IOPS Over Time (Hourly Average)",
                        selected_groups,
                    )
                    if write_iops_chart:
                        st.plotly_chart(write_iops_chart, use_container_width=True)

                # Bandwidth charts
                fio_bw_col1, fio_bw_col2 = st.columns(2)

                with fio_bw_col1:
                    read_bw_chart = create_time_series_chart(
                        agg_fio_df,
                        "read_bw_kbps",
                        "Read Bandwidth (KB/s) Over Time",
                        selected_groups,
                    )
                    if read_bw_chart:
                        st.plotly_chart(read_bw_chart, use_container_width=True)

                with fio_bw_col2:
                    write_bw_chart = create_time_series_chart(
                        agg_fio_df,
                        "write_bw_kbps",
                        "Write Bandwidth (KB/s) Over Time",
                        selected_groups,
                    )
                    if write_bw_chart:
                        st.plotly_chart(write_bw_chart, use_container_width=True)

    # Data tables section
    if st.sidebar.checkbox("Show Raw Data", value=False):
        st.subheader("📊 Raw Data")

        if show_load_tests and not filtered_load_df.empty:
            with st.expander("Load Test Results Data"):
                st.dataframe(filtered_load_df, use_container_width=True)

        if show_fio_metrics and not filtered_fio_df.empty:
            with st.expander("FIO Metrics Data"):
                st.dataframe(filtered_fio_df, use_container_width=True)

    # Help section
    with st.sidebar:
        st.markdown("---")
        st.subheader("ℹ️ Help")
        st.markdown(
            """
        **Demo Features:**
        - Sample data from 3 setups and 4 hosts
        - 7 days of test history
        - Interactive time series charts
        - Grouping and filtering
        
        **Grouping Logic:**
        - Select fields to group by
        - Unselected fields are averaged
        - Data is aggregated by hour
        
        **Interactive Features:**
        - Zoom: Click and drag on charts
        - Pan: Hold shift and drag
        - Reset: Double-click chart
        - Hover: View detailed values
        """
        )

        st.markdown("---")
        st.markdown(
            "💡 **Tip**: Try different grouping combinations to see how the data aggregates!"
        )


if __name__ == "__main__":
    main()
