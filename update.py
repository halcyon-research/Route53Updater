#!/bin/python3

# michaelpeterswa
# Route53 Updater, v1.0
# 11.14.20

import toml
import requests
import boto3
from tabulate import tabulate
from colorama import Fore, Style
from pyfiglet import Figlet
from datetime import datetime

AWS_IP_SERVICE = "http://checkip.amazonaws.com"
CONFIG = "domains.toml"
COLORS = True
LIVE = True
FANCY = True
VERBOSE = True

names = []
ids = []
records = []
matches = []


def title(time):
    if FANCY:
        f = Figlet(font="slant")
        print(f.renderText("R53 U"), end="")
        print(time)
    else:
        print("\nRoute53 Updater, by michaelpeterswa")
        print(time)


def green(text):
    if COLORS:
        print(Fore.GREEN + text)
    else:
        print(text)


def yellow(text):
    if COLORS:
        print(Fore.YELLOW + text)
    else:
        print(text)


def red(text):
    if COLORS:
        print(Fore.RED + text)
    else:
        print(text)


def reset():
    if COLORS:
        print(Style.RESET_ALL)
    else:
        print()


def update_record(zone_id, name, ip):
    subd = "*." + name
    batch = {
        "Comment": "Changed by update.py",
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": name,
                    "Type": "A",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": ip}],
                },
            },
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": subd,
                    "Type": "A",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": ip}],
                },
            },
        ],
    }
    response = client.change_resource_record_sets(
        HostedZoneId=zone_id, ChangeBatch=batch
    )

    return response


def groupHostedZones():
    for z in resp["HostedZones"]:
        names.append(z["Name"][:-1])  # trim trailing .
        ids.append(z["Id"])
        records.append((z["Name"][:-1], z["Id"]))


def printTitle(time):
    if COLORS:
        print(Fore.YELLOW)
    title(time)


def printRoute53Records():
    yellow("")
    print("Route53 Records:\n")
    print(tabulate({"Name": names, "ID": ids}, headers="keys"))
    reset()


def generateRoute53Matches():
    for link, ID in records:
        if link in data["domains"]:
            matches.append((link, ID))


def printRoute53Matches():
    for link, ID in records:
        if link in data["domains"]:
            green("✔ found domain match: " + link)
        else:
            red("✗ " + link + " was found on Route53 but not in domains")
    reset()


def updateMatchesOnRoute53(ip):
    for match in matches:
        r53response = update_record(match[1], match[0], ip)
    return r53response


def printUpdatesOnRoute53(r53response):
    for match in matches:
        if r53response["ChangeInfo"]["Status"] == "PENDING":
            yellow("PENDING (" + ip + "): " + match[0])
        else:
            pass
    reset()


def saveTOML(data, ip, time):
    data["ip"] = ip
    data["time"] = time
    with open(CONFIG, "w") as f:
        toml.dump(data, f)


def checkPrevIP(ip, prev_ip):
    if ip == prev_ip:
        return True
    else:
        return False


if __name__ == "__main__":
    data = toml.load(CONFIG)
    client = boto3.client("route53")
    resp = client.list_hosted_zones()
    ip = requests.get(AWS_IP_SERVICE).text.strip()
    curr_time = datetime.now().isoformat()
    prev_ip = data["ip"]

    printTitle(curr_time)

    if not checkPrevIP(ip, prev_ip):

        groupHostedZones()
        generateRoute53Matches()
        if VERBOSE:
            printRoute53Records()
            printRoute53Matches()
        else:
            print()

        saveTOML(data, ip, curr_time)
        if LIVE:
            printUpdatesOnRoute53(updateMatchesOnRoute53(ip), ip)
        else:
            yellow("testing mode")
            reset()
    else:
        yellow("\nprevious IP match, SKIPPING")
        reset()
