/*
 * Copyright © 2025 Opera Norway AS. All rights reserved.
 *
 * This file is an original work developed by Opera.
 */

terraform {
  source = "git@github.com:opera-gaming/gaming-infra.git//terraform/modules/ecs-service-v2"
}

include {
  path = find_in_parent_folders()
}

dependency "rds_instance" {
  config_path = "../rds-instance"
}

locals {
  environment    = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals.env
  aws_region     = read_terragrunt_config(find_in_parent_folders("region.hcl")).locals.aws_default_region
  aws_account_id = read_terragrunt_config(find_in_parent_folders("account.hcl")).locals.aws_account_id
  service_name   = "mcp-gsheets-${local.environment}"
  domain_name    = "mcp-gsheets.gmx.dev"
  image          = get_env("IMAGE_TAG_URI", "184861730404.dkr.ecr.eu-north-1.amazonaws.com/mcp-gsheets:latest")
  container_port = 8080
  app_secrets    = "arn:aws:secretsmanager:eu-north-1:184861730404:secret:test/mcp-gsheets-6msVD9"
}

inputs = merge(local, {
  route53_hosted_zone = "gmx.dev"

  dns_record_mappings = {
    "${local.domain_name}" = {
      domain_name         = local.domain_name
      record_type         = "CNAME"
      record_value        = "/infra/gx-games/${local.environment}/alb/dns-name"
      use_ssm_parameter   = true
      route53_hosted_zone = "gmx.dev"
    }
  }

  ### container definitions
  alb_listener_priority = 1801
  ingress_rules         = []

  ### service definitions
  desired_count              = 1
  deployment_maximum_percent = 200

  ### autoscaling
  scale_target_min_capacity    = 1
  scale_target_max_capacity    = 1
  scale_up_policy_adjustment   = 1
  scale_down_policy_adjustment = -1
  scale_up_alarms = {
    "cpu-high-avg" = {
      metric_name         = "CPUUtilization"
      namespace           = "AWS/ECS"
      statistic           = "Maximum"
      comparison_operator = "GreaterThanOrEqualToThreshold"
      threshold           = 80
      evaluation_periods  = 3
      period              = 60
    }
  }
  scale_down_alarms = {
    "cpu-low-avg" = {
      metric_name         = "CPUUtilization"
      namespace           = "AWS/ECS"
      statistic           = "Average"
      comparison_operator = "LessThanOrEqualToThreshold"
      threshold           = 20
      evaluation_periods  = 3
      period              = 60
    }
  }
  ### health check
  health_check_grace_period = 60
  health_check = {
    healthy_threshold   = 3
    interval            = 30
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    unhealthy_threshold = 2
    matcher             = "200"
  }

  ### task definition
  task_cpu    = "512"
  task_memory = "1024"

  containers = ([
    {
      name      = "${local.service_name}"
      essential = true
      image     = local.image
      environment = [
        {
          "name" : "ENVIRONMENT",
          "value" : "${local.environment}"
        },
        {
          "name" : "S3_BUCKET_NAME"
          "value" : "gg-mcp-gsheets-test"
        },
        {
          "name" : "BASE_URL"
          "value" : "https://mcp-gsheets.gmx.dev"
        }
      ]
      secrets = [
        {
          "name" : "DATABASE_URL",
          "valueFrom" : "${dependency.rds_instance.outputs.aws_ssm_secret_arn}:url::"
        },
        {
          "name" : "JWT_SECRET_KEY",
          "valueFrom" : "${local.app_secrets}:JWT_SECRET_KEY::"
        },
        {
          "name" : "GOOGLE_CLIENT_ID",
          "valueFrom" : "${local.app_secrets}:GOOGLE_CLIENT_ID::"
        },
        {
          "name" : "GOOGLE_CLIENT_SECRET",
          "valueFrom" : "${local.app_secrets}:GOOGLE_CLIENT_SECRET::"
        }
      ]
      portMappings = [
        {
          containerPort = local.container_port
          hostPort      = local.container_port
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awsfirelens"
        options = {
          Name       = "grafana-loki"
          RemoveKeys = "ecs_task_arn"
          LabelKeys  = "container_id,ecs_task_definition,source,ecs_cluster,level"
          Labels     = "{aws_account=\"${local.aws_account_id}\",aws_region=\"${local.aws_region}\",ecs_service=\"${local.service_name}\",service_name=\"fluent-bit\"}"
          LineFormat = "json"
          LogLevel   = "debug"
          Timeout    = "5s"
          MinBackoff = "1m"
          MaxBackoff = "1m"
          MaxRetries = "1"
        }
        secretOptions = [
          {
            "name" : "Url",
            "valueFrom" : "arn:aws:ssm:eu-north-1:184861730404:parameter/infra/loki-url"
          }
        ]
      }
      cpu         = 0
      volumesFrom = []
      dockerLabels = {
        "application" = "${local.service_name}"
      }
    },
    {
      name         = "fluentbit"
      essential    = true
      image        = "184861730404.dkr.ecr.eu-north-1.amazonaws.com/opera/gaming/infra/fluent-bit:0.2"
      environment  = []
      portMappings = []
      firelensConfiguration = {
        type = "fluentbit",
        options = {
          enable-ecs-log-metadata = "true"
          config-file-type        = "file"
          config-file-value       = "/fluent-bit/configs/extra.conf"
        }
      }
      cpu         = 0
      mountPoints = []
      user        = "0"
      volumesFrom = []
    }
  ])
  task_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Action" : "s3:*",
        "Effect" : "Allow",
        "Resource" : [
          "arn:aws:s3:::gg-mcp-gsheets-test/*",
          "arn:aws:s3:::gg-mcp-gsheets-test"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ],
        Resource = "*"
      }
    ]
  })
  task_execution_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = [
          "arn:aws:ecr:${local.aws_region}:${local.aws_account_id}:repository/mcp-gsheets",
          "arn:aws:ecr:eu-north-1:184861730404:repository/opera/gaming/infra/fluent-bit"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:*:*:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:UpdateService",
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:DeleteAlarms"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "secretsmanager:GetSecretValue"
        ]
        Resource = "*"
      }
    ]
  })
  parameter_vpc_id          = "/infra/gx-games/${local.environment}/network/vpc/vpc-id"
  parameter_private_subnets = "/infra/gx-games/${local.environment}/network/vpc/private-subnets"
  parameter_public_subnets  = "/infra/gx-games/${local.environment}/network/vpc/public-subnets"
  parameter_vpc_cidr        = "/infra/gx-games/${local.environment}/network/vpc/cidr"
  parameter_ecs_arn         = "/infra/gx-games/${local.environment}/ecs/arn"
  parameter_ecs_name        = "/infra/gx-games/${local.environment}/ecs/name"
  parameter_alb_https_listener_arn_list = [
    "/infra/gx-games/${local.environment}/alb/https-listener-arn",
  ]
})
