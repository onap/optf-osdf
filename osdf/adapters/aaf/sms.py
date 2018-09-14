#
# -------------------------------------------------------------------------
#   Copyright (c) 2018 Intel Corporation Intellectual Property
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# -------------------------------------------------------------------------
#

'''Secret Management Service Integration'''

from onapsmsclient import Client

import osdf.config.loader as config_loader
from osdf.config.base import osdf_config
from osdf.logging.osdf_logging import debug_log

config_spec = {
    "preload_secrets": "config/preload_secrets.yaml"
}

secret_cache = {}


def preload_secrets():
    """ This is intended to load the secrets required for testing Application
        Actual deployment will have a preload script. Make sure the config is
        in sync"""
    preload_config = config_loader.load_config_file(
        config_spec.get("preload_secrets"))
    domain = preload_config.get("domain")
    config = osdf_config.deployment
    sms_url = config["aaf_sms_url"]
    timeout = config["aaf_sms_timeout"]
    cacert = config["aaf_ca_certs"]
    sms_client = Client(url=sms_url, timeout=timeout, cacert=cacert)
    domain = sms_client.createDomain(domain)
    config["secret_domain"] = domain  # uuid
    secrets = preload_config.get("secrets")
    for secret in secrets:
        sms_client.storeSecret(domain, secret.get('name'),
                               secret.get('values'))
    debug_log.debug("Preload secrets complete")


def retrieve_secrets():
    """Get all secrets under the domain name"""
    secret_dict = dict()
    config = osdf_config.deployment
    sms_url = config["aaf_sms_url"]
    timeout = config["aaf_sms_timeout"]
    cacert = config["aaf_ca_certs"]
    domain = config["secret_domain"]
    sms_client = Client(url=sms_url, timeout=timeout, cacert=cacert)
    secrets = sms_client.getSecretNames(domain)
    for secret in secrets:
        values = sms_client.getSecret(domain, secret)
        secret_dict[secret] = values
    debug_log.debug("Secret Dictionary Retrieval Success")
    return secret_dict


def delete_secrets():
    """ This is intended to delete the secrets for a clean initialization for
        testing Application. Actual deployment will have a preload script.
        Make sure the config is in sync"""
    config = osdf_config.deployment
    sms_url = config["aaf_sms_url"]
    timeout = config["aaf_sms_timeout"]
    cacert = config["aaf_ca_certs"]
    domain = config["secret_domain"]
    sms_client = Client(url=sms_url, timeout=timeout, cacert=cacert)
    ret_val = sms_client.deleteDomain(domain)
    debug_log.debug("Clean up complete")
    return ret_val


if __name__ == "__main__":
    # Initialize Secrets from SMS
    preload_secrets()

    # Retrieve Secrets from SMS and load to secret cache
    # Use the secret_cache instead of config files
    secret_cache = retrieve_secrets()

    # Clean up Delete secrets and domain
    delete_secrets()
