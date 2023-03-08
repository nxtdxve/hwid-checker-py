import wmi
import hashlib

wmi_obj = wmi.WMI()

# Get processor ID
processor_id = wmi_obj.Win32_Processor()[0].ProcessorId.strip()

# Get motherboard ID
motherboard_id = wmi_obj.Win32_BaseBoard()[0].SerialNumber.strip()

# Get hard drive ID
hard_drive_id = ''
for drive in wmi_obj.Win32_DiskDrive():
    if "fixed" in drive.MediaType.lower():
        hard_drive_id = drive.SerialNumber.strip()
        break

# Get network adapter ID
network_adapter_id = ''
for adapter in wmi_obj.Win32_NetworkAdapter():
    if adapter.MACAddress is not None:
        network_adapter_id = adapter.MACAddress.replace(':', '').strip()
        break

# Combine the IDs to create a unique hardware ID
hwid = f"{processor_id}-{motherboard_id}-{hard_drive_id}-{network_adapter_id}"

# Hash the HWID to generate a 32-character string
hwid_hash = hashlib.sha256(hwid.encode()).hexdigest()

# Split the hash into four parts and join with hyphens
hwid_parts = [hwid_hash[i:i+8] for i in range(0, 32, 8)]
hwid_final = '-'.join(hwid_parts)

print(hwid_final)
