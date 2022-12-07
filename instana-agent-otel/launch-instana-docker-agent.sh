#!/bin/bash

sudo podman run \
   -it --rm \
   --name instana-agent \
   --volume /var/run:/var/run \
   --volume /run:/run \
   --volume /dev:/dev:ro \
   --volume /sys:/sys:ro \
   --volume /var/log:/var/log:ro \
   --volume ./configuration-otel.yaml:/opt/instana/agent/etc/instana/configuration-otel.yaml \
   --volume ./configuration-python.yaml:/opt/instana/agent/etc/instana/configuration-python.yaml \
   --privileged \
   --net=host \
   --pid=host \
   --env="INSTANA_AGENT_ENDPOINT=xxxxxxxx-saas.instana.io" \
   --env="INSTANA_AGENT_ENDPOINT_PORT=443" \
   --env="INSTANA_AGENT_KEY=xxxXXXXxxxxXXXXxxxXXXXx" \
   --env="INSTANA_DOWNLOAD_KEY=xxxXXXXxxxxXXXX" \
   --env="INSTANA_ZONE=xxx-test-emt" \
   icr.io/instana/agent
