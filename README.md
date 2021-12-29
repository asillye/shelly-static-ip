![image](https://user-images.githubusercontent.com/946782/147704579-4d1b65c0-2204-4ac6-b7ca-153057bd1bef.png)

# Script for setting static IPs to Shelly devices

Reconfigure masses of Shelly devices to static IP. This is useful, if you want to set up your Shelly (https://shelly.cloud/) devices to use static IP addresses on your home network - so next time, if you look for them, they will be on the same address.

Yes - the DHCP servers can be configured to give the same IP for a MAC address, but configuring that is more complex than just running this script and store the IPs in the Shelly devices.

This script will scan your full local network for Shelly devices and if any of them are in DHCP mode, it will automatically pick a static IP address and assign it to them. 

At the end, all DHCP Shelly devices will be reconfigured to a unique static IP.

The script assumes a simple home network setup with 255.255.255.0 netmask. Scanning is done on the last number from 2 to 254.

# Prerequisites
Install Python 3

Install required packages with
```
pip install -r requirements.txt
```

# Configuration
There are no command line arguments, please modify the script directly.

## GATEWAY_IP - Your Gateway IP
Your home router address. This will be used to determine the subnet to scan and also this will be configured to all Shelly devices as a gateway.
```
GATEWAY_IP = "192.168.100.1"
```
The above setting will scan the ```192.168.100.2``` - ```192.168.100.254``` range for Shelly devices.

## STATIC_IP_MIN, STATIC_IP_MAX: Static IP address range to use
Range of the static IPs available to use in the same subnet.

At home I've set up the router to assign DHCP addresses only in the range of 100-199, to above 200 all IPs are available for static IPs.
```
STATIC_IP_MIN = 200
STATIC_IP_MAX = 254
```

# Running

```
python ./shelly-static-ip.py
```
The script will run in two passes:

In the first pass with ```scanForShellys``` function floods the network with simple http requests and look for the Shelly ```/settings``` API. 

If any meaningful response comes the script registers the device data and also saves into the ```shelly-ip-table.txt``` file.

If no response comes, the script tries to PING the host and check for any network device there. 

If there was no answer, it registers it as an available static IP (if there is a ping answer, it will skip that IP from the available static addresses).

I added some basic multi threading, as it was quite slow sequentially, so the resuld order will be random.

```
INFO:root:Found: ip=192.168.100.202, mac=40F5202D3506, type=SHSW-1, name=Emeleti közlekedő lámpa, cloud=1, ipv4_method=static
INFO:root:Found: ip=192.168.100.201, mac=40F5202D6287, type=SHSW-1, name=Lépcső lámpa, cloud=1, ipv4_method=static
INFO:root:Found: ip=192.168.100.204, mac=8CAAB54807F7, type=SHSW-1, name=Garázs Lámpa, cloud=1, ipv4_method=static
INFO:root:Found: ip=192.168.100.209, mac=C45BBE75F386, type=SHSW-1, name=None, cloud=1, ipv4_method=static
INFO:root:Found: ip=192.168.100.212, mac=E868E7C571E3, type=SHPLG-S, name=None, cloud=1, ipv4_method=static
```

In the second pass with ```reconfigureShellys``` function, the script goes though sequentially all Shelly devices with DHCP and changes it to an automatically picked static IP. It picks the next available IP based on the first pass.

```
INFO:root:Reconfiguring Shelly with DHCP on IP 192.168.100.166 to new IP 192.168.100.212 with gateway 192.168.100.1
```

