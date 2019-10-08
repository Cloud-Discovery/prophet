# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).)

from requests import RequestException


# common errors
class IllegalArgumentError(ValueError):
    pass


# http errors
class HttpServerError(RequestException):
    pass


class HttpUnauthorized(RequestException):
    pass


class ItemNotFound(Exception):
    """Raise when can not get specific resource"""
    pass


# OpenStack errors
class CatalogNotFound(Exception):
    """Raise when can not parse catalog from authentication response"""
    pass


class ParserCatalogError(Exception):
    """Raise when parse catalog from authentication response"""
    pass


class ConnectOpenStackError(Exception):
    """Raise when can not connect to OpenStack auth url"""
    pass


class ConnectZStackError(Exception):
    """Raise when can not connect to ZStack auth url"""
    pass


class RequestZStackError(Exception):
    """Raise if return error when send request to ZStack"""
    pass


class TokenNotFound(Exception):
    """Raise when can not parse token from authentication response"""
    pass


class ProjectIdNotFound(Exception):
    """Raise when can not parse project id"""
    pass
