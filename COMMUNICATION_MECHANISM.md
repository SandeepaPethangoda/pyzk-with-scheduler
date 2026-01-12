# ZK Device Communication Mechanism Explained

## Overview
The ZK attendance devices use a **CLIENT-INITIATED REQUEST-RESPONSE** protocol, not passive listening. This is why Wireshark may not show what you expect.

## Communication Architecture

### 1. **Polling Mode** (`get_attendance()`)
**How it works:**
```
Your Computer (Client)              ZK Device (Server)
      |                                    |
      |------ Connect (CMD_CONNECT) ----->|
      |<----- ACK_OK --------------------|
      |                                    |
      |------ Request Data (CMD_ATTLOG_RRQ) ->|
      |<----- Attendance Records ---------|
      |                                    |
      |------ Disconnect (CMD_EXIT) ----->|
```

**Protocol Details:**
- **Transport**: TCP (default) or UDP
- **Port**: 4370 (default)
- **Direction**: YOU → Device (request) then Device → YOU (response)
- **Connection**: Client connects to device, device doesn't initiate

**Wireshark Filter to See This:**
```
tcp.port == 4370 or udp.port == 4370
```

### 2. **Live Capture Mode** (`live_capture()`)
**How it works:**
```
Your Computer                       ZK Device
      |                                    |
      |------ Connect & Auth ------------>|
      |<----- ACK_OK --------------------|
      |                                    |
      |------ Register Event (EF_ATTLOG) ->|
      |<----- ACK_OK --------------------|
      |                                    |
      |     [Keeps socket open, waiting]   |
      |                                    |
      |           [User scans finger]      |
      |                                    |
      |<----- Event Push (CMD_REG_EVENT) -|
      |------ ACK_OK ------------------->|
      |                                    |
      |<----- Event Push (CMD_REG_EVENT) -|
      |------ ACK_OK ------------------->|
```

**Key Point**: Even in "live capture", YOU still initiate the connection first. The device then uses that **existing connection** to push events back to you.

## Why Wireshark Might Not Show Traffic

### Reason 1: **No Active Connection**
The polling script only connects at scheduled times (9am, 9pm). If you're capturing at 2pm, there's nothing to see!

### Reason 2: **Wrong Interface**
If the device is on a different network segment or you're capturing on the wrong interface.

### Reason 3: **Encrypted/Obfuscated Protocol**
The ZK protocol uses custom binary packets with checksums. They won't look like HTTP or other standard protocols.

## How to Capture ZK Traffic with Wireshark

### Step 1: Find the Right Interface
```bash
# List all interfaces
ifconfig -a  # macOS/Linux
ipconfig /all  # Windows

# Your device IP is 192.168.1.201
# Look for interface with 192.168.1.x IP
```

### Step 2: Start Capture with Filter
In Wireshark:
```
ip.addr == 192.168.1.201 && (tcp.port == 4370 || udp.port == 4370)
```

### Step 3: Trigger Communication
While Wireshark is running, execute:
```bash
python3 example/poll_attendance_simple.py
```
Or manually trigger a poll by uncommenting line 182.

### Step 4: What You'll See

**TCP Mode (default):**
```
[SYN] Your_IP:random_port → 192.168.1.201:4370
[SYN-ACK] 192.168.1.201:4370 → Your_IP:random_port
[ACK] Your_IP:random_port → 192.168.1.201:4370
[PSH] Your_IP → Device (CMD_CONNECT packet)
[PSH] Device → Your_IP (ACK_OK response)
[PSH] Your_IP → Device (CMD_ATTLOG_RRQ)
[PSH] Device → Your_IP (Attendance data)
[FIN] Connection close
```

**UDP Mode:**
```
Your_IP:random_port → 192.168.1.201:4370 (CMD_CONNECT)
192.168.1.201:4370 → Your_IP:random_port (ACK_OK)
Your_IP:random_port → 192.168.1.201:4370 (CMD_ATTLOG_RRQ)
192.168.1.201:4370 → Your_IP:random_port (Data response)
```

## Packet Structure

### ZK Protocol Header (8 bytes for UDP, 16 for TCP)
```
TCP Header (8 bytes):
  0x5050 (magic)
  0x827d (magic)
  Length (4 bytes)

Command Header (8 bytes):
  Command ID (2 bytes)  - e.g., 0x03E8 = CMD_CONNECT
  Checksum (2 bytes)
  Session ID (2 bytes)
  Reply ID (2 bytes)

Data: Variable length
```

## Technical Deep Dive

### The Socket Connection Code:
```python
# From zk/base.py line 173-179
if self.tcp:
    self.__sock = socket(AF_INET, SOCK_STREAM)  # TCP socket
    self.__sock.settimeout(self.__timeout)
    self.__sock.connect_ex(self.__address)      # Client connects
else:
    self.__sock = socket(AF_INET, SOCK_DGRAM)   # UDP socket
    self.__sock.settimeout(self.__timeout)
```

### Command Sending (line 237-267):
```python
def __send_command(self, command, command_string=b'', response_size=8):
    # Build packet
    buf = self.__create_header(command, command_string, ...)
    
    if self.tcp:
        self.__sock.send(top)          # Send to device
        self.__tcp_data_recv = self.__sock.recv(...)  # Wait for response
    else:
        self.__sock.sendto(buf, self.__address)  # Send UDP
        self.__data_recv = self.__sock.recv(...)      # Wait for response
```

## There is NO Passive Listening

**What DOESN'T happen:**
- ❌ Device broadcasting to network
- ❌ Device multicasting events
- ❌ Device pushing to a known server IP
- ❌ Listening on a local port waiting for device

**What DOES happen:**
- ✅ You connect to device at IP:port
- ✅ You send command request
- ✅ Device responds on same connection
- ✅ Connection closes (or stays open for live events)

## Real-Time Testing

### Test Script to See Traffic:
```python
from zk import ZK
import time

print("Connecting... Watch Wireshark NOW!")
time.sleep(2)

zk = ZK('192.168.1.201', port=4370, verbose=True)
conn = zk.connect()

print("Getting attendance... Check Wireshark!")
attendances = conn.get_attendance()
print(f"Got {len(attendances)} records")

time.sleep(2)
conn.disconnect()
print("Done. Check Wireshark capture.")
```

Run this while Wireshark is capturing on the correct interface with the filter:
```
ip.addr == 192.168.1.201
```

## Protocol Analyzer

The repo includes a Wireshark dissector: `zk6.lua`
Load it in Wireshark to decode ZK packets properly:
1. Wireshark → Preferences → Protocols → Lua
2. Add `zk6.lua` script
3. Packets will show decoded command names instead of hex

## Summary

**The mechanism is:**
1. **CLIENT-INITIATED**: Your script connects to the device
2. **REQUEST-RESPONSE**: You ask, device answers
3. **PROPRIETARY PROTOCOL**: Custom binary format over TCP/UDP
4. **NO PASSIVE LISTENING**: Device never initiates connection to you
5. **SCHEDULED POLLING**: Script only connects at 9am/9pm on weekdays

That's why you don't see continuous traffic in Wireshark - the connection only happens when the scheduler triggers!
