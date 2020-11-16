# michaelpeterswa
# Route53 Updater, v1.0
# 11.14.20

from toml import load
import requests
import boto3
from tabulate import tabulate
from colorama import Fore, Style
from pyfiglet import Figlet
from datetime import datetime

AWS_IP_SERVICE = "http://checkip.amazonaws.com"
COLORS = True
LIVE = True
FANCY = True
VERBOSE = True

data = load("domains.toml")
client = boto3.client("route53")
resp = client.list_hosted_zones()


def title(fancy):
    if fancy:
        f = Figlet(font="slant")
        print(f.renderText("R53 U"), end="")
        print(datetime.now().isoformat() + "\n")
    else:
        print("Route53 Updater, by michaelpeterswa")
        print(datetime.now().isoformat() + "\n")


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


names = []
ids = []
records = []
for z in resp["HostedZones"]:
    names.append(z["Name"][:-1])  # trim trailing .
    ids.append(z["Id"])
    records.append((z["Name"][:-1], z["Id"]))

yellow("")
title(FANCY)

if VERBOSE:
    print("Route53 Records:\n")
    print(tabulate({"Name": names, "ID": ids}, headers="keys"))
    reset()

ip = requests.get(AWS_IP_SERVICE).text.strip()

matches = []
for link, ID in records:
    if link in data["domains"]:
        matches.append((link, ID))
        if VERBOSE:
            green("✔ found domain match: " + link)
    else:
        if VERBOSE:
            red("✗ " + link + " was found on Route53 but not in domains")
if VERBOSE:
    print()

for match in matches:
    if LIVE:
        resp = update_record(match[1], match[0], ip)
        if VERBOSE:
            if resp["ChangeInfo"]["Status"] == "PENDING":
                yellow("PENDING (" + ip + "): " + match[0])
            else:
                pass
if VERBOSE:
    reset()
