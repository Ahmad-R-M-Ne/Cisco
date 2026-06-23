###############################################################################
#                        IPv4/ACL Convertor Script V3.0                       #
###############################################################################
#  Job: This script will convert IPv4 address list to ACL list and vice versa #
#       base on the user input (option 1, 2 and 3)                            #
#       - Prefix cleanup and Redundant subnet removal Added to this Version   #
# Author: Ahmad Mojahed (NOC)                                                 #
# Date: 2026-06-23                                                            #
###############################################################################

from netaddr import IPNetwork, IPAddress, AddrFormatError, cidr_merge

# ------------------ File Names ------------------------------------------------
ACL_FILE = "IPV4-ACL.txt"                                  # Input ACL List file in Option 1
IP_LIST_FILE = "IPV4-LIST.txt"                             # Input IPv4 List file in Option 2 and 3
ACL_SEND_FILE = "IPV4-ACL-SEND.txt"                        # Output IPv4 Access List Outbound command in Option 2 
ACL_RECEIVE_FILE = "IPV4-ACL-RECEIVE.txt"                  # Output IPv4 Access List Inbound command in Option 2
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

# ------------------ Task 1: IPv4 List to ACL ----------------------------------
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

# ------------------ Main Menu -------------------------------------------------
def main():
    print("***** ACL/IPv4 Convertor *****")
    print("Choose the Process")
    print("1- ACL to IPv4 List")
    print("2- IPv4 List to ACL")
    print("3- Optimize IPv4 List")

    process = input("Enter your Process(1 or 2): ").strip()

    if process == "1":
        acl_to_ipv4_list()

    elif process == "2":
        ipv4_list_to_acl()
        
    elif process == "3":
        optimize_ipv4_list()

    else:
        print("Invalid choice. Please enter 1, 2 or 3.")


# ------------------ Start Script ----------------------------------------------
if __name__ == "__main__":
    main()
# ------------------ End -------------------------------------------------------