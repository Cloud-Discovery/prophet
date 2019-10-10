# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).)

"""Wrapper class for request module"""

import logging
import re
import requests
from urlparse import urljoin

from errors import ItemNotFound, \
    HttpServerError, HttpUnauthorized
import http_status_codes as http_code

DEFAULT_HEADERS = {"Content-Type": "application/json"}


class HttpRequest(object):

    @classmethod
    def get(self, *args, **kwargs):
        return self._do_request(method="GET", *args, **kwargs)

    @classmethod
    def post(self, *args, **kwargs):
        return self._do_request(method="POST", *args, **kwargs)

    @classmethod
    def put(self, *args, **kwargs):
        return self._do_request(method="PUT", *args, **kwargs)

    @classmethod
    def delete(self, *args, **kwargs):
        return self._do_request(method="DELETE", *args, **kwargs)

    @classmethod
    def http_2xx(self, status_code):
        return re.match(r"2\d{2}", str(status_code))

    @classmethod
    def http_4xx(self, status_code):
        return re.match(r"4\d{2}", str(status_code))

    @classmethod
    def http_5xx(self, status_code):
        return re.match(r"5\d{2}", str(status_code))

    @classmethod
    def _do_request(self,
                    method="GET",
                    url=None,
                    action=None,
                    headers=DEFAULT_HEADERS,
                    query=None,
                    payload=None,
                    timeout=None,
                    keep_alive=True,
                    max_retries=None,
                    **kwargs):
        """Wrapper method for all http connection, untify log output"""

        # set headers
        headers.update(DEFAULT_HEADERS)

        # combine url
        if action:
            url = urljoin(self._url_format(url),
                          self._action_format(action))

        logging.info("[HTTP]REQ: [%(method)s] %(headers)s %(url)s, "
                     "body is %(payload)s, "
                     "query is %(query)s" % {
                         "method": method,
                         "headers": headers,
                         "url": url,
                         "payload": payload,
                         "query": query})

        ret_headers = None
        ret_body = None
        try:
            if not keep_alive:
                s = requests.session()
                s.keep_alive = False
            if max_retries:
                requests.adapters.DEFAULT_RETRIES = max_retries
            if timeout:
                resp = requests.request(method,
                                        url,
                                        params=query,
                                        json=payload,
                                        headers=headers,
                                        timeout=timeout)
            else:
                resp = requests.request(method,
                                        url,
                                        params=query,
                                        json=payload,
                                        headers=headers)
            status_code = resp.status_code
            resp_headers = resp.headers
            resp_text = resp.text
            resp_body = resp.json()
            logging.info("[HTTP]RESP: "
                         "%(method)s %(url)s, "
                         "RESP CODE: %(status_code)s\n"
                         "RESP HEADERS: %(resp_headers)s\n"
                         "RESP BODY: %(resp_body)s" % {
                             "method": method,
                             "url": url,
                             "status_code": status_code,
                             "resp_headers": resp_headers,
                             "resp_body": resp_body})

            ret_headers = resp_headers
            ret_body = resp_body
        except ValueError as err:
            logging.warn("[HTTP]Failed to parse RESP BODY "
                         "in json, RESP BODY is %s" % resp_text)
            ret_headers = resp_headers
            ret_body = resp_text
        except Exception as err:
            logging.error("[HTTP]Failed to %(method)s %(url)s, "
                          "error is %(error)s" % {
                              "method": method,
                              "url": url,
                              "error": err})
            raise err

        # Define error message returns
        ret_err = {
            "code": status_code,
            "message": ret_body
        }
        if self.http_2xx(status_code):
            result = {
                "header": ret_headers,
                "body": ret_body,
                "code": status_code
            }
            return result

        elif self.http_4xx(status_code):
            if status_code == http_code.UNAUTHORIZED:
                ret_err["message"] = "Authentication failed or required."
                raise HttpUnauthorized(ret_err)

            if status_code == http_code.NOT_FOUND:
                ret_err["message"] = "Item not found."
                raise ItemNotFound(ret_err)

            logging.error("Http request failed, status "
                          "code %s." % status_code)
            raise requests.RequestException(ret_err)

        elif self.http_5xx(status_code):
            logging.error("http server response error, "
                          "status code %s." % status_code)
            raise HttpServerError(ret_err)

        else:
            logging.error("Unknown http request error, "
                          "status code %s." % status_code)
            raise requests.RequestException(ret_err)

    @classmethod
    def _url_format(self, url):
        """Add / at the end of url

        To use urlparse to join two urls, if the ending part without /,
        after join, the last part will be replaced. For example, if
        auth_url is http://192.168.10.201:5000/v2.0, and join with
        /tokens, we expect http://192.168.10.201:5000/v2.0/tokens, but
        the real return is http://192.168.10.201:5000/tokens. Add / at
        the end of os_auth_url.
        """
        if not url.endswith("/"):
            return url + "/"
        else:
            return url

    @classmethod
    def _action_format(self, action):
        """Add / at start"""
        if action.startswith("/"):
            return action[1:]
        else:
            return action
