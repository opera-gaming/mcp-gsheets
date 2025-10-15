/*
 * Copyright © 2025 Opera Norway AS. All rights reserved.
 *
 * This file is an original work developed by Opera.
 */

locals {
  aws_default_region = "eu-north-1"
  aws_regions = [
    {
      region  = "eu-north-1"
      alias   = "eun1"
      default = true
    },
  ]
}
