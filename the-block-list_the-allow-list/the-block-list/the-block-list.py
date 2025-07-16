#!/usr/bin/env python3

from cortexutils.responder import Responder
import os
import requests
import json

# TheHive API instance URL
THEHIVE_API_URL = "https://<thehive>/api/v1"
# Forcepoint Policy Server API URL
FORCEPOINT_API_URL = "https://<policy-server>:15873/api/web/v1/categories"

class TheBlockList(Responder):
    def __init__(self):
        """Initialize a The-Block-List responder.
        """
        Responder.__init__(self)

        ##########
        # Global #
        ##########
        self.proxies = {
            "http": "",
            "https": "",
        }

        ########################
        # Responder parameters #
        ########################
        # TheHive
        self.api_key = self.get_param("config.api_key", "your_api_key", "Clé API TheHive manquante.")

        # Forcepoint
        self.fp_username = self.get_param("config.fp_username", "your_fp_username", "Forcepoint Compte Service Nom d'utilisateur manquant.")
        self.fp_password = self.get_param("config.fp_password", "your_fp_password", "Forcepoint Compte Service MDP manquant.")
        self.category_id_fp = self.get_param("config.category_id_fp", None, "Forcepoint ID de la catégorie concernant la liste des URLs bloquées.")

        ###########
        # TheHive #
        ###########
        self.payload_thehive = {}
        self.headers_thehive = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

    def block_data_fp(self, data_to_block):
        """
        Adds a URL or a domain name to the Forcepoint block list within a specific category.

        Args:
           data_to_block (str): The data to be blocked via Forcepoint.

        Returns:
            int: 0 if the operation succeeded (commit successful), 1 otherwise (failure).
        """
        category_id = int(self.category_id_fp)

        # start transaction
        transaction = requests.post(
            f"{FORCEPOINT_API_URL}/start",
            auth=(self.fp_username, self.fp_password),
            proxies=self.proxies,
            verify=False,
            timeout=10
        )
        transaction_id = transaction.json().get("Transaction ID")

        # add URL or domain name
        add_data = {
            "Transaction ID": transaction_id,
            "Category ID": category_id,
            "URLs": [data_to_block],
            "IPs": ""
        }

        # file creation
        filename = 'add_data.json'
        with open(filename, 'w') as f:
            json.dump(add_data, f, indent=2)
        with open(filename, 'r') as f:
            data = f.read()
            requests.post(
                f"{FORCEPOINT_API_URL}/urls",
                auth=(self.fp_username, self.fp_password),
                data=data,
                proxies=self.proxies,
                verify=False,
                timeout=10
            )
        os.remove(filename)

        # commit
        commit = requests.post(
            f"{FORCEPOINT_API_URL}/commit?transactionid={transaction_id}",
            auth=(self.fp_username, self.fp_password),
            proxies=self.proxies,
            verify=False,
            timeout=10
        )

        return 0 if commit.status_code == 200 else 1

    def add_info_observable(self, observable_id, observable_tags):
        """
        Add a tag to the observable in TheHive if the URL or the domain name is blocked.

        Args:
            observable_id (str): The ID of the observable to update.
            observable_tags (list): The current list of tags for the observable.
        """
        observable_tags.append("Blocked : Forcepoint")

        url_info_observable = THEHIVE_API_URL + "/observable/" + observable_id

        payload = json.dumps({
            "tags": observable_tags
        })

        requests.patch(url_info_observable, headers=self.headers_thehive, data=payload, proxies=self.proxies, verify=False, timeout=10)

    def run(self):
        """Run a The-Block-List responder.
        """
        Responder.run(self)

        if self.get_param("data.dataType") == "url" or self.get_param("data.dataType") == "domain":
            observable_id = self.get_param("data.id")
            observable_tags = self.get_param("data.tags")
            data_to_block = self.get_param("data.data")

            ##############
            # Forcepoint #
            ##############
            if "Blocked : Forcepoint" not in observable_tags:
                response_block_data_fp = self.block_data_fp(data_to_block)

                if response_block_data_fp == 0:
                    self.add_info_observable(observable_id, observable_tags)
                    self.report({"message": "Blocked in Forcepoint."})
                else:
                    self.report({"message": "Wasn't blocked in Forcepoint. An error occured. Exit."})
                    return
            else:
                self.report({"message": "Already blocked in Forcepoint."})
        else:
            self.report({"message": "The data must be an URL or a domain name."})

if __name__ == "__main__":
    """Main program.
    """
    TheBlockList().run()