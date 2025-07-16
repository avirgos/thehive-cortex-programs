#!/usr/bin/env python3

import json
import requests
import pytz
from datetime import datetime, timedelta

# Microsoft Graph Security API URL
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/security"
# TheHive API instance URL
THEHIVE_API_URL = "https://<thehive>/api/v1"
# path to the configuration file
CONFIG_FILE_PATH = "<config-file-path>"

def load_config():
    """
    Load configuration from a JSON file.

    Returns:
        dict: The configuration data.
    """
    with open(CONFIG_FILE_PATH, "r") as config_file:
        config = json.load(config_file)

    return config

def define_proxies(config):
    """
    Define proxy settings from the configuration.

    Args:
        config (dict): The configuration data.

    Returns:
        dict: The proxy settings.
    """
    proxies = {
        "http": config["proxy"]["url"],
        "https": config["proxy"]["url"]
    }

    return proxies

def get_aad_token(config, proxies):
    """
    Obtain an Azure AD access token.

    Args:
        config (dict): The configuration data.
        proxies (dict): The proxy settings.

    Returns:
        str: The Azure AD access token.
    """
    url = f"https://login.microsoftonline.com/{config['azure_ad']['tenant_id']}/oauth2/token"
    
    token_data = {
        "grant_type": "client_credentials",
        "client_id": config["azure_ad"]["client_id"],
        "client_secret": config["azure_ad"]["client_secret"],
        "resource": config["azure_ad"]["resource"]
    }

    token_response = requests.post(url, data=token_data, proxies=proxies, verify=False)
    aad_token = token_response.json().get("access_token")
    
    return aad_token

def get_alerts(proxies, aad_token):
    """
    Retrieve security alerts from the Microsoft Graph API.

    Args:
        proxies (dict): The proxy settings.
        aad_token (str): The Azure AD access token.

    Returns:
        dict: The security alerts data.
    """
    time, timezone = get_time_timezone()
    url = f"{GRAPH_API_URL}/alerts_v2?$filter=createdDateTime ge {time}%2B{timezone}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aad_token}"
    }
    
    response = requests.get(url, headers=headers, proxies=proxies, verify=False)
    data = response.json() if response.status_code == 200 else None

    return data

def get_alerts_updated(proxies, aad_token):
    """
    Retrieve updated security alerts from the Microsoft Graph API.

    Args:
        proxies (dict): The proxy settings.
        aad_token (str): The Azure AD access token.

    Returns:
        dict: The updated security alerts data.
    """
    time, timezone = get_time_timezone()
    url = f"{GRAPH_API_URL}/alerts_v2?$filter=createdDateTime le {time}%2B{timezone} and lastUpdateDateTime ge {time}%2B{timezone}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aad_token}"
    }
    
    response = requests.get(url, headers=headers, proxies=proxies, verify=False)
    data = response.json() if response.status_code == 200 else None

    return data

def severity_to_thehive(alert_severity):
    """
    Convert alert severity to a format compatible with TheHive.

    Args:
        alert_severity (str): The alert severity level.

    Returns:
        int: The severity level as an integer.
    """
    severity_mapping = {
        "low": 1,
        "informational": 1,
        "medium": 2,
        "high": 4
    }

    return severity_mapping.get(alert_severity.lower(), 2)

def create_observable(observable_type, observable_data, observable_desc, observable_tags):
    """
    Create an observable for TheHive.

    Args:
        observable_type (str): The type of the observable.
        observable_data (str): The data of the observable.
        observable_desc (str): The description of the observable.
        observable_tags (list): The tags of the observable.

    Returns:
        dict: The observable data.
    """
    list_observable_types_managed = ["hostname", "account", "hash", "process", "ip", "url"]
    
    if observable_type in list_observable_types_managed:
        observable = {
            "dataType": observable_type,
            "data": observable_data,
            "message": observable_desc,
            "tags": observable_tags,
            "tlp": 2
        }
        return observable
    
    return None

def create_alert(config, alert):
    """
    Create an alert in TheHive from Microsoft alert data.

    Args:
        config (dict): The configuration data.
        alert (dict): The alert data.
    """
    url = f"{THEHIVE_API_URL}/alert"

    headers = {
        "Authorization": f"Bearer {config['thehive']['api_key']}",
        "Content-Type": "application/json"
    }

    list_observables = []

    if alert["evidence"]:
        for observable in alert["evidence"]:
            observable_type, observable_data, observable_desc = None, None, ""
            if "deviceEvidence" in observable["@odata.type"] and observable["deviceDnsName"]:
                observable_type, observable_data = "hostname", observable["deviceDnsName"]
            elif "userEvidence" in observable["@odata.type"] and observable["userAccount"]["accountName"]:
                observable_type, observable_data = "account", observable["userAccount"]["accountName"]
            elif "fileEvidence" in observable["@odata.type"] and observable["fileDetails"]["sha256"]:
                observable_type, observable_data = "hash", observable["fileDetails"]["sha256"]
                if observable["fileDetails"]["fileName"]:
                    observable_desc = f"**filename** - {observable['fileDetails']['fileName']}"
            elif "processEvidence" in observable["@odata.type"] and observable["processCommandLine"]:
                observable_type, observable_data = "process", observable["processCommandLine"]
                if observable["imageFile"] and observable["parentProcessImageFile"]:
                    observable_desc = (f"**imageFile** - {observable['imageFile']['fileName']} ({observable['imageFile']['filePath']})\n"
                                       f"**parentProcessImageFile** - {observable['parentProcessImageFile']['fileName']} ({observable['parentProcessImageFile']['filePath']})")
            elif "ipEvidence" in observable["@odata.type"] and observable["ipAddress"]:
                observable_type, observable_data = "ip", observable["ipAddress"]
            elif "urlEvidence" in observable["@odata.type"] and observable["url"]:
                observable_type, observable_data = "url", observable["url"]

            if observable_type and observable_data:
                observable_created = create_observable(observable_type, observable_data, observable_desc, observable["tags"])
                list_observables.append(observable_created)

    payload_thehive = json.dumps({
        "type": "alert",
        "source": alert["productName"],
        "sourceRef": alert["id"],
        "title": alert["title"],
        "description": f"{alert['description']}\n{alert['alertWebUrl']}",
        "severity": severity_to_thehive(alert["severity"]),
        "tlp": 2,
        "observables": list_observables,
        "customFields": {
            "mdealertid": alert["id"],
            "mdeincidentnumber": alert["incidentId"],
            "incidenturl": f"https://security.microsoft.com/alerts/{alert['incidentId']}"
        }
    })

    requests.post(url, headers=headers, data=payload_thehive, verify=False)

def update_alert(config, alert):
    """
    Update an existing alert in TheHive.

    Args:
        config (dict): The configuration data.
        alert (dict): The alert data.
    """
    url_search = f"{THEHIVE_API_URL}/query"

    headers = {
        "Authorization": f"Bearer {config['thehive']['api_key']}",
        "Content-Type": "application/json"
    }

    payload_search = json.dumps({
        "query": [
            {"_name": "listAlert"},
            {
                "_name": "filter",
                "_eq": {
                    "_field": "sourceRef",
                    "_value": alert["id"]
                }
            }
        ]
    })
    response = requests.post(url_search, headers=headers, data=payload_search, verify=False)
    response = json.loads(response.text)

    if response:
        payload_thehive = json.dumps({
            "description": f"{response[0]['description']}\n|\n**[Automatically Resolved in EDR]**",
            "tags": response[0]["tags"] or ["EDR:Resolved"]
        })
        url = f"{THEHIVE_API_URL}/alert/{response[0]['_id']}"
        if alert['status'] == "resolved":
            requests.patch(url, headers=headers, data=payload_thehive, verify=False)

def get_time_timezone():
    """
    Get the current time and timezone.

    Returns:
        tuple: The current time and timezone.
    """
    timezone = pytz.timezone("Europe/Paris")
    # get the current time in the specified timezone and subtract 2 minutes to account for potential delays
    now = datetime.now(timezone) - timedelta(minutes=2)
    start_search_date = now.isoformat()
    time, timezone = start_search_date.split('+')

    return time, timezone

if __name__ == "__main__":
    """Main program."""
    config = load_config()
    proxies = define_proxies(config)
    aad_token = get_aad_token(config, proxies)

    if aad_token:
        alerts = get_alerts(proxies, aad_token)
        alerts_updated = get_alerts_updated(proxies, aad_token)

        # create new alerts in TheHive for each alert retrieved from Microsoft Graph API
        if alerts and alerts["value"]:
            for alert in alerts["value"]:
                create_alert(config, alert)

        # update existing alerts in TheHive for each updated alert retrieved from Microsoft Graph API
        if alerts_updated and alerts_updated["value"]:
            for alert_updated in alerts_updated["value"]:
                update_alert(config, alert_updated)