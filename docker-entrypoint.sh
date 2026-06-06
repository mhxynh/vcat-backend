#!/bin/sh
set -eu

APP_MOUNT_INFO="$(awk '$5 == "/app" { print; exit }' /proc/self/mountinfo)"
HOST_APP_ROOT="$(printf '%s\n' "$APP_MOUNT_INFO" | awk '{ print $4 }')"

case "$APP_MOUNT_INFO" in
  *"path=C:"*)
    HOST_APP_ROOT="/run/desktop/mnt/host/c${HOST_APP_ROOT}"
    ;;
esac

SAM_TEMPLATE=".docker-sam/docker-template.yaml"
SAM_VOLUME_BASE="${SAM_DOCKER_VOLUME_BASEDIR:-${HOST_APP_ROOT}/.docker-sam}"

python /app/scripts/prepare_sam_docker_template.py \
  --source template.yaml \
  --output "$SAM_TEMPLATE" \
  --code-uri-prefix "../"

rm -f /tmp/vcat-backend-warmed

if [ "$HOST_APP_ROOT" != "/app" ] && [ ! -e "$HOST_APP_ROOT" ]; then
  mkdir -p "$(dirname "$HOST_APP_ROOT")"
  ln -s /app "$HOST_APP_ROOT"
fi

sam local start-api \
  --template "$SAM_TEMPLATE" \
  --config-env docker \
  --host 0.0.0.0 \
  --port 3001 \
  --docker-network vcat-dev \
  --docker-volume-basedir "$SAM_VOLUME_BASE" \
  --invoke-image vcat-backend-lambda-local:latest \
  --skip-pull-image \
  --container-host "${SAM_CONTAINER_HOST:-host.docker.internal}" \
  --container-host-interface 0.0.0.0 \
  --parameter-overrides \
    dbHostParam=postgres \
    dbNameParam=vcat_sandbox \
    dbUserParam=postgres \
    dbPasswordParam=postgres &

sam_pid="$!"
trap 'kill "$sam_pid" 2>/dev/null || true' INT TERM

python /app/scripts/warm_backend_api.py

wait "$sam_pid"
