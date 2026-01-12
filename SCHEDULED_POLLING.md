# Scheduled Attendance Polling

## Overview
This script polls attendance data from ZK devices at scheduled times (9am and 9pm on weekdays) and saves the data to CSV files.

## Features
- ✓ Scheduled polling at 9am (check-in) and 9pm (check-out) on weekdays only
- ✓ Automatically tracks processed records to avoid duplicates
- ✓ Saves attendance data to daily CSV files
- ✓ Marks each record as 'check-in' or 'check-out' based on poll time
- ✓ Creates `attendance_data/` directory for CSV storage

## Installation

```bash
pip install schedule
```

## Configuration

Edit the configuration variables in `poll_attendance_simple.py`:

```python
DEVICE_IP = '192.168.1.201'    # Your device IP
DEVICE_PORT = 4370              # Your device port
CSV_DIR = 'attendance_data'     # CSV output directory
```

## Usage

### Start the scheduler:
```bash
python3 example/poll_attendance_simple.py
```

The scheduler will run continuously and execute polls at:
- **9:00 AM** (Monday-Friday) - marked as "check-in"
- **9:00 PM** (Monday-Friday) - marked as "check-out"

### Test immediately (without waiting):
Uncomment this line in the `main()` function:
```python
# poll_and_save('check-in')
```

## Output

### CSV Files
CSV files are saved in `attendance_data/` directory:
- Filename format: `attendance_YYYY-MM-DD.csv`
- One file per day

### CSV Format
```csv
user_id,uid,timestamp,status,punch,type,poll_time
123,1,2026-01-09 08:45:32,1,0,check-in,2026-01-09 09:00:15
456,2,2026-01-09 20:55:10,1,0,check-out,2026-01-09 21:00:22
```

**Fields:**
- `user_id`: User's ID on the device
- `uid`: User's unique identifier
- `timestamp`: When the attendance was recorded on device
- `status`: Attendance status code
- `punch`: Punch type code
- `type`: "check-in" or "check-out" (based on poll time)
- `poll_time`: When the data was retrieved

### Tracking File
`attendance_data/processed_records.txt` - Tracks processed records to avoid duplicates

## Running as Background Service

### On macOS/Linux:
```bash
nohup python3 example/poll_attendance_simple.py > scheduler.log 2>&1 &
```

### Using screen/tmux:
```bash
screen -S attendance
python3 example/poll_attendance_simple.py
# Press Ctrl+A then D to detach
```

### As systemd service (Linux):
Create `/etc/systemd/system/attendance-poll.service`:
```ini
[Unit]
Description=ZK Attendance Polling Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/pyzk
ExecStart=/usr/bin/python3 example/poll_attendance_simple.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable attendance-poll
sudo systemctl start attendance-poll
```

## Stop the Scheduler

Press `Ctrl+C` in the terminal where the script is running.

## Notes

- The script only runs on **weekdays** (Monday-Friday)
- Skips weekends automatically
- Records are deduplicated based on user_id + timestamp + status
- If connection fails, error is logged and scheduler continues
- Next scheduled run time is displayed on startup
