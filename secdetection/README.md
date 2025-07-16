# secdetection

## Overview

Python script to create and update alerts in TheHive based on Microsoft Graph Security alerts.

## Prerequisites

```bash
pip install -r requirements.txt
```

- Azure AD service account with Microsoft Graph API access and permissions to retrieve security alerts : `SecurityEvents.Read.All`, `SecurityEvents.ReadWrite.All`
- TheHive API key of your service account
- Proxy settings (optional)

## Usage

To use the `secdetection` Python script, you need to copy the `config-template.json` and rename it to `config.json` using this command :

```bash
cp config-template.json config.json
```

In `config.json` file, complete the fields :

```json
{
    "azure_ad": {
        "tenant_id": "",
        "client_id": "",
        "client_secret": "",
        "resource": ""
    },
    "proxy": {
        "url": ""
    },
    "thehive": {
        "api_key": ""
    }
}
```

In the Python script `secdetection.py`, update the following global variables :

```py
# Microsoft Graph Security API URL
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/security"
# TheHive API instance URL
THEHIVE_API_URL = "https://<thehive>/api/v1"
# path to the configuration file
CONFIG_FILE_PATH = "<config-file-path>"
```

## Configuration

### Execution mode

The Python script should be configured to run automatically at regular intervals to fetch and process new alerts.

Run the script **every minute** using a cron job :

```bash
* * * * * /usr/bin/python3 /path/to/secdetection.py
```
