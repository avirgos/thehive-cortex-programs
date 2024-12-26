# send-SMS

## Overview

Cortex responder to send an SMS if a High or Critical TheHive alert has been created.

![cortex-responder](assets/img/cortex-responder.png)

The SMS is sent using the `send-SMS.pl` script. The SMS messages are in the following format :

```
[On-call duty]
TheHive alert { <severity> } : <alert-title>

https://<thehive-url>/alerts/<alert-id>/details
```

## Configuration

### Variables

In the Python program `send-SMS.py`, change this variables :

![variables-to-modify](assets/img/variables-to-modify.png)

- **\<sms-phone-number>** - Phone number to which the SMS will be sent
- **\<thehive-url>** - URL of your TheHive platform

Note : you can also customize the SMS message format modifying `sms_text` variable.

### Execution mode

Responder triggering should be configured automatically.

On your TheHive platform, go to "**Organization**" > "**\<organization-name>**" > "**Notifications**" menu and create a notification named "Send SMS". You must add the following data shown in the screenshot below :

![thehive-notification](assets/img/thehive-notification.png)