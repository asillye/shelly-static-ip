import threading
import traceback
import logging
import requests
from json.decoder import JSONDecodeError
from ping3 import ping

logging.basicConfig(level=logging.INFO)

GATEWAY_IP = "192.168.100.1"
STATIC_IP_MIN = 200
STATIC_IP_MAX = 254

lastDot = GATEWAY_IP.rfind(".")
ipAddressBase = GATEWAY_IP[0:lastDot+1]
threadLock = threading.Lock()
availableForStaticIp = []
dchpNeedToReconfigure = []

def registerShellyFound(outputFile, ip, mac = "", type = "", ipv4_method ="", name = ""):
    threadLock.acquire()
    try:
        outputFile.write(ip + '\t' + mac + '\t' + type + '\t' + ipv4_method + '\t' + str(name) + '\n')
        if ipv4_method == "dhcp":
            dchpNeedToReconfigure.append(ip)
    finally:
        threadLock.release()

def detectDevice(ipLast):
    ip = ipAddressBase + str(ipLast)
    if STATIC_IP_MIN < ipLast & ipLast < STATIC_IP_MAX:
        logging.debug('No Shelly on IP %s, pinging IP to check availability...', ip)
        pingResult = ping(ip)
        if pingResult == False:
            logging.debug("No device on IP %s, registering as available static IP", ip)
            availableForStaticIp.append(ipLast)
        else:
            logging.debug('Network device detected on IP %s, ping in %f sec.', ip, pingResult)
            return

def detectShelly(ipLast, outputFile):
    try:
        ip = ipAddressBase + str(ipLast)
        logging.debug('Checking for Shelly at IP %s...', ip)
        url = "http://" + ip + "/settings"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            detectDevice(ipLast)
            return

        json = response.json()

        device = json["device"]
        cloud = json["cloud"]
        cloud_enabled = cloud["enabled"]
        name = json["name"]
        mac = device["mac"]
        type = device["type"]
        wifi_sta = json["wifi_sta"]
        ipv4_method = wifi_sta["ipv4_method"]

        logging.info("Found: ip=%s, mac=%s, type=%s, name=%s, cloud=%d, ipv4_method=%s", ip, mac, type, name, cloud_enabled, ipv4_method)
        registerShellyFound(outputFile, ip, mac, type, ipv4_method, name)
    except JSONDecodeError:
        return
    except AttributeError:
        return
    except requests.ConnectionError as error:
        detectDevice(ipLast)
        return

def configureStaticIp(currentIp, newIp, gatewayIp):
    try:
        # example: http://192.168.100.165/settings/sta?ipv4_method=static&ip=192.168.100.208&netmask=255.255.255.0&gateway=192.168.100.1
        logging.info("Reconfiguring Shelly with DHCP on IP %s to new IP %s with gateway %s", currentIp, newIp, gatewayIp)
        url = "http://" + currentIp + "/settings/sta?ipv4_method=static&ip=" + newIp + "&netmask=255.255.255.0&gateway=" + gatewayIp
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            logging.error("Error reconfiguring %s error code %d", currentIp, response.status_code)
            return
    except Exception as e:
        logging.error(traceback.format_exc())
        return


def scanForShellys():
    ipTableFile = open("shelly-ip-table.txt", "w", encoding="utf-8")
    threads = []

    for c in range(2, 254):
        t = threading.Thread(target=detectShelly, args=(c, ipTableFile))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    ipTableFile.close()
    availableForStaticIp.sort()
    dchpNeedToReconfigure.sort()
    

def reconfigureDhcpShellys():
    for ipToReconfigure in dchpNeedToReconfigure:
        if availableForStaticIp.count == 0:
            logging.error("No more static IP slot available for %s. Stopping.", ipToReconfigure)
            break

        staticIpLast = availableForStaticIp.pop(0)
        staticIp = ipAddressBase + str(staticIpLast)
        configureStaticIp(ipToReconfigure, staticIp, GATEWAY_IP)


scanForShellys()
reconfigureDhcpShellys()