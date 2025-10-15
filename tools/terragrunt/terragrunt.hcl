/*
 * Copyright © 2025 Opera Norway AS. All rights reserved.
 *
 * This file is an original work developed by Opera.
 */

locals {
  account_vars     = read_terragrunt_config(find_in_parent_folders("account.hcl")).locals
  environment_vars = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
  region_vars      = read_terragrunt_config(find_in_parent_folders("region.hcl")).locals
  local_component  = read_terragrunt_config("${get_terragrunt_dir()}/component.hcl", { locals = { component = "" } }).locals.component
  component        = local.local_component != "" ? local.local_component : read_terragrunt_config(find_in_parent_folders("component.hcl")).locals.component

  # Root variables
  variables = {
    project_name = "gm-cloud"
    component    = local.component
    environment  = local.environment_vars.env

  }

  aws_default_tags = {
    "opera:project"                  = "${local.variables.project_name}"
    "opera:environment"              = "${local.environment_vars.env}"
    "opera:component"                = "${local.component}"
    "opera:owner"                    = "gaming-gothenburg-devops-team@opera.com"
    "opera:gaming:terragrunt-source" = path_relative_to_include()
  }

  # Remote setup
  s3_state = {
    bucket_name         = "${local.account_vars.aws_account_id}-terraform-state"
    dynamodb_table_name = "${local.variables.project_name}-terraform-locks"
    region              = "${local.account_vars.terragrunt_state_region}"
  }
}

generate "variables" {
  path      = "variables_root.tf"
  if_exists = "skip"
  contents  = <<-EOF
    variable "project_name" {
      type        = string
      description = "Name of the project"
    }
    variable "component" {
      type        = string
      description = "Component name"
    }
    variable "environment" {
      type        = string
      description = "Environment name"
    }
    variable "env" {
      type        = string
      description = "Environment name"
    }
    variable "aws_account_id" {
      type        = string
      description = "AWS account ID"
    }
  EOF
}

generate "terraform" {
  path      = "terraform.tf"
  if_exists = "skip"
  contents  = <<-EOF
    terraform {
      required_version = "~> 1.9"
      required_providers {
        aws = {
          source  = "hashicorp/aws"
          version = "~> 5.0"
        }
        cloudflare = {
          source = "cloudflare/cloudflare"
          version = "~> 4.0"
        }
      }
    }
  EOF
}

# Generate an AWS provider block.
generate "provider_aws" {
  path      = "provider_aws.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
%{~for i in local.region_vars.aws_regions}
provider "aws" {
  region = "${i.region}"
%{if !contains(keys(i), "default")~}
  alias = "${i.alias}"
%{endif~}
  allowed_account_ids = ["${local.account_vars.aws_account_id}"]

  default_tags {
    tags = {
%{for tag_key, tag_value in local.aws_default_tags~}
      "${tag_key}" = "${tag_value}"
%{endfor~}
      "opera:gaming:region"      = "${i.region}"
    }
  }
}
%{~endfor}
  EOF
}

generate "provider_cloudflare" {
  path      = "provider_cloudflare.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    provider "cloudflare" {}
  EOF
}

remote_state {
  backend = "s3"
  config = {
    encrypt        = true
    bucket         = local.s3_state.bucket_name
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.s3_state.region
    dynamodb_table = local.s3_state.dynamodb_table_name
  }

  generate = {
    path      = "remote_state.tf"
    if_exists = "overwrite_terragrunt"
  }
}

inputs = merge(
  local.account_vars,
  local.environment_vars,
  local.region_vars,
  local.variables
)
