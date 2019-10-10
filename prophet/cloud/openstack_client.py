# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).)

"""OpenStack client implementation based on requests module"""

from functools import wraps
import logging
import json
import six

from requests import ConnectionError

from errors import CatalogNotFound, \
    ConnectOpenStackError, HttpUnauthorized, IllegalArgumentError, \
    ParserCatalogError, ProjectIdNotFound, TokenNotFound
from http_request import HttpRequest as req

ALLOW_AUTH_VERSIONS = ["v2.0", "v3"]
ALLOW_ENDPOINT = "public"

# OpenStack endpoint versions
COMPUTE_SERVICE = "compute"
IMAGE_SERVICE = "image"
IMAGE_SERVICE_VERSION = "v2"
NETWORK_SERVICE = "network"
NETWORK_SERVICE_VERSION = "v2.0"
VOLUME_SERVICE = "volumev2"

DEFAULT_REGION = "RegionOne"
DEFAULT_DOMAIN = "default"

HEADERS = {"Content-Type": "application/json"}
IDENTITY_V3_TOKEN_FIELD = "X-Subject-Token"
TOKEN_VARY_FIELD = "X-Auth-Token"
TOKEN_LOCAL_FILE = "./openstack_token_cache"


# Decorator define
def token_expired(func):
    """set token to None if token is expired"""
    @wraps(func)
    def token_expired_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except HttpUnauthorized:
            logging.warn("Token expired, trying to get fresh token ...")
            # NOTE(Zhao Jianbo): Authentication info
            # need to set to None or update
            self._auth_resp_headers = None
            self._auth_resp_body = None
            self._catalogs = None
            self._endpoints = None
            self._compute_url = None
            self._volume_url = None
            self._image_url = None
            self._network_url = None
            self._project_id = None
            self._neutron_enabled = None
            self._token = self._get_token()
            self._set_token_into_local(self._token)
            kwargs.update(headers={TOKEN_VARY_FIELD: self.token})
            return func(self, *args, **kwargs)
    return token_expired_wrapper


def token_required(func):
    """Add token into headers"""
    @wraps(func)
    def token_required_wrapper(self, *args, **kwargs):
        kwargs.update(headers={TOKEN_VARY_FIELD: self.token})
        return func(self, *args, **kwargs)
    return token_required_wrapper


class OpenStackClient(object):

    def __init__(self,
                 os_username=None,
                 os_password=None,
                 os_project_name=None,
                 os_auth_url=None,
                 os_region_name=DEFAULT_REGION,
                 os_domain_name=DEFAULT_DOMAIN,
                 compute_service=COMPUTE_SERVICE,
                 image_service=IMAGE_SERVICE,
                 volume_service=VOLUME_SERVICE,
                 network_service=NETWORK_SERVICE,
                 image_service_version=IMAGE_SERVICE_VERSION,
                 network_service_version=NETWORK_SERVICE_VERSION,
                 allow_endpoint=ALLOW_ENDPOINT,
                 allow_auth_versions=ALLOW_AUTH_VERSIONS,
                 host_mapping={},
                 **kwargs):
        """Initialization method to connect OpenStack

        :param os_username: <string>, OpenStack username
        :param os_password: <string>, OpenStack password
        :param os_project_name: <string>, OpenStack project name
        :param os_auth_url: <string>, OpenStack auth url,
            eg: http://192.168.10.201:5000/v3
        :param os_region_name: <string>, OpenStack region name
        :param os_domain_name: <string>, OpenStack domain name
        :param compute_service: <string>, OpenStack compute service name
        :param image_service: <string>, OpenStack image service name
        :param volume_service: <string>, OpenStack volume service name
        :param network_service: <string>, OpenStack network service name
        :param image_service_version: <string>, OpenStack image
            service version
        :param network_service_version: <string>, OpenStack network
            service version
        :param host_mapping: <dict>, mapping between domain name and ip
        """
        if not os_username and os_password and \
                os_project_name and os_auth_url:
            raise IllegalArgumentError("os_username, os_password \
                os_project_name and os_aut_url must be given")

        # add all params into self but need to remove self
        self.__dict__.update(locals())
        del self.__dict__["self"]

        self.auth_version = self._get_auth_version()

        # initialization for property
        self._auth_resp_headers = None
        self._auth_resp_body = None
        self._token = None
        self._catalogs = None
        self._endpoints = None
        self._compute_url = None
        self._volume_url = None
        self._image_url = None
        self._network_url = None
        self._project_id = None
        self._neutron_enabled = None

    @property
    def token(self):
        # if not token, get token from local
        # if the token is expired, get a new token
        try:
            self._token = self._get_token_from_local()
        except Exception as err:
            logging.warning("Can not get token from local file,"
                            "detail is %s" % err.message)
            self._token = None

        if not self._token:
            logging.warning("There is no token,"
                            " Get refresh token from openstack")
            self._token = self._get_token()
            logging.info("Successfully get token info, the token is %s, "
                         "will write it to local file" % self._token)
            self._set_token_into_local(self._token)
        return self._token

    @property
    def project_id(self):
        if not self._project_id:
            self._project_id = self._get_project_id()
        return self._project_id

    @property
    def catalogs(self):
        if not self._catalogs:
            self._catalogs = self._get_catalogs()
        return self._catalogs

    @property
    def endpoints(self):
        if not self._endpoints:
            self._endpoints = self._get_endpoints()
        return self._endpoints

    @property
    def auth_resp_body(self):
        """Authentication response body"""
        if not self._auth_resp_body:
            self._authentication()
        return self._auth_resp_body

    @property
    def auth_resp_headers(self):
        """Authentication response headers"""
        if not self._auth_resp_headers:
            self._authentication()
        return self._auth_resp_headers

    @property
    def compute_url(self):
        if not self._compute_url:
            self._compute_url = self.endpoints.get(self.compute_service, None)
            if not self._compute_url:
                raise ParserCatalogError("Get compute url failed.")
        return self._compute_url

    @property
    def volume_url(self):
        if not self._volume_url:
            self._volume_url = self.endpoints.get(self.volume_service, None)
            if not self._volume_url:
                raise ParserCatalogError("Get volume url failed.")
        return self._volume_url

    @property
    def image_url(self):
        if not self._image_url:
            self._image_url = self.endpoints.get(self.image_service, None)
            if not self._image_url:
                raise ParserCatalogError("Get image url failed.")
            url = self._image_url + "/" + self.image_service_version
            self._image_url = url
        return self._image_url

    @property
    def network_url(self):
        if not self._network_url:
            self._network_url = self.endpoints.get(self.network_service, None)
            if self._network_url:
                url = self._network_url + "/" + self.network_service_version
                self._network_url = url
        return self._network_url

    @property
    def neutron_enabled(self):
        if not self._neutron_enabled:
            self._neutron_enabled = True if self.network_url else False
            logging.info("Neutron service enabled is %s"
                         % self._neutron_enabled)
        return self._neutron_enabled

    def _authentication(self):
        action = None
        if self.auth_version == "v2":
            action = "/tokens"
            auth_body = {
                "auth": {
                    "passwordCredentials": {
                        "password": self.os_password,
                        "username": self.os_username
                    },
                    "tenantName": self.os_project_name
                }
            }

        if self.auth_version == "v3":
            action = "/auth/tokens"
            auth_body = {
                "auth": {
                    "identity": {
                        "methods": [
                            "password"
                        ],
                        "password": {
                            "user": {
                                "domain": {
                                    "id": self.os_domain_name
                                },
                                "name": self.os_username,
                                "password": self.os_password
                            }
                        }
                    },
                    "scope": {
                        "project": {
                            "domain": {
                                "id": self.os_domain_name
                            },
                            "name": self.os_project_name
                        }
                    }
                }
            }
        try:
            logging.info("Authenticating to OpenStack... ")
            resp = req.post(url=self.os_auth_url,
                            action=action,
                            payload=auth_body)
            logging.info("OpenStack authentication successfully.")
            self._auth_resp_headers = resp["header"]
            self._auth_resp_body = resp["body"]
        except HttpUnauthorized as err:
            logging.error("OpenStack authentication failed, please "
                          "check your credentials.")
            raise err
        except ConnectionError as err:
            raise ConnectOpenStackError("Can not connect to openstack "
                                        "auth url, please check os_auth_url")
        except Exception as err:
            raise err

    def _get_auth_version(self):
        """Parser version from auth url"""

        version = None
        if self.os_auth_url.endswith("/"):
            version = self.os_auth_url.split("/")[-2]
        else:
            version = self.os_auth_url.split("/")[-1]
        logging.info("Auth version string is %s" % version)

        if version not in self.allow_auth_versions:
            raise Exception("Version %s is not supported, "
                            "allow auth version is %s, "
                            "example: http://<openstack ip>:5000/v2.0,"
                            " http://<openstack ip>:5000/v3"
                            % (version, self.allow_auth_versions))
        auth_version = None
        if version == "v2.0":
            auth_version = "v2"
        elif version == "v3":
            auth_version = "v3"
        return auth_version

    def _get_catalogs(self):
        try:
            if self.auth_version == "v2":
                access = self.auth_resp_body["access"]
                return access["serviceCatalog"]
            elif self.auth_version == "v3":
                return self.auth_resp_body["token"]["catalog"]
        except Exception as err:
            logging.exception(err)
            raise CatalogNotFound("Can not find key word access "
                                  "or token from response %s"
                                  % self.auth_resp_body)

    def _get_endpoints(self):
        """Parser endpoints from catalogs

        Return example:
        {
            "service_name": "public url"
        }
        """
        try:
            if self.auth_version == "v2":
                return self._get_v2_endpoints()
            elif self.auth_version == "v3":
                return self._get_v3_endpoints()
        except Exception as err:
            logging.error("Parser catalog failed.")
            raise err

    def _get_v2_endpoints(self):
        """Parser OpenStack v2 catalog, filter by region:

           [
               {
                   "endpoints": [
                       {
                           "region": "RegionOne",
                           "publicURL": "http://..."
                           "adminURL": "http://..."
                           "internalURL": "http://..."
                           ...
                       }
                   ]
                   "type": "compute",
                   "name": "nova"
               }
           ]
        """
        endpoints = {}
        for catalog in self.catalogs:
            service_type = catalog["type"]
            logging.info("Found service %s ..." % service_type)

            for endpoint in catalog["endpoints"]:
                region = endpoint["region"]
                if region == self.os_region_name:
                    url_type = self.allow_endpoint + "URL"
                    url = endpoint.get(url_type, None)
                    if not url:
                        logging.warn("Service %s %s is not existing" % (
                                     service_type, url_type))
                    else:
                        logging.info("Service %s %s is %s." % (
                                     service_type, url_type, url))
                        endpoints[service_type] = url
                else:
                    logging.info("Skip to parser service %s belongs to "
                                 "region %s, expect region name "
                                 "is %s" % (service_type, region,
                                            self.os_region_name))
                    continue
        return endpoints

    def _get_v3_endpoints(self):
        """Parser OpenStack v3 catalog, filter by region:
        [
            {
                "endpoints": [
                    {
                        "region": "RegionOne",
                        "interface": "admin",
                        "url": "http://..."
                        ...
                    },
                    {
                        "region": "RegionOne",
                        "interface": "public",
                        "url": "http://..."
                        ...
                    }
                ]
                "type": "compute",
                "name": "nova"
            }
        ]
        """
        endpoints = {}
        for catalog in self.catalogs:
            service_type = catalog["type"]
            logging.info("Found service %s ..." % service_type)

            for endpoint in catalog["endpoints"]:
                region = endpoint.get("region", None)
                if region == self.os_region_name:
                    interface = endpoint.get("interface", None)
                    url = endpoint.get("url", None)
                    if interface == self.allow_endpoint:
                        logging.info("Service %s %s is %s." % (
                                     service_type, interface, url))
                        endpoints[service_type] = url
                else:
                    logging.info("Skip to parser service %s belongs to "
                                 "region %s, expect region name "
                                 "is %s" % (service_type, region,
                                            self.os_region_name))
                    continue
        return endpoints

    def _get_token(self):
        try:
            if self.auth_version == "v2":
                return self.auth_resp_body["access"]["token"]["id"]
            elif self.auth_version == "v3":
                return self.auth_resp_headers[IDENTITY_V3_TOKEN_FIELD]
        except Exception as e:
            logging.exception(e)
            if self.auth_version == "v2":
                raise TokenNotFound("Can not find key word access or "
                                    "token from response %s"
                                    % self.auth_resp_body)
            elif self.auth_version == "v3":
                raise TokenNotFound("Can not find key word %s in "
                                    "headers from response %s"
                                    % (IDENTITY_V3_TOKEN_FIELD,
                                       self.auth_resp_headers))

    def _get_token_from_local(self):
        logging.info("Get token and account info from local file")
        with open(TOKEN_LOCAL_FILE, "r") as f:
            res = json.loads(f.read())
            token = res.get("token")
            return token

    def _set_token_into_local(self, token):
        logging.info("Write token %s info into local file: %s"
                     % (token, TOKEN_LOCAL_FILE))
        json_auth_info = {
            "token": token
        }
        str_auth_info = json.dumps(json_auth_info)
        with open(TOKEN_LOCAL_FILE, "w") as f:
            f.write(str_auth_info)

    def _get_project_id(self):
        try:
            if self.auth_version == "v2":
                token_info = self.auth_resp_body["access"]["token"]
                return token_info["tenant"]["id"]
            elif self.auth_version == "v3":
                token_info = self.auth_resp_body["token"]
                return token_info["project"]["id"]
        except Exception as e:
            logging.exception(e)
            raise ProjectIdNotFound("Can not find key word tenant or "
                                    "project from response %s"
                                    % (self.auth_resp_body))

    # NOTE(Ray): List methods to get resource list from OpenStack, add
    # new methods under this section, order by letter alpha
    @token_required
    @token_expired
    def list_instance_attachments(self, inst_id, **kwargs):
        try:
            return req.get(url=self.compute_url,
                           action="/servers/%s/os-volume_attachments"
                                  % inst_id,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list instance(id:%s) attach info."
                          " Error: %s" % (inst_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def list_availability_zones(self, *args, **kwargs):
        """Return nova avaliability zones"""
        try:
            return req.get(url=self.compute_url,
                           action="/os-availability-zone",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list availability zones. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_flavors(self, *args, **kwargs):
        """Return flavors list"""
        try:
            return req.get(url=self.compute_url,
                           action="/flavors/detail",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list flavors. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_images(self, *args, **kwargs):
        try:
            return req.get(url=self.image_url,
                           action="/images",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list images. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_instances(self, *args, **kwargs):
        try:
            return req.get(url=self.compute_url,
                           action="/servers/detail",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list instances. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_keypairs(self, *args, **kwargs):
        """Return tenant keypairs list"""
        try:
            return req.get(url=self.compute_url,
                           action="/os-keypairs",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list keypairs. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_networks(self, *args, **kwargs):
        """Return network list"""
        try:
            if self.neutron_enabled:
                resp = req.get(url=self.network_url,
                               action="/networks",
                               **kwargs)
                data = resp["body"]
                networks = []
                # NOTE(Zhao Jiangbo): Only return networks of the project
                # and the shared networks
                for network in data["networks"]:
                    if network.get("project_id") == self.project_id:
                        networks.append(network)
                    elif network.get("tenant_id") == self.project_id:
                        networks.append(network)
                    elif network.get("shared"):
                        networks.append(network)
                return {
                    "header": resp["header"],
                    "body": networks,
                    "code": resp["code"]
                }
            else:
                # FIXME(Zhao Jiangbo): This API has no project_id and
                # shared attribute. How to filter ?
                resp = req.get(url=self.compute_url,
                               action="/os-networks",
                               **kwargs)
                nets = resp["body"]
                networks = []
                name_key = "name"
                for net in nets['networks']:
                    if name_key not in net.keys():
                        name_key = "label"
                    if name_key not in net.keys():
                        name_key = "id"
                    networks.append({
                        "id": net["id"],
                        "name": net[name_key],
                        "type": "fixed",
                        "subnets": [{
                            "name": net[name_key],
                            "cidr": net["cidr"],
                            "gateway": net["gateway"],
                            "allocation_pools": None
                        }]
                    })
                return {
                    "header": resp["header"],
                    "body": networks,
                    "code": resp["code"]
                }
        except Exception as err:
            logging.error("Failed to list networks. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_subnets(self, *args, **kwargs):
        try:
            if not self.neutron_enabled:
                return {
                    "header": "",
                    "body": "",
                    "code": 404
                }
            else:
                return req.get(url=self.network_url,
                               action="/subnets",
                               **kwargs)
        except Exception as err:
            logging.error("Failed to list subnets. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_ports(self, network_id=None, **kwargs):
        try:
            if not self.neutron_enabled:
                return {
                    "header": "",
                    "body": "",
                    "code": 404
                }
            else:
                action = "/ports"
                if network_id:
                    action = "/ports?network_id%s" % network_id
                return req.get(url=self.network_url,
                               action=action,
                               **kwargs)
        except Exception as err:
            logging.error("Failed to list ports. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_security_groups(self, *args, **kwargs):
        try:
            if not self.neutron_enabled:
                return req.get(url=self.compute_url,
                               action="/os-security-groups",
                               **kwargs)
            else:
                resp = req.get(url=self.network_url,
                               action="/security-groups",
                               **kwargs)
                data = resp["body"]
                security_groups = []
                # NOTE(Zhao Jiangbo): Only return security_group
                # of the project
                for security_group in data["security_groups"]:
                    if security_group.get("project_id") == self.project_id:
                        security_groups.append(security_group)
                    elif security_group.get("tenant_id") == self.project_id:
                        security_groups.append(security_group)
                return {
                    "header": resp["header"],
                    "body": {"security_groups": security_groups},
                    "code": resp["code"]
                }

        except Exception as err:
            logging.error("Failed to list security groups. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_snapshots(self, *args, **kwargs):
        try:
            return req.get(url=self.compute_url,
                           action="/os-snapshots/detail",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list snapshots. "
                          "Error: %s" % six.text_type(err))
            raise err

    @token_required
    @token_expired
    def list_volume_types(self, *args, **kwargs):
        try:
            return req.get(url=self.volume_url,
                           action="/types",
                           **kwargs)
        except Exception as err:
            logging.error("Failed to list volume types. "
                          "Error: %s" % six.text_type(err))
            raise err

    # NOTE(Ray): Get method for specific OpenStack resource, add new
    # method in this section, order by letter alpha
    @token_required
    @token_expired
    def get_image(self, image_id, **kwargs):
        try:
            return req.get(url=self.image_url,
                           action="/images/%s" % image_id,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get image(id:%s). Error: %s"
                          % (image_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def get_instance(self, instance_id, **kwargs):
        try:
            return req.get(url=self.compute_url,
                           action="/servers/%s" % instance_id,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get instance(id:%s). Error: %s"
                          % (instance_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def get_snapshot_by_id(self, snap_id, **kwargs):
        try:
            return req.get(url=self.compute_url,
                           action="/os-snapshots/%s" % snap_id,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get snapshot(id:%s). Error: %s"
                          % (snap_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def get_volume(self, volume_id, **kwargs):
        try:
            return req.get(url=self.volume_url,
                           action="/volumes/%s" % volume_id,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get volume(id:%s). Error: %s"
                          % (volume_id, six.text_type(err)))
            raise err

    # NOTE(Ray): Get Quota start
    @token_required
    @token_expired
    def get_compute_quota(self, *args, **kwargs):
        """Get nova quota usage

        According to OpenStack API document, quota interface maybe not
        allowed normal user to access according to policy.
        """
        try:
            quota_action = "/os-quota-sets/%s/detail" % self.project_id
            return req.get(url=self.compute_url,
                           action=quota_action,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get compute quota(project_id:%s). "
                          "Error: %s" % (self.project_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def get_volume_quota(self, *args, **kwargs):
        """Get cinder quota usage

        According to OpenStack API document, quota interface maybe not
        allowed normal user to access according to policy.
        """
        try:
            quota_action = "/os-quota-sets/%s" % self.project_id
            return req.get(url=self.volume_url,
                           action=quota_action,
                           query={"usage": True},
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get volume quota(project_id:%s). "
                          "Error: %s" % (self.project_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def get_network_quota(self, *args, **kwargs):
        """Get network quota usage

        According to OpenStack API document, quota interface maybe not
        allowed normal user to access according to policy.
        """
        try:
            quota_action = "/quotas/%s" % self.project_id
            return req.get(url=self.network_url,
                           action=quota_action,
                           **kwargs)
        except Exception as err:
            logging.error("Failed to get network quota(project_id:%s). "
                          "Error: %s" % (self.project_id, six.text_type(err)))
            raise err

    # NOTE(Ray): Image actions start, order by letter alpha
    @token_required
    @token_expired
    def create_instance_snapshot(self, inst_id, name, **kwargs):
        try:
            action = "/servers/%s/action" % inst_id
            body = {
                "createImage": {
                    "name": name
                }
            }
            return req.post(url=self.compute_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to create instance snapshot. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def delete_instance_snapshot(self, image_id, **kwargs):
        try:
            action = "/images/%s" % image_id
            return req.delete(url=self.compute_url,
                              action=action,
                              **kwargs)
        except Exception as err:
            logging.error("Failed to delete image(id: %s). Error: %s"
                          % (image_id, six.text_type(err)))
            raise err

    # NOTE(Ray): Volume actions start, order by letter alpha
    @token_required
    @token_expired
    def create_volume(self,
                      size,
                      name,
                      volume_type=None,
                      volume_az=None,
                      snapshot_id=None,
                      **kwargs):
        try:
            action = "/volumes"
            body = {
                "volume": {
                    "size": int(size),
                    "name": str(name)
                }
            }
            if volume_type:
                body["volume"]["volume_type"] = volume_type
            if volume_az:
                body["volume"]["availability_zone"] = volume_az
            if snapshot_id:
                body["volume"]["snapshot_id"] = snapshot_id
            return req.post(url=self.volume_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to create volume. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def create_volume_snapshot(self,
                               volume_id,
                               name,
                               **kwargs):
        try:
            action = "/snapshots"
            body = {
                "snapshot": {
                    "name": name,
                    "volume_id": volume_id,
                    "force": True
                }
            }
            return req.post(url=self.volume_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to create volume(id: %s) snapshot. Error: %s"
                          % (volume_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def update_volume_metedata(self, volume_id, data, **kwargs):
        try:
            action = "volumes/%s/action" % volume_id
            return req.post(url=self.volume_url,
                            action=action,
                            payload=data,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to update volume(id: %s) metedata. Error: %s"
                          % (volume_id, six.text_type(err)))
            raise err

    # volume ttach actions
    @token_required
    @token_expired
    def attach_volume(self, volume_id, instance_id, **kwargs):
        try:
            action = "servers/%s/os-volume_attachments" % instance_id
            body = {
                "volumeAttachment": {
                    "volumeId": volume_id
                }
            }
            return req.post(url=self.compute_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to attach volume(id: %s) "
                          "to instance(id: %s). Error: %s"
                          % (volume_id, instance_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def detach_volume(self, volume_id, instance_id, **kwargs):
        """Detach volume from instance the instance_id can is None"""
        try:
            action = "servers/%s/os-volume_attachments/%s" \
                     % (instance_id, volume_id)
            return req.delete(url=self.compute_url,
                              action=action,
                              **kwargs)
        except Exception as err:
            logging.error("Failed to detach volume(id: %s) "
                          "from instance(id: %s). Error: %s"
                          % (volume_id, instance_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def delete_volume(self, volume_id, **kwargs):
        try:
            action = "/volumes/%s" % volume_id
            return req.delete(url=self.volume_url,
                              action=action,
                              **kwargs)
        except Exception as err:
            logging.error("Failed to delete volume(id: %s). Error: %s"
                          % (volume_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def delete_volume_snapshot(self, snapshot_id, **kwargs):
        try:
            action = "/snapshots/%s" % snapshot_id
            return req.delete(url=self.volume_url,
                              action=action,
                              **kwargs)
        except Exception as err:
            logging.error("Failed to delete volume snapshot(id: %s). Error: %s"
                          % (snapshot_id, six.text_type(err)))
            raise err

    # NOTE(Ray): Instance actions start, order by letter alpha
    @token_required
    @token_expired
    def create_instance(self, data, **kwargs):
        try:
            action = "/os-volumes_boot"
            return req.post(url=self.compute_url,
                            action=action,
                            payload=data,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to create instance. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def delete_instance(self, instance_id, **kwargs):
        try:
            return req.delete(url=self.compute_url,
                              action="/servers/%s" % instance_id,
                              **kwargs)
        except Exception as err:
            logging.error("Failed to delete instance(id: %s). Error: %s"
                          % (instance_id, six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def create_server(self, data, **kwargs):
        try:
            action = "/servers"
            return req.post(url=self.compute_url,
                            action=action,
                            payload=data,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to create server. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def start_server(self, server_id, **kwargs):
        try:
            action = "/servers/%s/action" % server_id
            body = {
                "os-start": None
            }
            return req.post(url=self.compute_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to start server. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def stop_server(self, server_id, **kwargs):
        try:
            action = "/servers/%s/action" % server_id
            body = {
                "os-stop": None
            }
            return req.post(url=self.compute_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to stop server. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def reboot_server(self, server_id, **kwargs):
        try:
            action = "/servers/%s/action" % server_id
            body = {
                "reboot": {
                    "type": "HARD"
                }
            }
            return req.post(url=self.compute_url,
                            action=action,
                            payload=body,
                            **kwargs)
        except Exception as err:
            logging.error("Failed to reboot server. Error: %s"
                          % (six.text_type(err)))
            raise err

    @token_required
    @token_expired
    def _map_domain_to_ip(self):
        pass

    def cache_clean(self):
        with open(TOKEN_LOCAL_FILE, "w"):
            pass
