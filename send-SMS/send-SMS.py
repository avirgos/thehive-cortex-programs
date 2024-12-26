#!/usr/bin/env python3

from cortexutils.responder import Responder
import subprocess
import os

class SendSMS(Responder):
    def __init__(self):
        """Initialize a SendSMS responder."""
        Responder.__init__(self)

    def run(self):
        """Run a SendSMS responder."""
        Responder.run(self)

        alert_title = self.get_param("data.title", None, "Title not provided.")
        alert_severity = self.get_param("data.severity", None, "Severity not provided.")
        alert_id = self.get_param("data.id", None, "ID not provided.")
        alert_status = self.get_param("data.status", None, "Status not provided.")

        # ignore alerts that are not of High or Critical severity
        if alert_status == "Ignored" or "Ignore" in alert_title or alert_title == "Connection attempt over HTTP to a deceptive host" or alert_severity <= 2:
            self.report({"status": "Alert ignored, SMS not sent."})
            return

        alert_severity = self.severity_int_to_str(alert_severity)

        ##########################
        # To be modified by user #
        ##########################
        sms_phone_number = "<sms-phone-number>"
        thehive_url = "<thehive-url>"
        
        sms_text = "[On-call duty] " + "\n" + "TheHive alert { " + alert_severity + " } : " + alert_title + "\n\n" + "https://" + thehive_url + "/alerts/" + alert_id + "/details"

        if sms_phone_number and sms_text:
            result = self.send_sms(sms_phone_number, sms_text)

            if result:
                self.report({"status": "SMS sent successfully !"})
            else:
                self.error("Failed to send SMS.")
        else:
            self.error("SMS number or text not provided.")

    def severity_int_to_str(self, alert_severity):
        """
        Convert severity integer to string representation.

        Args:
            alert_severity (int): The severity level as an integer.

        Returns:
            str: The string representation of the severity level.
        """
        severity_mapping = {
            1: "Faible",
            2: "Moyenne",
            3: "Élevée",
            4: "Critique"
        }

        return severity_mapping.get(alert_severity, "Unknown")

    def send_sms(self, number, text):
        """
        Call the perl script to send an SMS.

        Args:
            number (str): The phone number to send the SMS to.
            text (str): The text content of the SMS.

        Returns:
            bool: True if the SMS was sent successfully, False otherwise.
        """
        try:
            script_path = "Send-SMS/send-SMS.pl"

            if not os.path.isfile(script_path):
                self.error(f"Script {script_path} not found.")
                return False

            command = ["/usr/bin/perl", script_path, number, text]
            completed_process = subprocess.run(command, capture_output=True, text=True)

            if completed_process.returncode == 0:
                return True
            else:
                self.error(f"Script returned Error Code {completed_process.returncode} + {completed_process.stdout}")
                return False
        except Exception as e:
            self.error(str(e))
            return False

if __name__ == "__main__":
    """Main program."""
    SendSMS().run()