#!/bin/bash

set -e

subcmd=$1
action=$2
opts=$3

BASE_PATH=$(cd `dirname $0`; pwd)
BASE_URL=http://192.168.10.254
DOCKER_TAG=${TAG_ID}
DOCKER_REG="192.168.10.10/hypermotion"

function deploy() {
    check=`docker images | grep hypermotion/base | awk '{print $3}'`
    if [ "$check" = "" ]; then
        echo "Download hypermotion/base.tgz and load as image"
        docker pull 192.168.10.10/hypermotion/base:latest
    fi
    CUR=$(cd "$BASE_PATH/.."; pwd)
    cd $CUR
    docker build --rm --tag prophet \
                 -f "$CUR/Dockerfile.deploy" $CUR
    img_id=`docker images | grep "prophet " | awk '{print $3}'`
    echo "Save Image[$img_id] with cmd: "
    echo "> docker save $img_id prophet | gzip>prophet.tgz"
    docker save $img_id prophet | gzip>prophet.tgz
    docker login 192.168.10.10 -u jenkins -p Abc999
    if [ $? == 0 ]; then
        docker tag $img_id ${DOCKER_REG}/prophet:${DOCKER_TAG} && \
        docker push ${DOCKER_REG}/prophet:${DOCKER_TAG} && \
        docker rmi ${DOCKER_REG}/prophet:${DOCKER_TAG} && \
        docker tag $img_id ${DOCKER_REG}/prophet:latest && \
        docker push ${DOCKER_REG}/prophet:latest && \
        docker rmi ${DOCKER_REG}/prophet:latest && \
        echo "The image has been uploaded to the repository..."
    fi
    docker rmi $img_id
}

if [[ "$subcmd" = "deploy" ]]; then
    deploy
    exit 0
fi
