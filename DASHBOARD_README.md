# Load Test Results Dashboard

An interactive web-based dashboard for analyzing and visualizing load test results from your database. Built with Streamlit and Plotly for rich, interactive time series visualizations.

## Features

### 📊 Interactive Time Series Visualization
- **Time Series Charts**: View execution times, IOPS, bandwidth over time
- **Grouping Support**: Group by `test_result_id`, `setup_id`, `hostname`, `test_name`
- **Smart Aggregation**: Automatically averages data over unspecified grouping fields
- **Interactive Zooming**: Click and drag to zoom into specific time windows
- **Multiple Metrics**: Support for both load test results and FIO performance metrics

### 🎯 Key Capabilities
- **Flexible Filtering**: Filter by date range, setup IDs, hostnames, and test names
- **Real-time Data**: Connects directly to your PostgreSQL database
- **Performance Metrics**: 
  - Execution times and success rates
  - Read/Write IOPS
  - Read/Write Bandwidth (KB/s)
- **Summary Statistics**: Quick overview of test runs, success rates, and averages

## Quick Start

### Option 1: Demo Mode (No Database Required)
Get started immediately with sample data:

```bash
# Install dependencies
pip install -r dashboard_requirements.txt

# Run the demo dashboard
streamlit run demo_dashboard.py
```

The demo will generate realistic sample data and show you all the features of the dashboard.

### Option 2: Full Database Mode
Connect to your actual database:

1. **Install Dependencies**:
   ```bash
   pip install -r dashboard_requirements.txt
   ```

2. **Configure Database Access**:
   ```bash
   # Copy the template
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   
   # Edit with your database password
   nano .streamlit/secrets.toml
   ```

3. **Launch with Script**:
   ```bash
   ./launch_dashboard.sh
   ```

   Or manually:
   ```bash
   streamlit run dashboard.py
   ```

## Configuration

### Database Configuration
The dashboard reads database connection details from `config.json`:

```json
{
  "database": {
    "host": "your-postgres-host.com",
    "port": 5432,
    "database": "postgres",
    "user": "loadtest"
  }
}
```

### Secrets Configuration
Create `.streamlit/secrets.toml` with your database password:

```toml
[default]
db_password = "your_database_password_here"
```

## Database Schema Support

The dashboard expects the following tables (as defined in `database_schema.sql`):

### `load_test_results`
- `id` (SERIAL PRIMARY KEY)
- `setup_id` (VARCHAR) - Test setup identifier
- `hostname` (VARCHAR) - Host where test ran
- `test_name` (VARCHAR) - Name of the test
- `start_time` (TIMESTAMP) - When test started
- `execution_time_seconds` (DECIMAL) - How long test took
- `success` (BOOLEAN) - Whether test succeeded
- `error_message` (TEXT) - Error details if failed

### `fio_metrics` 
- `test_result_id` (INTEGER) - Reference to load_test_results
- `setup_id`, `hostname`, `test_name`, `start_time` - Same as above
- `read_iops`, `write_iops` (DECIMAL) - IOPS metrics
- `read_bw_kbps`, `write_bw_kbps` (DECIMAL) - Bandwidth metrics

## Usage Guide

### Grouping Logic
The dashboard implements intelligent grouping where:

- **Selected Fields**: Data is grouped by these dimensions
- **Unselected Fields**: Data is averaged across these dimensions
- **Time Series**: Always shows progression over time

**Example**: If you select "Group by Setup ID" and "Group by Test Name":
- Each line represents a unique (setup_id, test_name) combination
- Data from different hostnames and test_result_ids are averaged together
- You see how each setup performs for each test type over time

### Interactive Features

#### Chart Interactions
- **Zoom In**: Click and drag to select a time range
- **Pan**: Hold Shift and drag to move view
- **Reset Zoom**: Double-click on chart
- **Hover Details**: Hover over data points for exact values
- **Toggle Series**: Click legend items to show/hide data series

#### Filtering Options
- **Date Range**: Focus on specific time periods
- **Setup IDs**: Compare different test setups
- **Hostnames**: Analyze per-host performance
- **Test Names**: Focus on specific test types

### Use Cases

#### Performance Comparison
```
✓ Group by: Setup ID, Test Name  
✓ Filter: Select specific test types
→ Compare how different setups perform on same tests
```

#### Host Analysis
```
✓ Group by: Hostname, Test Name
✓ Filter: Select specific setup
→ Identify problematic hosts or performance variations
```

#### Test Trend Analysis
```
✓ Group by: Test Name only
✓ Filter: Recent date range
→ See overall performance trends for each test type
```

#### Detailed Investigation  
```
✓ Group by: Test Result ID
✓ Filter: Specific hostname + test
→ See individual test run performance over time
```

## File Structure

```
load-test/
├── dashboard.py                 # Main dashboard application
├── demo_dashboard.py           # Demo version with sample data
├── dashboard_requirements.txt   # Python dependencies
├── launch_dashboard.sh         # Launch script
├── config.json                 # Database configuration
├── database_schema.sql         # Database schema
└── .streamlit/
    └── secrets.toml.template   # Database password template
```

## Dependencies

- **streamlit**: Web framework for the dashboard
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive plotting library
- **psycopg2-binary**: PostgreSQL database adapter
- **python-dateutil**: Date parsing utilities

## Troubleshooting

### Database Connection Issues
1. Verify database credentials in `config.json` and `.streamlit/secrets.toml`
2. Check if database server is accessible from your machine
3. Ensure database has the required tables (run `database_schema.sql`)

### Performance Issues
1. Use date filters to limit data range for large datasets
2. Consider adding database indexes on frequently filtered columns
3. The dashboard caches data for 5 minutes to improve performance

### Chart Display Problems
1. Try refreshing the browser
2. Check browser console for JavaScript errors
3. Ensure all required Python packages are installed

### No Data Showing
1. Verify your database has test data
2. Check date range filters aren't too restrictive  
3. Ensure selected filters match data in database
4. Try the demo version to verify dashboard functionality

## Advanced Usage

### Custom Metrics
To add new metrics, modify the aggregation functions in `dashboard.py`:

```python
# Add your custom column to value_columns list
value_columns = ['execution_time_seconds', 'your_custom_metric']
```

### Additional Filtering
Add new filter dimensions by extending the sidebar controls and SQL query logic.

### Export Data
Use the "Show Raw Data" option to view and copy filtered datasets for external analysis.

## Contributing

When extending the dashboard:
1. Maintain the existing grouping logic
2. Add appropriate caching decorators for performance
3. Include error handling for database operations
4. Update this README with new features

## License

This dashboard is part of the load test analysis toolkit. Modify as needed for your specific use case.