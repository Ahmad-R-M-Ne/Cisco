####################################################################################################
# Name: Cisco _ Vlan Check V3                                                                      #
# Job: This script connects to a Cisco switch via SSH using Netmiko, retrieves VLAN information,   #
#      and identifies VLANs that **do not have any dynamically learned MAC addresses**.            #
#      It ignores VLANs 1002-1005, which are default reserved VLANs on Cisco switches.             #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-12-22                                                                                 #
####################################################################################################

from netmiko import ConnectHandler

# Get user credentials and device hostname
username = input("Enter your Username :")
password = input("Enter your Password: ")
hostname = input("Enter the switch hostname or IP address: ")

# Define the device connection details
device = {
    "device_type": "cisco_ios",  # Cisco IOS device type for Netmiko
    "host": hostname,
    "username": username,
    "password": password,
}

try:
    # Establish SSH connection
    net_connect = ConnectHandler(**device)
    print(f"Connected to {hostname}")

    # Get VLAN list from "show vlan brief"
    vlan_brief = net_connect.send_command("show vlan brief")
    vlan_lines = vlan_brief.splitlines()

    vlans = []
    for line in vlan_lines:
        if line and line[0].isdigit():  # Check if the line starts with a number (VLAN ID)
            vlan_id = line.split()[0]   # Extract VLAN ID
            if vlan_id not in ["1002", "1003", "1004", "1005"]:  # Skip reserved VLANs
                vlans.append(vlan_id)

    unused_vlans = []

    # Check each VLAN for dynamically learned MAC addresses
    for vlan in vlans:
        mac_table = net_connect.send_command(f"show mac address-table dynamic vlan {vlan}")

        # If no dynamically learned MAC addresses exist, add VLAN to the unused list
        if "No entries found." in mac_table or not any(char.isdigit() for char in mac_table):
            unused_vlans.append(vlan)

    # Display results
    if unused_vlans:
        print("\nVLANs with no dynamically learned MAC addresses (possibly unused):")
        for vlan in unused_vlans:
            print(f"- VLAN {vlan}")
    else:
        print("\nAll VLANs have dynamically learned MAC addresses.")

    # Close SSH connection
    net_connect.disconnect()

except Exception as e:
    print(f"Error: {e}")