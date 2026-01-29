#!/usr/bin/env python3
"""
Interactive Dashboard for Load Test Results Analysis

This dashboard allows you to visualize and analyze load test results stored in the database.
Features:
- Time series visualization
- Grouping by test_result_id, setup_id, hostname, test_name
- Averaging over unspecified fields
- Interactive time window zooming
- Multiple metrics visualization (execution time, IOPS, bandwidth)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
import json
from datetime import datetime, timedelta
import logging
import sys
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
# Configure page
st.set_page_config(
    page_title="Load Test Results Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_config():
    """Load configuration from config.json"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return None


@st.cache_data(ttl=60)  # Cache connection parameters for 1 minute
def get_database_config():
    """Get database configuration and password"""
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return None

    try:
        db_config = config["database"]
        password = ""

        # 1. Try session state (for manual input)
        if hasattr(st.session_state, "db_password") and st.session_state.db_password:
            password = st.session_state.db_password
            logger.info("Using password from session state")

        # 2. Try Streamlit secrets
        elif "default" in st.secrets and "db_password" in st.secrets["default"]:
            password = st.secrets["default"]["db_password"]
            logger.info("Using password from Streamlit secrets")

        # 3. Try environment variable
        else:
            password = os.environ.get("DB_PASSWORD", "")
            if password:
                logger.info("Using password from environment variable")

        if not password:
            logger.warning("No database password found")
            return None

        return {
            "host": db_config["host"],
            "port": db_config["port"],
            "database": db_config["database"],
            "user": db_config["user"],
            "password": password,
        }
    except Exception as e:
        logger.error(f"Error getting database config: {e}")
        return None


@contextmanager
def get_database_connection():
    """Context manager for database connections"""
    db_config = get_database_config()
    if not db_config:
        yield None
        return

    conn = None
    try:
        logger.info(
            f"Connecting to database at {db_config['host']}:{db_config['port']}"
        )
        conn = psycopg2.connect(**db_config)
        logger.info("Database connection established successfully")
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        st.error(f"Database connection error: {e}")
        yield None
    finally:
        if conn:
            try:
                conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")


def test_database_connection():
    """Test if database connection is working"""
    with get_database_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                logger.info("Database connection test successful")
                return True
            except Exception as e:
                logger.error(f"Database connection test failed: {e}")
                return False
        return False


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_load_test_data(
    setup_ids=None, hostnames=None, test_names=None, start_date=None, end_date=None
):
    """Fetch load test results data with optional filters"""
    logger.info(
        f"Fetching load test data with filters: setup_ids={setup_ids}, hostnames={hostnames}, test_names={test_names}"
    )

    with get_database_connection() as conn:
        if not conn:
            logger.error("No database connection available for fetch_load_test_data")
            return None

        # Base query
        query = """
        SELECT 
            id as test_result_id,
            setup_id,
            hostname,
            test_name,
            start_time,
            execution_time_seconds,
            success,
            error_message,
            created_at
        FROM load_test_results
        WHERE 1=1
        """

        params = []

        # Add filters
        if setup_ids:
            placeholders = ",".join(["%s"] * len(setup_ids))
            query += f" AND setup_id IN ({placeholders})"
            params.extend(setup_ids)

        if hostnames:
            placeholders = ",".join(["%s"] * len(hostnames))
            query += f" AND hostname IN ({placeholders})"
            params.extend(hostnames)

        if test_names:
            placeholders = ",".join(["%s"] * len(test_names))
            query += f" AND test_name IN ({placeholders})"
            params.extend(test_names)

        if start_date:
            query += " AND start_time >= %s"
            params.append(start_date)

        if end_date:
            query += " AND start_time <= %s"
            params.append(end_date)

        query += " ORDER BY start_time DESC"

        try:
            logger.info(f"Executing query with {len(params)} parameters")
            df = pd.read_sql_query(query, conn, params=params)
            logger.info(f"Successfully fetched {len(df)} load test records")
            return df
        except Exception as e:
            logger.error(f"Error fetching load test data: {e}")
            st.error(f"Error fetching data: {e}")
            return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_fio_metrics_data(
    setup_ids=None, hostnames=None, test_names=None, start_date=None, end_date=None
):
    """Fetch FIO metrics data with optional filters"""
    logger.info(
        f"Fetching FIO metrics data with filters: setup_ids={setup_ids}, hostnames={hostnames}, test_names={test_names}"
    )

    with get_database_connection() as conn:
        if not conn:
            logger.error("No database connection available for fetch_fio_metrics_data")
            return None

        # Base query
        query = """
        SELECT 
            test_result_id,
            setup_id,
            hostname,
            test_name,
            start_time,
            read_iops,
            write_iops,
            read_bw_kbps,
            write_bw_kbps,
            created_at
        FROM fio_metrics
        WHERE 1=1
        """

        params = []

        # Add filters (same logic as above)
        if setup_ids:
            placeholders = ",".join(["%s"] * len(setup_ids))
            query += f" AND setup_id IN ({placeholders})"
            params.extend(setup_ids)

        if hostnames:
            placeholders = ",".join(["%s"] * len(hostnames))
            query += f" AND hostname IN ({placeholders})"
            params.extend(hostnames)

        if test_names:
            placeholders = ",".join(["%s"] * len(test_names))
            query += f" AND test_name IN ({placeholders})"
            params.extend(test_names)

        if start_date:
            query += " AND start_time >= %s"
            params.append(start_date)

        if end_date:
            query += " AND start_time <= %s"
            params.append(end_date)

        query += " ORDER BY start_time DESC"

        try:
            logger.info(f"Executing FIO metrics query with {len(params)} parameters")
            df = pd.read_sql_query(query, conn, params=params)
            logger.info(f"Successfully fetched {len(df)} FIO metrics records")
            return df
        except Exception as e:
            logger.error(f"Error fetching FIO data: {e}")
            st.error(f"Error fetching FIO data: {e}")
            return None


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_filter_options():
    """Get available filter options from the database"""
    logger.info("Fetching filter options from database")

    with get_database_connection() as conn:
        if not conn:
            logger.error("No database connection available for get_filter_options")
            return [], [], [], {}

        try:
            # Get unique values for filters
            setup_ids_query = (
                "SELECT DISTINCT setup_id FROM load_test_results ORDER BY setup_id"
            )
            hostnames_query = (
                "SELECT DISTINCT hostname FROM load_test_results ORDER BY hostname"
            )
            test_names_query = (
                "SELECT DISTINCT test_name FROM load_test_results ORDER BY test_name"
            )

            logger.info("Fetching setup IDs, hostnames, and test names")
            setup_ids = pd.read_sql_query(setup_ids_query, conn)["setup_id"].tolist()
            hostnames = pd.read_sql_query(hostnames_query, conn)["hostname"].tolist()
            test_names = pd.read_sql_query(test_names_query, conn)["test_name"].tolist()

            # Get date range
            logger.info("Fetching date range")
            date_range_query = "SELECT MIN(start_time) as min_date, MAX(start_time) as max_date FROM load_test_results"
            date_range = pd.read_sql_query(date_range_query, conn)

            logger.info(
                f"Successfully fetched filter options: {len(setup_ids)} setups, {len(hostnames)} hosts, {len(test_names)} tests"
            )
            return (
                setup_ids,
                hostnames,
                test_names,
                date_range.iloc[0] if not date_range.empty else {},
            )

        except Exception as e:
            logger.error(f"Error fetching filter options: {e}")
            st.error(f"Error fetching filter options: {e}")
            return [], [], [], {}


def aggregate_data(df, group_by_fields, time_column="start_time", value_columns=None):
    """Aggregate data by specified fields, averaging over unspecified fields"""
    if df is None or df.empty:
        return df

    # Convert start_time to datetime if it's not already
    if time_column in df.columns:
        df[time_column] = pd.to_datetime(df[time_column])

    # Determine grouping columns
    available_group_fields = ["test_result_id", "setup_id", "hostname", "test_name"]
    group_columns = [
        field
        for field in group_by_fields
        if field in available_group_fields and field in df.columns
    ]

    # Add time column for time series
    group_columns.append(time_column)

    # Define value columns to aggregate
    if value_columns is None:
        value_columns = ["execution_time_seconds"]
        # Add FIO metrics if they exist in the dataframe
        fio_columns = ["read_iops", "write_iops", "read_bw_kbps", "write_bw_kbps"]
        value_columns.extend([col for col in fio_columns if col in df.columns])

    # Remove any value columns that don't exist in the dataframe
    value_columns = [col for col in value_columns if col in df.columns]

    if not value_columns:
        return df

    # Group and aggregate
    agg_dict = {col: "mean" for col in value_columns}
    agg_dict["success"] = "mean"  # Success rate

    try:
        grouped_df = df.groupby(group_columns).agg(agg_dict).reset_index()
        return grouped_df
    except Exception as e:
        st.error(f"Error aggregating data: {e}")
        return df


def create_time_series_chart(df, metric_column, title, group_by_fields):
    """Create a time series chart for the specified metric"""
    if df is None or df.empty:
        st.warning("No data available for the chart")
        return None

    # Create color mapping based on grouping
    color_column = None
    if "test_name" in group_by_fields and "test_name" in df.columns:
        color_column = "test_name"
    elif "hostname" in group_by_fields and "hostname" in df.columns:
        color_column = "hostname"
    elif "setup_id" in group_by_fields and "setup_id" in df.columns:
        color_column = "setup_id"
    elif "test_result_id" in group_by_fields and "test_result_id" in df.columns:
        color_column = "test_result_id"

    try:
        if color_column:
            # Convert test_result_id to string if it's used as color
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
    st.title("📊 Load Test Results Dashboard")
    st.markdown(
        "Analyze and visualize your load test results with interactive time series charts."
    )

    # Check database connection
    logger.info("Starting dashboard application")
    if not test_database_connection():
        logger.warning("Database connection test failed, showing password input")
        st.warning("Database connection failed. Please provide the database password.")

        # Show password input in the main area
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("Database Connection Required")
            manual_password = st.text_input(
                "Database Password",
                type="password",
                help="Enter your database password to connect",
            )

            if st.button("Connect to Database"):
                if manual_password:
                    # Store password in session state and clear cache
                    st.session_state.db_password = manual_password
                    get_database_config.clear()
                    logger.info("Testing connection with manually entered password")

                    # Test connection
                    if test_database_connection():
                        st.success("✅ Connected successfully!")
                        logger.info("Manual connection test successful")
                        st.rerun()  # Refresh the app
                    else:
                        st.error("❌ Connection failed. Please check your password.")
                        logger.error("Manual connection test failed")
                        if hasattr(st.session_state, "db_password"):
                            del st.session_state.db_password
                else:
                    st.error("Please enter a password.")

        st.info(
            """
        **Alternative Setup Options:**
        1. Set password in `.streamlit/secrets.toml` file under `[default]` section
        2. Set `DB_PASSWORD` environment variable
        3. Use the password input above
        """
        )
        st.stop()

    logger.info("Database connection successful, loading dashboard")

    # Sidebar for filters
    st.sidebar.header("🔍 Filters")

    # Get filter options
    with st.spinner("Loading filter options..."):
        setup_ids, hostnames, test_names, date_range = get_filter_options()

    if not setup_ids and not hostnames and not test_names:
        st.error("No data found in database or connection issue")
        st.stop()

    # Date range filter
    if len(date_range) > 0 and not date_range.isna().all():
        min_date = pd.to_datetime(date_range.get("min_date")).date()
        max_date = pd.to_datetime(date_range.get("max_date")).date()

        date_col1, date_col2 = st.sidebar.columns(2)
        with date_col1:
            start_date = st.date_input(
                "Start Date", value=min_date, min_value=min_date, max_value=max_date
            )
        with date_col2:
            end_date = st.date_input(
                "End Date", value=max_date, min_value=min_date, max_value=max_date
            )
    else:
        start_date = end_date = None

    # Grouping options
    st.sidebar.subheader("📊 Grouping Options")
    group_by_options = {
        "test_result_id": st.sidebar.checkbox("Group by Test Result ID", value=False),
        "setup_id": st.sidebar.checkbox("Group by Setup ID", value=True),
        "hostname": st.sidebar.checkbox("Group by Hostname", value=True),
        "test_name": st.sidebar.checkbox("Group by Test Name", value=True),
    }

    selected_groups = [
        field for field, selected in group_by_options.items() if selected
    ]

    # Filter options
    st.sidebar.subheader("🔽 Data Filters")

    selected_setups = st.sidebar.multiselect("Setup IDs", options=setup_ids, default=[])
    selected_hosts = st.sidebar.multiselect("Hostnames", options=hostnames, default=[])
    selected_tests = st.sidebar.multiselect(
        "Test Names", options=test_names, default=[]
    )

    # Data source selection
    st.sidebar.subheader("📈 Metrics to Display")
    show_load_tests = st.sidebar.checkbox("Load Test Results", value=True)
    show_fio_metrics = st.sidebar.checkbox("FIO Performance Metrics", value=True)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("📋 Summary")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()

    # Fetch and display data
    with st.spinner("Loading data..."):
        load_test_df = None
        fio_df = None

        if show_load_tests:
            load_test_df = fetch_load_test_data(
                setup_ids=selected_setups if selected_setups else None,
                hostnames=selected_hosts if selected_hosts else None,
                test_names=selected_tests if selected_tests else None,
                start_date=start_date,
                end_date=end_date,
            )

        if show_fio_metrics:
            fio_df = fetch_fio_metrics_data(
                setup_ids=selected_setups if selected_setups else None,
                hostnames=selected_hosts if selected_hosts else None,
                test_names=selected_tests if selected_tests else None,
                start_date=start_date,
                end_date=end_date,
            )

    # Display summary statistics
    with col2:
        if load_test_df is not None and not load_test_df.empty:
            st.metric("Total Test Runs", len(load_test_df))
            success_rate = (
                (load_test_df["success"].mean() * 100)
                if "success" in load_test_df.columns
                else 0
            )
            st.metric("Success Rate", f"{success_rate:.1f}%")

            if "execution_time_seconds" in load_test_df.columns:
                avg_time = load_test_df["execution_time_seconds"].mean()
                st.metric("Avg Execution Time", f"{avg_time:.2f}s")

        if fio_df is not None and not fio_df.empty:
            st.metric("FIO Test Runs", len(fio_df))
            if "read_iops" in fio_df.columns:
                avg_read_iops = fio_df["read_iops"].mean()
                st.metric("Avg Read IOPS", f"{avg_read_iops:.0f}")

    # Main charts area
    with col1:
        if load_test_df is not None and not load_test_df.empty and show_load_tests:
            st.subheader("⏱️ Load Test Performance")

            # Aggregate data based on selected groupings
            agg_load_df = aggregate_data(load_test_df, selected_groups)

            if agg_load_df is not None and not agg_load_df.empty:
                # Execution time chart
                exec_time_chart = create_time_series_chart(
                    agg_load_df,
                    "execution_time_seconds",
                    "Execution Time Over Time",
                    selected_groups,
                )
                if exec_time_chart:
                    st.plotly_chart(exec_time_chart, use_container_width=True)

                # Success rate chart if data is grouped
                if "success" in agg_load_df.columns:
                    success_chart = create_time_series_chart(
                        agg_load_df,
                        "success",
                        "Success Rate Over Time",
                        selected_groups,
                    )
                    if success_chart:
                        st.plotly_chart(success_chart, use_container_width=True)

        if fio_df is not None and not fio_df.empty and show_fio_metrics:
            st.subheader("💾 FIO Performance Metrics")

            # Aggregate FIO data
            agg_fio_df = aggregate_data(
                fio_df,
                selected_groups,
                value_columns=[
                    "read_iops",
                    "write_iops",
                    "read_bw_kbps",
                    "write_bw_kbps",
                ],
            )

            if agg_fio_df is not None and not agg_fio_df.empty:
                # IOPS charts
                fio_col1, fio_col2 = st.columns(2)

                with fio_col1:
                    if "read_iops" in agg_fio_df.columns:
                        read_iops_chart = create_time_series_chart(
                            agg_fio_df,
                            "read_iops",
                            "Read IOPS Over Time",
                            selected_groups,
                        )
                        if read_iops_chart:
                            st.plotly_chart(read_iops_chart, use_container_width=True)

                with fio_col2:
                    if "write_iops" in agg_fio_df.columns:
                        write_iops_chart = create_time_series_chart(
                            agg_fio_df,
                            "write_iops",
                            "Write IOPS Over Time",
                            selected_groups,
                        )
                        if write_iops_chart:
                            st.plotly_chart(write_iops_chart, use_container_width=True)

                # Bandwidth charts
                fio_bw_col1, fio_bw_col2 = st.columns(2)

                with fio_bw_col1:
                    if "read_bw_kbps" in agg_fio_df.columns:
                        read_bw_chart = create_time_series_chart(
                            agg_fio_df,
                            "read_bw_kbps",
                            "Read Bandwidth (KB/s) Over Time",
                            selected_groups,
                        )
                        if read_bw_chart:
                            st.plotly_chart(read_bw_chart, use_container_width=True)

                with fio_bw_col2:
                    if "write_bw_kbps" in agg_fio_df.columns:
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

        if load_test_df is not None and not load_test_df.empty and show_load_tests:
            with st.expander("Load Test Results Data"):
                st.dataframe(load_test_df, use_container_width=True)

        if fio_df is not None and not fio_df.empty and show_fio_metrics:
            with st.expander("FIO Metrics Data"):
                st.dataframe(fio_df, use_container_width=True)

    # Help section
    with st.sidebar:
        st.markdown("---")
        st.subheader("ℹ️ Help")
        st.markdown(
            """
        **Grouping Logic:**
        - Select fields to group by
        - Unselected fields are averaged
        - Time series shows trends over time
        
        **Interactive Features:**
        - Zoom: Click and drag on charts
        - Pan: Hold shift and drag
        - Reset: Double-click chart
        - Hover: View detailed values
        """
        )


if __name__ == "__main__":
    main()
