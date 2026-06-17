####################################################################################################
# Name: Cisco _ Vlan Check V2                                                                      #
# Job: This script connects to a Layer-2 Cisco switch, extracts VLAN IDs and VLAN Names, then      #
#      connects to one or more BRAS routers and checks whether each VLAN has a corresponding       #    
#      sub-interface.                                                                              #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-12-22                                                                                 #
####################################################################################################

from netmiko import ConnectHandler
from getpass import getpass
import re
import csv
from datetime import datetime

# ------------------------------------------------------------
# Reserved VLANs (Must be Ignored)
# ------------------------------------------------------------
RESERVED_VLANS = {1, 1002, 1003, 1004, 1005}

# ------------------------------------------------------------
# Parse VLAN IDs and VLAN Names from switch output
# ------------------------------------------------------------
def parse_vlans(output):
    """
    Returns a dictionary:
        { vlan_id : vlan_name }
    """
    vlans = {}

    for line in output.splitlines():
        match = re.match(r"^\s*(\d+)\s+(\S+)\s+", line)
        if match:
            vlan_id = int(match.group(1))
            vlan_name = match.group(2)
            vlans[vlan_id] = vlan_name

    return vlans

# ------------------------------------------------------------
# Check VTP operating mode
# ------------------------------------------------------------
def check_vtp_mode(connection):
    output = connection.send_command("show vtp status")
    match = re.search(r"VTP Operating Mode\s+:\s+(\S+)", output)

    if not match:
        return None

    return match.group(1).lower()

# ------------------------------------------------------------
# Check if VLAN has real subinterface on BRAS
# ------------------------------------------------------------
def check_vlan_on_bras(connection, vlan_id):
    command = f"show interface description | include .{vlan_id}"
    output = connection.send_command(command)

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip PPPoE virtual-access interfaces
        if line.startswith("Vi"):
            continue

        # Skip deleted subinterfaces
        if "deleted" in line.lower():
            continue

        match = re.match(r"^\S+\.([0-9]+)", line)
        if match and int(match.group(1)) == vlan_id:
            return True

    return False

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    username = input("Enter ISE username: ")
    password = getpass("Enter ISE password: ")

    switch_host = input("Enter Switch DNS name: ")

    # --------------------------------------------------------
    # Collect BRAS routers
    # --------------------------------------------------------
    bras_hosts = []
    while True:
        bras = input("Enter BRAS Router DNS name: ")
        bras_hosts.append(bras)

        more = input("Add Another BRAS Router ? (yes/no): ").strip().lower()
        if more != "yes":
            break

    # --------------------------------------------------------
    # Connect to L2 switch
    # --------------------------------------------------------
    print(f"\nConnecting to switch {switch_host} ...")
    l2_device = {
        "device_type": "cisco_ios",
        "host": switch_host,
        "username": username,
        "password": password,
    }

    conn_switch = ConnectHandler(**l2_device)
    print("Connected to switch.")

    # --------------------------------------------------------
    # Check VTP mode
    # --------------------------------------------------------
    vtp_mode = check_vtp_mode(conn_switch)

    if vtp_mode == "client":
        print("\nThis Switch are in Clinet VTP Status, Check the Corespondig Server Switch")
        conn_switch.disconnect()
        return

    print(f"VTP Mode detected: {vtp_mode.upper()}")

    # --------------------------------------------------------
    # Get VLAN list + VLAN names and exclude reserved VLANs
    # --------------------------------------------------------
    vlan_output = conn_switch.send_command("show vlan brief")
    vlan_dict = parse_vlans(vlan_output)

    # Remove reserved VLANs
    for rv in RESERVED_VLANS:
        vlan_dict.pop(rv, None)

    print(f"VLANs after excluding reserved VLANs: {list(vlan_dict.keys())}")

    conn_switch.disconnect()

    # --------------------------------------------------------
    # Connect to BRAS routers
    # --------------------------------------------------------
    bras_connections = []

    for bras in bras_hosts:
        print(f"\nConnecting to BRAS {bras} ...")
        bras_device = {
            "device_type": "cisco_ios",
            "host": bras,
            "username": username,
            "password": password,
        }
        conn = ConnectHandler(**bras_device)
        bras_connections.append(conn)
        print(f"Connected to BRAS {bras}")

    # --------------------------------------------------------
    # Check VLAN usage
    # --------------------------------------------------------
    results = []

    for vlan_id, vlan_name in vlan_dict.items():
        in_use = False

        for conn in bras_connections:
            if check_vlan_on_bras(conn, vlan_id):
                in_use = True
                break

        if in_use:
            status = "IN-USE"
            cleanup_cmd = ""
        else:
            status = "NOT-IN-USE"
            cleanup_cmd = f"no vlan {vlan_id}"

        results.append({
            "vlan_id": vlan_id,
            "vlan_name": vlan_name,
            "status": status,
            "cleanup_command": cleanup_cmd
        })

        print(f"VLAN {vlan_id} ({vlan_name}): {status}")

    for conn in bras_connections:
        conn.disconnect()

    # --------------------------------------------------------
    # CSV filename with timestamp + switch name
    # --------------------------------------------------------
    now = datetime.now()
    timestamp = now.strftime("%Y_%m_%d_%H_%M")
    csv_filename = f"Report_{switch_host}_{timestamp}.csv"

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["vlan_id", "vlan_name", "status", "cleanup_command"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nReport saved as: {csv_filename}")
    print("Done.\n")

# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
