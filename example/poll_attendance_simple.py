# -*- coding: utf-8 -*-
"""
Scheduled attendance polling: Runs at 9am and 9pm on weekdays
Saves attendance data to CSV files with check-in/check-out designation
"""
import os
import sys
import time
import csv
from datetime import datetime, time as dt_time
import schedule

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK

# Configuration
DEVICE_IP = '192.168.1.201'
DEVICE_PORT = 4370
CSV_DIR = os.path.join(ROOT_DIR, 'attendance_data')

# Create CSV directory if it doesn't exist
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)

# Track processed attendance records
processed_records = set()


def load_processed_records():
    """Load previously processed records from tracking file"""
    tracking_file = os.path.join(CSV_DIR, 'processed_records.txt')
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            return set(line.strip() for line in f)
    return set()


def save_processed_record(record_id):
    """Save processed record ID to tracking file"""
    tracking_file = os.path.join(CSV_DIR, 'processed_records.txt')
    with open(tracking_file, 'a') as f:
        f.write(f"{record_id}\n")


def create_record_id(att):
    """Create unique ID for attendance record"""
    return f"{att.user_id}_{att.timestamp.strftime('%Y%m%d%H%M%S')}_{att.status}"


def poll_and_save(attendance_type):
    """
    Poll attendance data and save to CSV
    
    :param attendance_type: 'check-in' or 'check-out'
    """
    global processed_records
    
    conn = None
    zk = ZK(DEVICE_IP, port=DEVICE_PORT)
    
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting {attendance_type} poll...")
        conn = zk.connect()
        print(f"Connected to device {DEVICE_IP}")
        
        # Get all attendance records
        attendances = conn.get_attendance()
        print(f"Retrieved {len(attendances)} total records")
        
        # Filter new records only
        new_records = []
        for att in attendances:
            record_id = create_record_id(att)
            if record_id not in processed_records:
                new_records.append(att)
                processed_records.add(record_id)
                save_processed_record(record_id)
        
        if new_records:
            # Create CSV filename with current date
            today = datetime.now().strftime('%Y-%m-%d')
            csv_filename = os.path.join(CSV_DIR, f'attendance_{today}.csv')
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(csv_filename)
            
            # Write to CSV
            with open(csv_filename, 'a', newline='') as csvfile:
                fieldnames = ['user_id', 'uid', 'timestamp', 'status', 'punch', 'type', 'poll_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                for att in new_records:
                    writer.writerow({
                        'user_id': att.user_id,
                        'uid': att.uid,
                        'timestamp': att.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'status': att.status,
                        'punch': att.punch,
                        'type': attendance_type,
                        'poll_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"✓ Saved {len(new_records)} new record(s) to {csv_filename}")
            print(f"  Type: {attendance_type}")
            for att in new_records:
                print(f"  - User: {att.user_id}, Time: {att.timestamp}, Status: {att.status}")
        else:
            print("No new records found")
        
        conn.disconnect()
        print("Disconnected successfully\n")
        
    except Exception as e:
        print(f"Error during polling: {e}\n")
        if conn:
            try:
                conn.disconnect()
            except:
                pass


def check_in_job():
    """Job for 9am check-in poll"""
    poll_and_save('check-in')


def check_out_job():
    """Job for 9pm check-out poll"""
    poll_and_save('check-out')


def is_weekday():
    """Check if today is a weekday (Monday=0 to Friday=4)"""
    return datetime.now().weekday() < 5


def main():
    """Main scheduling loop"""
    global processed_records
    
    print("="*60)
    print("Attendance Polling Scheduler")
    print("="*60)
    print(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
    print(f"CSV Directory: {CSV_DIR}")
    print("Schedule: Weekdays at 9:00 AM and 9:00 PM")
    print("="*60)
    print()
    
    # Load previously processed records
    processed_records = load_processed_records()
    print(f"Loaded {len(processed_records)} previously processed records")
    
    # Schedule jobs for weekdays only
    schedule.every().monday.at("09:00").do(check_in_job)
    schedule.every().monday.at("21:00").do(check_out_job)
    
    schedule.every().tuesday.at("09:00").do(check_in_job)
    schedule.every().tuesday.at("21:00").do(check_out_job)
    
    schedule.every().wednesday.at("09:00").do(check_in_job)
    schedule.every().wednesday.at("21:00").do(check_out_job)
    
    schedule.every().thursday.at("09:00").do(check_in_job)
    schedule.every().thursday.at("21:00").do(check_out_job)
    
    schedule.every().friday.at("09:00").do(check_in_job)
    schedule.every().friday.at("21:00").do(check_out_job)
    
    print("Scheduler started. Press Ctrl+C to stop.")
    print(f"Next run: {schedule.next_run()}")
    print()
    
    # Optional: Run once immediately for testing
    # Uncomment the line below to test without waiting
    # poll_and_save('check-in')
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


if __name__ == "__main__":
    main()
