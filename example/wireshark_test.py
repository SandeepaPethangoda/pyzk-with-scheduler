# -*- coding: utf-8 -*-
"""
Test script to demonstrate ZK device communication for Wireshark capture

Run this while Wireshark is capturing with filter:
  ip.addr == 192.168.1.201 && (tcp.port == 4370 || udp.port == 4370)
"""
import os
import sys
import time

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK

# Configuration
DEVICE_IP = '192.168.1.201'
DEVICE_PORT = 4370
USE_UDP = False  # Set True to test UDP instead of TCP

print("="*70)
print("ZK Device Communication Test for Wireshark")
print("="*70)
print(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
print(f"Protocol: {'UDP' if USE_UDP else 'TCP'}")
print()
print("START WIRESHARK NOW with this filter:")
print(f"  ip.addr == {DEVICE_IP} && ({'udp' if USE_UDP else 'tcp'}.port == {DEVICE_PORT})")
print()
print("You should see:")
if USE_UDP:
    print("  - UDP packets from your IP to device IP:4370")
    print("  - UDP responses from device IP:4370 to your IP")
else:
    print("  - TCP 3-way handshake (SYN, SYN-ACK, ACK)")
    print("  - TCP data packets (PSH) with ZK protocol")
    print("  - TCP connection close (FIN)")
print()
print("Waiting 5 seconds for you to start Wireshark...")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

print()
print("="*70)
print("STEP 1: Connecting to device...")
print("="*70)
time.sleep(1)

conn = None
zk = ZK(DEVICE_IP, port=DEVICE_PORT, force_udp=USE_UDP, verbose=True)

try:
    conn = zk.connect()
    print("✓ Connected successfully")
    print()
    
    # Small pause to see connection packets clearly
    time.sleep(2)
    
    print("="*70)
    print("STEP 2: Getting device info...")
    print("="*70)
    time.sleep(1)
    
    # Get firmware version (small request)
    try:
        firmware = conn.get_firmware_version()
        print(f"✓ Firmware: {firmware}")
    except:
        print("✗ Could not get firmware")
    
    time.sleep(2)
    
    print()
    print("="*70)
    print("STEP 3: Reading attendance data...")
    print("="*70)
    time.sleep(1)
    
    # Get attendance (larger data transfer)
    attendances = conn.get_attendance()
    print(f"✓ Retrieved {len(attendances)} attendance records")
    
    if attendances:
        print("\nFirst 3 records:")
        for att in attendances[:3]:
            print(f"  - User: {att.user_id}, Time: {att.timestamp}, Status: {att.status}")
    
    time.sleep(2)
    
    print()
    print("="*70)
    print("STEP 4: Getting users...")
    print("="*70)
    time.sleep(1)
    
    users = conn.get_users()
    print(f"✓ Retrieved {len(users)} users")
    
    if users:
        print("\nFirst 3 users:")
        for user in users[:3]:
            print(f"  - UID: {user.uid}, Name: {user.name}, User ID: {user.user_id}")
    
    time.sleep(2)
    
    print()
    print("="*70)
    print("STEP 5: Disconnecting...")
    print("="*70)
    time.sleep(1)
    
    conn.disconnect()
    print("✓ Disconnected")
    
    print()
    print("="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print()
    print("Now check Wireshark:")
    print("  1. Stop the capture")
    print("  2. Look for packets between your IP and device IP")
    print("  3. You should see all the request/response exchanges")
    print()
    print("Packet Flow:")
    print("  - Connection establishment")
    print("  - CMD_CONNECT + response")
    print("  - Multiple data request/response pairs")
    print("  - Connection termination")
    print()
    print("To decode ZK protocol properly, load zk6.lua dissector in Wireshark:")
    print("  Wireshark → Preferences → Protocols → Lua → Add zk6.lua")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print()
    print("Common issues:")
    print("  - Device IP incorrect or unreachable")
    print("  - Device port blocked by firewall")
    print("  - Device already connected by another client")
    print("  - Wrong network interface in Wireshark")
finally:
    if conn:
        try:
            conn.disconnect()
        except:
            pass

print()
print("="*70)
