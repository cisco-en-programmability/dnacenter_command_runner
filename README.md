# Cisco DNA Center Path Trace


This Python script will execute a CLI command on a Cisco DNA Center managed device

**Cisco Products & Services:**

- Cisco DNA Center

**Tools & Frameworks:**

- Python environment

**Usage**

This sample script will execute one CLI command {command} on the device {device_hostname}:

    - obtain a Cisco DNA Center auth token
    - retrieve the list of commands keywords supported by Cisco DNA Center
    - identify if the command is supported
    - execute the command on the specified device
    - retrieve the file with the command output
    
- $ python command_runner.py "command" "device_hostname"
Example:
python3 command_runner.py "show run int gi0/0" "PDX-9300"

- Sample Output:

The command "show run int gi0/0" is supported

The command output from the device: PDX-9300

 show run int gi0/0
Building configuration...

Current configuration : 185 bytes
!
interface GigabitEthernet0/0
 description connected to LKO2-RU6-R10-TOR3650 Gi1/0/4
 vrf forwarding Mgmt-vrf
 ip address 10.93.130.24 255.255.255.0
 speed 1000
 negotiation auto
end

PDX-9300#


End of Application "command_runner.py" Run

**License**

This project is licensed to you under the terms of the [Cisco Sample Code License](./LICENSE).
