###############################################################################
#                        ACL/IPv4 Convertor Script V1.0                       #
###############################################################################
#  Job: This script will convert IPv4 address list to ACL list and vice versa #
#       base on the user input (option 1 & 2)                                 #
# Author: Ahmad Mojahed (NOC)                                                 #
# Date: 2026-06-22                                                            #
###############################################################################

import ipaddress                                           # Built-in Library

# ---------- File Names --------------------------
IP_LIST_FILE = "IPV4-LIST.txt"                             # Input IPv4 List file in Option 1
ACL_FILE = "IPV4-ACL.txt"                                  # Input ACL List file in Option 2
ACL_SEND_FILE = "IPV4-ACL-SEND.txt"                        # Output IPv4 Access List Outbound command in Option 1 
ACL_RECEIVE_FILE = "IPV4-ACL-RECEIVE.txt"                  # Output IPv4 Access List Inbound command in Option 1
IP_LIST_OUTPUT_FILE = "IPV4-LIST-CONVERTED.txt"            # Output IPv4 List file in Option 2

# ---------- Convert /Prefix to Wildcard --------------
def prefix_to_wildcard(prefix):
    """
    Example:
    /16 -> 0.0.255.255
    /24 -> 0.0.0.255
    """
    netmask = ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask
    wildcard_int = 0xFFFFFFFF - int(netmask)
    return str(ipaddress.IPv4Address(wildcard_int))

# ---------- Convert Wildcard to /Prefix ---------
def wildcard_to_prefix(wildcard):
    """
    Example:
    0.0.255.255 -> /16
    0.0.0.255 -> /24
    """
    wildcard_int = int(ipaddress.IPv4Address(wildcard))
    netmask_int = 0xFFFFFFFF - wildcard_int
    netmask = ipaddress.IPv4Address(netmask_int)
    network = ipaddress.IPv4Network(f"0.0.0.0/{netmask}", strict=False)
    return network.prefixlen

# ---------- Task 1: IPv4 List to ACL ------------
def ipv4_list_to_acl():
    try:
        with open(IP_LIST_FILE, "r") as input_file, \
             open(ACL_SEND_FILE, "w") as send_file, \
             open(ACL_RECEIVE_FILE, "w") as receive_file:

            for line in input_file:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue

                try:
                    network = ipaddress.IPv4Network(line, strict=False)
                    ip_address = str(network.network_address)
                    prefix = network.prefixlen
                    wildcard = prefix_to_wildcard(prefix)

                    send_file.write(f"permit ip any {ip_address} {wildcard}\n")
                    receive_file.write(f"permit ip {ip_address} {wildcard} any\n")

                except Exception:
                    # Wrong line format, skip and continue
                    print(f"Skipped wrong line: {line}")

        print("Task Completed Successfully!")

    except FileNotFoundError:
        print(f"Error: File not found: {IP_LIST_FILE}")

    except Exception as error:
        print(f"Unexpected error: {error}")

# ---------- Task 2: ACL to IPv4 List ------------
def acl_to_ipv4_list():
    try:
        with open(ACL_FILE, "r") as input_file, \
             open(IP_LIST_OUTPUT_FILE, "w") as output_file:

            for line in input_file:
                line = line.strip()

                if not line:
                    continue

                try:
                    parts = line.split()

                    # If first part is ACL sequence number, remove it
                    # Example:
                    # 10 permit ip 10.10.10.0 0.0.0.63 any
                    if parts[0].isdigit():
                        parts = parts[1:]

                    # Now expected format must be:
                    # permit ip any DEST_IP WILDCARD
                    # permit ip SRC_IP WILDCARD any
                    if len(parts) != 5:
                        raise ValueError

                    if parts[0] != "permit" or parts[1] != "ip":
                        raise ValueError

                    # Format: permit ip any 10.10.10.0 0.0.0.63
                    if parts[2] == "any":
                        ip_address = parts[3]
                        wildcard = parts[4]

                    # Format: permit ip 10.10.10.0 0.0.0.63 any
                    elif parts[4] == "any":
                        ip_address = parts[2]
                        wildcard = parts[3]

                    else:
                        raise ValueError

                    prefix = wildcard_to_prefix(wildcard)
                    network = ipaddress.IPv4Network(f"{ip_address}/{prefix}", strict=False)

                    output_file.write(f"{network.network_address}/{prefix}\n")

                except Exception:
                    print(f"Skipped wrong line: {line}")

        print("Task Completed Successfully!")

    except FileNotFoundError:
        print(f"Error: File not found: {ACL_FILE}")

    except Exception as error:
        print(f"Unexpected error: {error}")

# ---------- Main Menu ---------------------------
def main():
    print("***** ACL/IPv4 Convertor *****")
    print("Choose the Process")
    print("1- ACL to IPv4 List")
    print("2- IPv4 List to ACL")

    process = input("Enter your Process(1 or 2): ").strip()

    if process == "1":
        acl_to_ipv4_list()

    elif process == "2":
        ipv4_list_to_acl()

    else:
        print("Invalid choice. Please enter 1 or 2.")

# ---------- Start Script ------------------------
if __name__ == "__main__":
    main()
# ---------- End ---------------------------------