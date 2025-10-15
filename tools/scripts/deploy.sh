#!/usr/bin/env sh

IMAGE_NAME="${1}"
IMAGE_TAG="${2}"
ENVIRONMENT="${3}"
AWS_REGION="${4}"

# echo 'Update Docker tag used by ECS...'
# export IMAGE_TAG_URI=$DOCKER_REPOSITORY:$IMAGE_TAG

echo "Deploying ${IMAGE_TAG_URI} to ${ENVIRONMENT} with Terragrunt..."
#cd tools/$IMAGE_NAME/$ENVIRONMENT/$AWS_REGION/ecs-service && \
IMAGE_TAG_URI=$DOCKER_REPOSITORY:$IMAGE_TAG \
terragrunt apply \
    --terragrunt-non-interactive \
    -auto-approve \
    --terragrunt-working-dir="tools/terragrunt/$IMAGE_NAME/$ENVIRONMENT/$AWS_REGION/ecs-service" 
