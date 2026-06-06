#!/bin/sh
set -eu

APP_MOUNT_INFO="$(awk '$5 == "/app" { print; exit }' /proc/self/mountinfo)"
HOST_APP_ROOT="$(printf '%s\n' "$APP_MOUNT_INFO" | awk '{ print $4 }')"

if [ -z "$APP_MOUNT_INFO" ] || [ -z "$HOST_APP_ROOT" ]; then
  echo "Error: unable to locate the /app bind mount in /proc/self/mountinfo." >&2
  echo "Start the backend container with the repository mounted at /app (for example, -v .:/app)." >&2
  exit 1
fi

case "$APP_MOUNT_INFO" in
  *"path=C:"*)
    HOST_APP_ROOT="/run/desktop/mnt/host/c${HOST_APP_ROOT}"
    ;;
esac

SAM_TEMPLATE=".docker-sam/docker-template.yaml"
SAM_VOLUME_BASE="${SAM_DOCKER_VOLUME_BASEDIR:-${HOST_APP_ROOT}/.docker-sam}"
DOCKER_ARCHITECTURE="$(docker info --format '{{.Architecture}}' 2>/dev/null || true)"

case "${SAM_FUNCTION_ARCHITECTURE:-$DOCKER_ARCHITECTURE}" in
  amd64|x86_64)
    SAM_FUNCTION_ARCHITECTURE="x86_64"
    ;;
  arm64|aarch64)
    SAM_FUNCTION_ARCHITECTURE="arm64"
    ;;
  *)
    SAM_FUNCTION_ARCHITECTURE="x86_64"
    ;;
esac
echo "Using $SAM_FUNCTION_ARCHITECTURE for Docker local SAM template."

python /app/scripts/prepare_sam_docker_template.py \
  --source template.yaml \
  --output "$SAM_TEMPLATE" \
  --code-uri-prefix "../" \
  --architecture "$SAM_FUNCTION_ARCHITECTURE"

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
