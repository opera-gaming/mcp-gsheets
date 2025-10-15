/*
 * Copyright © 2025 Opera Norway AS. All rights reserved.
 *
 * This file is an original work developed by Opera.
 */

terraform {
  source = "git@github.com:opera-gaming/gaming-infra.git//terraform/modules/rds-postgres-instance"
}

include {
  path = find_in_parent_folders()
}

locals {
  db_identifier           = "mcp-gsheets-test"
  create_replica          = false
  component               = "mcp-ghsheets"
  instance_class          = "db.t4g.micro"
  storage_type            = "gp2"
  allocated_storage       = 10
  major_engine_version    = "17"
  engine_version          = "17.5"
  parameters_family       = "postgres17"
  backup_retention_period = 0
  deletion_protection     = true
  publicly_accessible     = false
  aws_ssm_secret_name     = "test/mcp-gsheets-db/creds"
  parameters = [
    {
      name         = "rds.force_ssl"
      value        = "0"
      apply_method = "immediate"
    }
  ]
}

inputs = merge(local, {
  ingress_source_sg_id_list = toset([
    "sg-00efb0f25e9991a59", # ssm-proxy
    "sg-0cf3cc66d646ead7b", # ssm-proxy
    "sg-078e3d07315948544"  # ecs/test/mcp-gsheets-test
  ])
  vpc_id = "vpc-0508b5be3567f3d02"
  subnet_ids = [
    "subnet-0171ece4a02df76ea",
    "subnet-01eee625428e46167",
    "subnet-00cfa2bed73d26cfc"
  ]
  subnet_group = "opera-gaming-common"
})
