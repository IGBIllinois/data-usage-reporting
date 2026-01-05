# Biocluster Data Management

[![Build Status](https://github.com/IGBIllinois/biocluster_dmanage/actions/workflows/main.yml/badge.svg)](https://github.com/IGBIllinois/biocluster_dmanage/actions/workflows/main.yml)

A comprehensive Python-based system for scanning, analyzing, and reporting storage usage on the Biocluster. This automated workflow scans user directories, processes metadata, generates statistics, and sends personalized usage reports with visualizations to users and supervisors.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Workflow](#workflow)
- [Scripts Documentation](#scripts-documentation)
- [Usage Examples](#usage-examples)
- [Output Files](#output-files)

## Overview

This repository contains an automated pipeline for managing Biocluster storage data:

1. **Scan** - Collect file metadata from GPFS directories (users, labs, groups)
2. **Summarize** - Process raw data into statistical summaries
3. **Database** - Query MySQL for billing information
4. **Visualize** - Generate PDF reports with usage charts
5. **Notify** - Email personalized reports to users and supervisors

The system is designed to run periodically (e.g., monthly) on the `dmanage.igb.illinois.edu` VM.

## Features

- **Multi-target scanning**: Scans user directories (a-z), lab directories, and group directories
- **Configurable workflow**: JSON-based configuration for directories, scan types, and email settings
- **Intelligent statistics**: Tracks total storage, inactive files (>6 months), small files (<1KB), and yearly trends
- **Database integration**: Fetches billing data from MySQL and merges with usage statistics
- **Automated reporting**: Generates professional PDF visualizations with usage tables and charts
- **Smart emailing**: Sends consolidated reports to supervisors including their supervised users' data
- **Flexible execution**: Run all steps or individual scripts with command-line options

## Directory Structure

```
biocluster_dmanage/
├── bin/                          # Main workflow scripts (numbered execution order)
│   ├── 1_run_scans.py           # Step 1: Scan directories and collect metadata
│   ├── 2_summarize_scan.py      # Step 2: Process data into statistics
│   ├── 3_mysql_run.py           # Step 3: Query billing database
│   ├── 4_plot_user.py           # Step 4: Generate PDF reports
│   └── 5_email_user.py          # Step 5: Send email notifications
├── lib/                          # Reusable utility modules
│   ├── scan_utils.py            # Scanning and file processing functions
│   ├── stat_utils.py            # Statistical analysis functions
│   └── email_utils.py           # Email sending functions
├── config/                       # Configuration files (JSON)
│   ├── scan_config.json         # Scan directories and processing settings
│   ├── mysql_config.json        # Database connection and queries
│   └── email_config.json        # SMTP and email template settings
├── data/                         # Raw scan outputs (YYYYMMDD/)
├── results/                      # Processed statistics and reports (YYYYMMDD/)
└── README.md                     # This file
```

## Prerequisites

- **Python 3.8+** (tested with 3.11)
- **Required packages**:
  ```bash
  pip install pandas matplotlib mysql-connector-python
  ```
- **Access requirements**:
  - Read access to GPFS directories
  - MySQL database credentials
  - SMTP server access for sending emails

## Workflow

The complete workflow runs 5 numbered scripts in sequence:

```
1_run_scans.py → 2_summarize_scan.py → 3_mysql_run.py → 4_plot_user.py → 5_email_user.py
```

### Step-by-Step Process

1. **Scan** (`1_run_scans.py`):
   - Recursively scans configured GPFS directories
   - Collects file metadata (size, timestamps, paths)
   - Outputs: `data/YYYYMMDD/{labs,groups,users}/{users.csv, files.csv}`
   - Supports selective scanning: `--scan-type labs groups`

2. **Summarize** (`2_summarize_scan.py`):
   - Processes raw CSV files into aggregated statistics
   - Calculates: total storage, file counts, inactive files, yearly breakdowns
   - Outputs: `results/YYYYMMDD/combined/{user_statistics.csv, yearly_statistics.csv}`

3. **Database Query** (`3_mysql_run.py`):
   - Queries MySQL for current billing information
   - Outputs: `results/YYYYMMDD/combined/current_user_project_bill.csv`

4. **Generate Reports** (`4_plot_user.py`):
   - Merges statistics with billing data
   - Creates PDF reports with usage tables and bar charts (storage and file counts by year)
   - Outputs: `results/YYYYMMDD/combined/plots/{netid}_YYYY-MM-DD.pdf`
   - Also creates: `merged_user_bill.csv`, `not_in_bill.csv`, `not_in_users.csv`

5. **Send Emails** (`5_email_user.py`):
   - Sends personalized PDFs to users
   - Sends consolidated reports to supervisors (includes supervised users' PDFs)
   - Uses SMTP with attachment support

## Scripts Documentation

### `bin/1_run_scans.py`

Scans GPFS directories and collects file metadata.

**Usage:**
```bash
python3 bin/1_run_scans.py [--scan-type {all,users,labs,groups} ...]
```

**Options:**
- `--scan-type`: Select which directories to scan (default: all)

**Outputs:**
- `data/YYYYMMDD/labs/users.csv` - Lab directory summaries
- `data/YYYYMMDD/labs/files.csv` - Individual lab file metadata
- `data/YYYYMMDD/groups/users.csv` - Group directory summaries
- `data/YYYYMMDD/groups/files.csv` - Individual group file metadata
- `data/YYYYMMDD/users/users.csv` - User directory summaries
- `data/YYYYMMDD/users/files.csv` - Individual user file metadata
- `data/YYYYMMDD/scan.log` - Scan timing and statistics log

### `bin/2_summarize_scan.py`

Processes raw scan data into statistical summaries.

**Usage:**
```bash
python3 bin/2_summarize_scan.py
```

**Outputs:**
- `results/YYYYMMDD/combined/user_statistics.csv` - Per-user summary stats
- `results/YYYYMMDD/combined/yearly_statistics.csv` - Yearly breakdown by user
- Includes: TotalFiles, TotalSizeBytes, InactiveFileCount, SmallFileCount, etc.

### `bin/3_mysql_run.py`

Queries MySQL database for billing information.

**Usage:**
```bash
export MYSQL_USER='your_username'
export MYSQL_PASSWORD='your-password'
python3 bin/3_mysql_run.py
```

**Outputs:**
- `results/YYYYMMDD/combined/current_user_project_bill.csv` - Current billing data
- `results/YYYYMMDD/combined/recent_12_bill_summary.csv` - 12-month billing summary

### `bin/4_plot_user.py`

Generates PDF visualization reports for each user.

**Usage:**
```bash
python3 bin/4_plot_user.py
```

**Outputs:**
- `results/YYYYMMDD/combined/plots/{netid}_YYYY-MM-DD.pdf` - Individual PDF reports
- `results/YYYYMMDD/combined/plot_map_all.csv` - Mapping of plots to users
- `results/YYYYMMDD/combined/merged_user_bill.csv` - Statistics merged with billing
- `results/YYYYMMDD/combined/not_in_bill.csv` - NetIDs without billing records
- `results/YYYYMMDD/combined/not_in_users.csv` - Billed users not in scan

Each PDF includes:
- User information table (project, path, dates, file stats, billing)
- Storage usage bar chart by year (GB)
- File count bar chart by year
- University of Illinois branding colors

### `bin/5_email_user.py`

Sends email reports to users and supervisors.

**Usage:**
```bash
python3 bin/5_email_user.py [--dry-run]
```

**Options:**
- `--dry-run`: Show what emails would be sent without actually sending them (recommended before first run)

**Behavior:**
- Regular users: Receive their own PDF report
- Supervisors: Receive their own report + all supervised users' reports
- Email addresses: Defaults to `{netid}@igb.illinois.edu` if not in database
- Requires: `config/email_config.json` and supervisor mapping CSV
- Dry run mode displays summary of recipients and attachment counts without sending

## Usage Examples

### Run Complete Monthly Workflow

```bash
# Set MySQL password
export MYSQL_PASSWORD='your-password'

# Run all 5 steps in sequence
python3 bin/1_run_scans.py
python3 bin/2_summarize_scan.py
python3 bin/3_mysql_run.py
python3 bin/4_plot_user.py

# Preview emails before sending (recommended)
python3 bin/5_email_user.py --dry-run

# Send emails after verifying dry run output
python3 bin/5_email_user.py
```

### Run Partial Workflow

```bash
# Scan only labs and groups
python3 bin/1_run_scans.py --scan-type labs groups

# Process specific folder (edit scan_config.json first)
# Set "target_folder": "20251201" in scan_config.json
python3 bin/2_summarize_scan.py

# Generate plots without emailing
python3 bin/4_plot_user.py
```

## Output Files

### Raw Scan Data (`data/YYYYMMDD/`)

**`{labs,groups,users}/users.csv`**:
| Column | Description |
|--------|-------------|
| ID | Unique identifier |
| NetID | User/lab/group name |
| Group | Category (labs/groups/users) |
| TotalFiles | Total file count |
| TotalSizeBytes | Total size in bytes |
| LastModified | Last modification timestamp |
| ScanTime | Scan duration (seconds) |

**`{labs,groups,users}/files.csv`**:
| Column | Description |
|--------|-------------|
| ID | Directory ID (links to users.csv) |
| NetID | Owner NetID |
| Path | Full file path |
| Name | File name |
| SizeBytes | File size |
| LastModified | Modification timestamp |

### Processed Statistics (`results/YYYYMMDD/combined/`)

**`user_statistics.csv`**:
| Column | Description |
|--------|-------------|
| ID | User ID |
| NetID | User NetID |
| Group | User category |
| TotalFiles | Total file count |
| TotalSizeBytes | Total storage (bytes) |
| InactiveFileCount | Files not modified in 6+ months |
| SmallFileCount | Files < 1KB |
| LargestFileSize | Largest file size (bytes) |
| AvgFileSize | Average file size (bytes) |

**`yearly_statistics.csv`**:
| Column | Description |
|--------|-------------|
| NetID | User NetID |
| Year | File last modified year |
| FileCount | Number of files |
| FileSizeBytes | Total size for that year |

**`current_user_project_bill.csv`** (from MySQL):
| Column | Description |
|--------|-------------|
| data_dir_path | Storage directory path |
| data_bill_date | Billing period date |
| data_bill_avg_bytes | Average storage billed (bytes) |
| data_bill_total_cost | Total storage cost ($) |
| data_bill_billed_cost | Amount billed ($) |
| user_id | Database user ID |
| user_name | User NetID |
| user_firstname | First name |
| user_lastname | Last name |

**`merged_user_bill.csv`**: Combines `user_statistics.csv` with `current_user_project_bill.csv`

**`plot_map_all.csv`**: Maps generated PDFs to user information for email sending

### Reports (`results/YYYYMMDD/combined/plots/`)

PDF files named `{netid}_YYYY-MM-DD.pdf` containing:
- User/project information table
- Total storage usage bar chart (GB by year)
- File count bar chart (by year)

## Notes

- **Performance**: Full scans can take several hours depending on GPFS size
- **Disk Space**: Raw scan data can be large (several GB); consider cleanup policies
- **Security**: Keep `mysql_config.json` and email configs secure (add to `.gitignore`)
- **Scheduling**: Consider running via cron on the 1st of each month
- **Error Handling**: Check `data/YYYYMMDD/scan.log` for scan errors and timing

## Troubleshooting

**Scan fails with permission errors:**
- Ensure the VM has read access to all GPFS directories
- Check `skip_hidden: true` in `scan_config.json`

**MySQL connection fails:**
- Verify `MYSQL_PASSWORD` environment variable is set
- Test connection: `mysql -h host -u user -p database`
- Check `mysql_config.json` credentials

**No PDFs generated:**
- Verify `matplotlib` is installed
- Check that `merged_user_bill.csv` exists and has data
- Review `user_statistics.csv` and `current_user_project_bill.csv` for matching NetIDs

**Emails not sending:**
- Test SMTP connection manually
- Verify `sender_email` and SMTP credentials in `email_config.json`
- Check `plot_map_all.csv` exists

## License

This project is licensed under the GPLv3 License – see the LICENSE file for details.

