# Filesystem Load Testing Tool

A Python script designed to perform specific filesystem workload tests to mimic real-world operations and measure their performance over time. Unlike standard I/O throughput tools, this focuses on realistic workflow patterns.

## Features

- **Configurable Test Cases**: Currently supports git repository cloning and Python virtual environment creation
- **Continuous Monitoring**: Infinite loop execution with configurable intervals
- **PostgreSQL Logging**: Comprehensive metrics storage with timestamps and execution times
- **Flexible Configuration**: JSON-based configuration for all aspects of testing
- **Robust Error Handling**: Automatic cleanup and error recovery

## Quick Start

### Prerequisites

- Python 3.7+
- PostgreSQL database
- Git (for repository cloning tests)
- Virtual environment support (`python -m venv`)

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL database:
   ```bash
   # Connect to PostgreSQL as superuser and run:
   psql -U postgres -f database_schema.sql
   ```

4. Configure the application:
   ```bash
   cp config.json config.json.local
   # Edit config.json.local with your settings
   ```

### Configuration

Edit `config.json` to customize the testing parameters:

```json
{
  "setup_id": "production_server_1",
  "target_path": "/path/to/test/directory",
  "loop_interval_seconds": 300,
  "log_level": "INFO",
  "log_file": "filesystem_load_test.log",
  "enabled_tests": ["git_clone", "virtualenv_install"],
  "tests": {
    "git_clone": {
      "repository_url": "https://github.com/octocat/Hello-World.git"
    },
    "virtualenv_install": {
      "packages": ["pandas"]
    }
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "load_test_db",
    "user": "load_test_user"
  }
}
```

### Usage

Run the load testing script:

```bash
# Using default config.json
python filesystem_load_test.py

# Using custom configuration file
python filesystem_load_test.py --config my_config.json
```

The script will run continuously until interrupted with Ctrl+C.

## Test Cases

### Git Clone Test (`git_clone`)

- Clones a specified repository to a subdirectory in the target path
- Measures time from clone start to completion
- Automatically cleans up the cloned repository after measurement
- Tests filesystem write performance and directory creation

### Virtual Environment Test (`virtualenv_install`)

- Creates a Python virtual environment in the target path
- Installs specified packages (default: pandas)
- Measures time from venv creation through package installation
- Tests filesystem operations, Python package management, and dependency resolution
- Automatically cleans up the virtual environment after measurement


### Pandas Load Test (`pandas_load`)

- **One-time setup**: Creates a persistent virtual environment with pandas installed
- **Per-iteration test**: Measures pandas import time in fresh Python processes
- Tests filesystem scan performance (pandas scans thousands of files on import)
- Setup phase runs only once when the script starts
- Virtual environment persists between test cycles (no cleanup)
- Each test iteration spawns a new Python process for "cold start" measurement

## Database Schema

Test results are stored in PostgreSQL with the following structure:

```sql
CREATE TABLE load_test_results (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    execution_time_seconds DECIMAL(10, 3) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Analyzing Results

Use the provided SQL queries in `database_schema.sql` to analyze performance:

```sql
-- Average execution times by test type
SELECT 
    test_name,
    COUNT(*) as total_runs,
    AVG(execution_time_seconds) as avg_time,
    MIN(execution_time_seconds) as min_time,
    MAX(execution_time_seconds) as max_time
FROM load_test_results 
WHERE success = true 
GROUP BY test_name;

-- Recent test results
SELECT * FROM load_test_results 
ORDER BY start_time DESC 
LIMIT 50;
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `target_path` | Directory where test operations are performed | `/tmp/load_test_workspace` |
| `loop_interval_seconds` | Seconds between test iterations | `300` |
| `log_level` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `log_file` | Path to log file | `filesystem_load_test.log` |
| `enabled_tests` | List of test case names to run | `[\"clone_hello_world\", \"install_pandas\"]` |\n| `setup_id` | Identifier for this test setup | `\"production_server_1\"` |

## Extending the Tool

The tool supports multiple test instances of the same type through the flexible `test_definitions` structure.

### Adding New Test Instances

To add new test cases, add them to the `test_definitions` section in `config.json`:

```json
"test_definitions": {
  "clone_my_repo": {
    "type": "git_clone",
    "repository_url": "https://github.com/myuser/myrepo.git",
    "description": "Clone my custom repository"
  },
  "install_data_science": {
    "type": "virtualenv_install",
    "packages": ["pandas", "numpy", "matplotlib"],
    "description": "Install data science stack"
  }
}
```

Then add the test names to `enabled_tests`:
```json
"enabled_tests": ["clone_my_repo", "install_data_science"]
```

### Adding New Test Types

To create entirely new test types:

1. Add a new test method in `FilesystemLoadTester`:
   ```python
   def test_my_new_type(self, test_config: Dict[str, Any]) -> float:
       start_time = time.time()
       # Implement your test logic here
       # Use test_config to get parameters
       return time.time() - start_time
   ```

2. Add the new type to the `execute_test_case` method dispatcher:
   ```python
   elif test_type == "my_new_type":
       execution_time = self.test_my_new_type(test_config)
   ```

3. Define test instances in `config.json`:
   ```json
   "my_test_instance": {
     "type": "my_new_type",
     "custom_parameter": "value"
   }
   ```
## Security Considerations

- Ensure the target path has appropriate permissions
- Use secure database credentials
- Consider network security for remote repository access
- Monitor disk space usage in the target path

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL service status
   - Verify database credentials in config
   - Ensure database and user exist

2. **Permission Denied on Target Path**
   - Verify write permissions on target directory
   - Check filesystem mount options
   - Ensure sufficient disk space

3. **Git Clone Failures**
   - Verify network connectivity
   - Check if repository URL is accessible
   - Ensure git is installed and in PATH

4. **Virtual Environment Creation Fails**
   - Verify Python installation
   - Check if `python -m venv` works manually
   - Ensure sufficient disk space

### Logs

Check the log file (default: `filesystem_load_test.log`) for detailed error information and execution traces.