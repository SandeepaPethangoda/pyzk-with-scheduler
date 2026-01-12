# -*- coding: utf-8 -*-
"""
Poll attendance data from ZK device(s) at regular intervals
This is an alternative to live_capture for retrieving attendance records
"""
import os
import sys
import time
from datetime import datetime

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK


def poll_single_device(ip, port=4370, interval=5):
    """
    Poll attendance data from a single device at regular intervals
    
    :param ip: Device IP address
    :param port: Device port (default: 4370)
    :param interval: Polling interval in seconds (default: 5)
    """
    conn = None
    zk = ZK(ip, port=port)
    last_attendance_count = 0
    
    try:
        print(f"[{ip}] Connecting...")
        conn = zk.connect()
        print(f"[{ip}] Connected successfully")
        
        while True:
            try:
                # Get all attendance records
                attendances = conn.get_attendance()
                current_count = len(attendances)
                
                # Only show new records
                if current_count > last_attendance_count:
                    print(f"\n[{ip}] Found {current_count - last_attendance_count} new record(s):")
                    for att in attendances[last_attendance_count:]:
                        print(f"[{ip}] User: {att.user_id}, Time: {att.timestamp}, Status: {att.status}")
                    last_attendance_count = current_count
                else:
                    print(f"[{ip}] No new records (total: {current_count})")
                
                # Wait before next poll
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n[{ip}] Stopping polling...")
                break
            except Exception as e:
                print(f"[{ip}] Error during polling: {e}")
                time.sleep(interval)
                
    except Exception as e:
        print(f"[{ip}] Connection error: {e}")
    finally:
        if conn:
            conn.disconnect()
            print(f"[{ip}] Disconnected")


def poll_multiple_devices(devices, interval=5):
    """
    Poll attendance data from multiple devices using threading
    
    :param devices: List of tuples (ip, port, name)
    :param interval: Polling interval in seconds
    """
    import threading
    
    def poll_device(ip, port, device_name, interval):
        conn = None
        zk = ZK(ip, port=port)
        last_attendance_count = 0
        
        try:
            print(f"[{device_name}] Connecting to {ip}:{port}...")
            conn = zk.connect()
            print(f"[{device_name}] Connected successfully")
            
            while True:
                try:
                    attendances = conn.get_attendance()
                    current_count = len(attendances)
                    
                    if current_count > last_attendance_count:
                        print(f"\n[{device_name}] Found {current_count - last_attendance_count} new record(s):")
                        for att in attendances[last_attendance_count:]:
                            print(f"[{device_name}] User: {att.user_id}, Time: {att.timestamp}, Status: {att.status}")
                        last_attendance_count = current_count
                    else:
                        print(f"[{device_name}] No new records (total: {current_count})")
                    
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[{device_name}] Error during polling: {e}")
                    time.sleep(interval)
                    
        except Exception as e:
            print(f"[{device_name}] Connection error: {e}")
        finally:
            if conn:
                conn.disconnect()
                print(f"[{device_name}] Disconnected")
    
    # Create threads for each device
    threads = []
    for ip, port, name in devices:
        t = threading.Thread(target=poll_device, args=(ip, port, name, interval))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Keep main thread alive
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nStopping all polling threads...")


if __name__ == "__main__":
    # Example 1: Poll single device
    # poll_single_device('192.168.1.201', port=4370, interval=5)
    
    # Example 2: Poll multiple devices
    devices = [
        ('192.168.1.201', 4370, 'Device-1'),
        ('192.168.1.202', 4370, 'Device-2'),
        ('192.168.1.203', 4370, 'Device-3')
    ]
    poll_multiple_devices(devices, interval=5)
