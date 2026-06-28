###############################################################################
#                        IPv4/ACL Convertor Script V4.0                       #
###############################################################################
#  Job: This script will convert IPv4 address list to ACL list and vice versa #
#       base on the user input (option 1, 2, 3 and 4)                         #
#       - Push ACL Lines to a Cisco Router using Netmiko Library Added to     #
#         this Version.                                                       #
# Author: Ahmad Mojahed (NOC)                                                 #
# Date: 2026-06-28                                                            #
###############################################################################

from netaddr import IPNetwork, IPAddress, AddrFormatError, cidr_merge
from netmiko import ConnectHandler

# ------------------ File Names ------------------------------------------------
ACL_FILE = "IPV4-ACL.txt"                                  # Input ACL List file in Option 1
IP_LIST_FILE = "IPV4-LIST.txt"                             # Input IPv4 List file in Option 2 and 3
ACL_SEND_FILE = "IPV4-ACL-SEND.txt"                        # Output IPv4 Access List Outbound command in Option 2 
ACL_RECEIVE_FILE = "IPV4-ACL-RECEIVE.txt"                  # Output IPv4 Access List Inbound command in Option 2
ACL_LINES_FILE = "IPV4-ACL-NEW-LINES.txt"                  # Input ACL Lines in Option 4
IP_LIST_OUTPUT_FILE = "IPV4-LIST-CONVERTED.txt"            # Output IPv4 List file in Option 1
IP_LIST_OPTIMIZED_FILE = "IPV4-LIST-OPTIMIZED.txt"         # Output IPv4 List file in Option 3

# ------------------ Validate Wildcard and Convert to Prefix -------------------
def wildcard_to_prefix(wildcard):
    """
    Convert Cisco wildcard mask to prefix length.
    Example:
    0.0.255.255   -> /16
    0.0.0.255     -> /24
    """

    wildcard_ip = IPAddress(wildcard)
    wildcard_int = int(wildcard_ip)

    # Convert wildcard to netmask
    netmask_int = 0xFFFFFFFF - wildcard_int
    netmask = IPAddress(netmask_int)

    # Create temporary network for validation
    network = IPNetwork(f"0.0.0.0/{netmask}")

    # Validate that wildcard is normal/contiguous
    if str(network.netmask) != str(netmask):
        raise ValueError("Invalid wildcard mask")

    return network.prefixlen

# ------------------ Task 1: ACL to IPv4 List ----------------------------------
def acl_to_ipv4_list():
    """
    Read IPV4-ACL.txt and create:
    IPV4-LIST-CONVERTED.txt
    """

    networks = []

    try:
        with open(ACL_FILE, "r") as input_file:

            for line in input_file:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                try:
                    parts = line.split()

                    # Remove ACL sequence number if exists
                    # Example:
                    # 10 permit ip 192.168.1.0 0.0.0.255 any
                    if parts[0].isdigit():
                        parts = parts[1:]

                    # Expected formats:
                    # permit ip any DEST_IP WILDCARD
                    # permit ip SRC_IP WILDCARD any
                    if len(parts) != 5:
                        raise ValueError

                    if parts[0].lower() != "permit" or parts[1].lower() != "ip":
                        raise ValueError

                    # Format:
                    # permit ip any 192.168.1.0 0.0.0.255
                    if parts[2].lower() == "any":
                        ip_address = parts[3]
                        wildcard = parts[4]

                    # Format:
                    # permit ip 192.168.1.0 0.0.0.255 any
                    elif parts[4].lower() == "any":
                        ip_address = parts[2]
                        wildcard = parts[3]

                    else:
                        raise ValueError

                    # Validate IP address
                    ip = IPAddress(ip_address)

                    if ip.version != 4:
                        raise ValueError

                    # Validate wildcard and convert to prefix
                    prefix = wildcard_to_prefix(wildcard)

                    # Build network object
                    network = IPNetwork(f"{ip_address}/{prefix}")

                    # Accept IPv4 only
                    if network.version != 4:
                        raise ValueError

                    networks.append(network)

                except Exception:
                    print(f"Skipped wrong line: {line}")

        # Sort networks ascending
        networks.sort()

        with open(IP_LIST_OUTPUT_FILE, "w") as output_file:
            for network in networks:
                output_file.write(f"{network.network}/{network.prefixlen}\n")

        print("Task Completed Successfully!")

    except FileNotFoundError:
        print(f"Error: File not found: {ACL_FILE}")

    except Exception as error:
        print(f"Unexpected error: {error}")

# ------------------ Task 2: IPv4 List to ACL ----------------------------------
def ipv4_list_to_acl():
    """
    Read IPV4-LIST.txt and create:
    1- IPV4-ACL-SEND.txt
    2- IPV4-ACL-RECEIVE.txt
    """
    networks = []

    try:
        with open(IP_LIST_FILE, "r") as input_file:

            for line in input_file:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                try:
                    # Validate IP/prefix
                    network = IPNetwork(line)

                    # Accept IPv4 only
                    if network.version != 4:
                        raise ValueError

                    networks.append(network)

                except Exception:
                    print(f"Skipped wrong line: {line}")

        # Sort networks ascending
        networks.sort()

        with open(ACL_SEND_FILE, "w") as send_file, \
             open(ACL_RECEIVE_FILE, "w") as receive_file:

            for network in networks:
                ip_address = str(network.network)
                wildcard = str(network.hostmask)

                send_file.write(f"permit ip any {ip_address} {wildcard}\n")
                receive_file.write(f"permit ip {ip_address} {wildcard} any\n")

        print("Task Completed Successfully!")

    except FileNotFoundError:
        print(f"Error: File not found: {IP_LIST_FILE}")

    except Exception as error:
        print(f"Unexpected error: {error}")

# ------------------ Task 3: Optimize IPv4 List --------------------------------
def optimize_ipv4_list():
    """
    Read IPV4-LIST.txt
    Remove unnecessary subnets
    Merge possible adjacent networks
    Create IPV4-LIST-OPTIMIZED.txt
    """
    networks = []

    try:
        with open(IP_LIST_FILE, "r") as input_file:

            for line in input_file:
                line = line.strip()

                if not line:
                    continue

                try:
                    network = IPNetwork(line)

                    # Accept IPv4 only
                    if network.version != 4:
                        raise ValueError

                    networks.append(network)

                except Exception:
                    print(f"Skipped wrong line: {line}")

        # Remove redundant subnets and merge adjacent ranges
        optimized_networks = cidr_merge(networks)

        # Sort optimized networks
        optimized_networks.sort()

        with open(IP_LIST_OPTIMIZED_FILE, "w") as output_file:
            for network in optimized_networks:
                output_file.write(f"{network}\n")

        print("Task Completed Successfully!")

    except FileNotFoundError:
        print(f"Error: File not found: {IP_LIST_FILE}")

    except Exception as error:
        print(f"Unexpected error: {error}")

# ---------- Task 4: Push ACL Lines to Cisco IOS XE ----------
def push_acl_to_cisco():
    """
    Read ACL lines from IPV4-ACL-NEW-LINES.txt
    SSH to Cisco IOS XE router
    Remove deny ip any any
    Add new ACL lines
    Add deny ip any any again at the bottom
    Save configuration
    """

    acl_lines = []

    try:
        # Read ACL lines from file
        with open(ACL_LINES_FILE, "r") as input_file:
            for line in input_file:
                line = line.strip()

                if not line:
                    continue

                # Very simple validation
                if line.startswith("permit ip") or line.startswith("deny ip"):
                    acl_lines.append(line)
                else:
                    print(f"Skipped wrong ACL line: {line}")

        if not acl_lines:
            print("No valid ACL lines found.")
            return

        # Ask user for device information
        dnsname = input("Enter Router DNS/IP: ").strip()
        username = input("Enter Username: ").strip()
        password = input("Enter Password: ").strip()
        acl_name = input("Enter ACL Name: ").strip()

        # Cisco IOS XE device information
        device = {
            "device_type": "cisco_ios",
            "host": dnsname,
            "username": username,
            "password": password,
            "secret": password,
        }

        print("Connecting to device...")

        connection = ConnectHandler(**device)
        connection.enable()

        print("Connected successfully.")
        print("Sending ACL commands...")

        # Build configuration commands
        commands = [
            f"ip access-list extended {acl_name}",
            "no deny ip any any",
        ]

        # Add new ACL lines
        commands.extend(acl_lines)

        # Add deny any any again at the bottom
        commands.append("deny ip any any")

        # Push commands to router
        output = connection.send_config_set(commands)

        # Save configuration
        save_output = connection.save_config()

        connection.disconnect()

        print(output)
        print(save_output)
        print("Task Completed Successfully!")

    except FileNotFoundError:
        print(f"Error: File not found: {ACL_LINES_FILE}")

    except Exception as error:
        print(f"Unexpected error: {error}")
        
# ------------------ Main Menu -------------------------------------------------
def main():
    print("***** ACL/IPv4 Convertor *****")
    print("Choose the Process")
    print("1- ACL to IPv4 List")
    print("2- IPv4 List to ACL")
    print("3- Optimize IPv4 List")
    print("4- Push ACL Lines to Cisco Router")

    process = input("Enter your Process(1 or 2): ").strip()

    if process == "1":
        acl_to_ipv4_list()

    elif process == "2":
        ipv4_list_to_acl()
        
    elif process == "3":
        optimize_ipv4_list()
    
    elif process == "4":
        push_acl_to_cisco()

    else:
        print("Invalid choice. Please enter 1, 2, 3 or 4.")


# ------------------ Start Script ----------------------------------------------
if __name__ == "__main__":
    main()
# ------------------ End -------------------------------------------------------