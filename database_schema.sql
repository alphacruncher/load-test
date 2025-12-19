-- Database schema for filesystem load testing results
-- Run this script to create the necessary database and table

-- Create database (run as superuser)
-- CREATE DATABASE load_test_db;
-- CREATE USER load_test_user WITH PASSWORD 'your_password_here';
-- GRANT ALL PRIVILEGES ON DATABASE load_test_db TO load_test_user;

-- Connect to load_test_db and run the following:

-- Create the table for storing test results
CREATE TABLE IF NOT EXISTS load_test_results (
    id SERIAL PRIMARY KEY,
    setup_id VARCHAR(100) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    execution_time_seconds DECIMAL(10, 3) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_load_test_results_setup_id ON load_test_results(setup_id);
CREATE INDEX IF NOT EXISTS idx_load_test_results_hostname ON load_test_results(hostname);
CREATE INDEX IF NOT EXISTS idx_load_test_results_test_name ON load_test_results(test_name);
CREATE INDEX IF NOT EXISTS idx_load_test_results_start_time ON load_test_results(start_time);
CREATE INDEX IF NOT EXISTS idx_load_test_results_success ON load_test_results(success);

-- Create the table for storing FIO test metrics
CREATE TABLE IF NOT EXISTS fio_metrics (
    id SERIAL PRIMARY KEY,
    test_result_id INTEGER REFERENCES load_test_results(id) ON DELETE CASCADE,
    setup_id VARCHAR(100) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    read_iops DECIMAL(15, 2),
    write_iops DECIMAL(15, 2),
    read_bw_kbps DECIMAL(15, 2),
    write_bw_kbps DECIMAL(15, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for FIO metrics table
CREATE INDEX IF NOT EXISTS idx_fio_metrics_test_result_id ON fio_metrics(test_result_id);
CREATE INDEX IF NOT EXISTS idx_fio_metrics_setup_id ON fio_metrics(setup_id);
CREATE INDEX IF NOT EXISTS idx_fio_metrics_hostname ON fio_metrics(hostname);
CREATE INDEX IF NOT EXISTS idx_fio_metrics_test_name ON fio_metrics(test_name);
CREATE INDEX IF NOT EXISTS idx_fio_metrics_start_time ON fio_metrics(start_time);

-- Example queries for analyzing results:

-- Get average execution times by setup, hostname, and test type
-- SELECT
--     setup_id,
--     hostname,
--     test_name,
--     COUNT(*) as total_runs,
--     AVG(execution_time_seconds) as avg_time,
--     MIN(execution_time_seconds) as min_time,
--     MAX(execution_time_seconds) as max_time,
--     STDDEV(execution_time_seconds) as std_dev
-- FROM load_test_results
-- WHERE success = true
-- GROUP BY setup_id, hostname, test_name;

-- Get recent test results
-- SELECT * FROM load_test_results 
-- ORDER BY start_time DESC 
-- LIMIT 50;

-- Get failure analysis
-- SELECT
--     setup_id,
--     hostname,
--     test_name,
--     error_message,
--     COUNT(*) as frequency
-- FROM load_test_results
-- WHERE success = false
-- GROUP BY setup_id, hostname, test_name, error_message
-- ORDER BY frequency DESC;

-- Get FIO performance metrics summary
-- SELECT
--     setup_id,
--     hostname,
--     test_name,
--     COUNT(*) as total_runs,
--     AVG(read_iops) as avg_read_iops,
--     AVG(write_iops) as avg_write_iops,
--     AVG(read_bw_kbps) as avg_read_bw_kbps,
--     AVG(write_bw_kbps) as avg_write_bw_kbps,
--     MAX(read_iops) as max_read_iops,
--     MAX(write_iops) as max_write_iops
-- FROM fio_metrics
-- GROUP BY setup_id, hostname, test_name
-- ORDER BY setup_id, hostname, test_name;

-- Get FIO metrics over time
-- SELECT
--     start_time,
--     test_name,
--     read_iops,
--     write_iops,
--     read_bw_kbps,
--     write_bw_kbps
-- FROM fio_metrics
-- WHERE setup_id = 'your_setup_id'
-- ORDER BY start_time DESC
-- LIMIT 100;