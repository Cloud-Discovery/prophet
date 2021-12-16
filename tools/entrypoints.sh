#!/bin/bash

#
# Service start script
#
# Maintainer: Ray Sun<ray.sun@oneprocloud.com>
#

set -x
set -e

if [[ -z "$1" ]]; then
    /bin/bash
elif [[ "$1" =~ "bash" ]]; then
    exec "$@"
fi
