# Terraform IaC Audit — Domain Reference

White-box security and configuration audit for Terraform codebases. Complements black-box scanning (vibecode-lead-finder) with source-level analysis.

## Cost Table

| Level | Gate | Execute | Cost | Proves |
|-------|------|---------|------|--------|
| L1 | `terraform fmt -check`, `terraform validate` | Read .tf files, grep for known anti-patterns | 1-5min | Syntax valid, known misconfigurations caught |
| L2 | `tflint`, `trivy config .` | `terraform plan` in target workspace, diff against expected | 5-15min | Provider-aware lint, plan shows no unexpected changes |
| L3 | `checkov -d .`, OPA/Sentinel policies | Apply to isolated environment, verify with AWS API calls | 30min+ | Full compliance scan, runtime verification |

## Audit Checklist

Work through these categories in order. Each item lists what to grep for, where to look, and what's wrong when you find it.

### 1. Committed credentials

The highest-priority finding. Scan the entire repo, not just .tf files.

```
# API keys, tokens, passwords in HCL
grep -rn "api_key\|app_key\|password\|token\|secret" --include="*.tf" \
  | grep -v "secretsmanager\|var\.\|local\.\|data\."

# Hardcoded tokens in task definitions, user data, scripts
grep -rn "token\s*=" --include="*.tf" --include="*.sh" --include="*.py"

# Base64-encoded secrets
grep -rn "^[A-Za-z0-9+/=]\{40,\}" --include="*.tf"
```

What you're looking for:
- Provider blocks with literal `api_key = "..."` (Datadog, PagerDuty, etc.)
- ECS task definitions with tokens in `command` arrays
- User data scripts with embedded credentials
- Lambda environment variables with literal secret values

### 2. Network exposure — RDS

The most common critical finding in startup Terraform. Check every `aws_db_instance`:

```
grep -n "publicly_accessible" *.tf
grep -n "db_subnet_group" *.tf   # cross-reference: is it public or private subnets?
```

For each RDS instance, verify three things form a consistent set:
- `publicly_accessible` must be `false`
- `db_subnet_group_name` must reference private subnets
- Security group must not allow `0.0.0.0/0` on port 3306/5432

When these three are scattered across different files (rds-*.tf, security_groups/*.tf, network.tf), they're easy to get wrong independently. A public subnet group with a restrictive SG still exposes the instance to the VPC. A private subnet group with `publicly_accessible = true` does nothing (AWS ignores it), but signals confused intent.

Also check:
- `deletion_protection` — should be `true` in production
- `multi_az` — should be `true` for production primary databases
- `storage_encrypted` — should always be `true`
- `backup_retention_period` — 7 days is the minimum, 30+ for production
- Parameter groups: `require_secure_transport = 1` for MySQL SSL enforcement
- `enabled_cloudwatch_logs_exports` — should include error, slowquery at minimum

### 3. Network exposure — security groups

```
grep -rn "0.0.0.0/0" --include="*.tf"
```

For each match, classify:
- ALB ingress on 443: expected for public-facing ALB
- ALB ingress on 80: acceptable if listener redirects to 443
- RDS/database port from 0.0.0.0/0: critical finding
- All-port ingress (0-65535): overly permissive, even from VPC CIDRs
- Egress 0.0.0.0/0: common but worth noting for sensitive workloads

Check security group references vs CIDR ranges. SG-to-SG references (`security_groups = [sg-xxx]`) are more precise than CIDR blocks. A database SG that allows the entire VPC CIDR on 3306 lets any instance in the VPC connect, not just the application.

### 4. Network exposure — OpenSearch, ElastiCache, other data stores

```
grep -rn "aws_opensearch_domain\|aws_elasticache" --include="*.tf"
```

For OpenSearch, check:
- `vpc_options` block exists (otherwise it's internet-accessible)
- `access_policies` defined (otherwise default allows all)
- `encrypt_at_rest` enabled
- `node_to_node_encryption` enabled
- `advanced_security_options` with fine-grained access control
- Domain name containing "public" is a red flag

### 5. TLS configuration

```
grep -rn "ssl_policy" --include="*.tf"
```

Any policy older than `ELBSecurityPolicy-TLS-1-2-2017-01` allows TLS 1.0. Policies from 2015 are a compliance failure. For 2026, use `ELBSecurityPolicy-TLS13-1-2-2021-06` or newer.

Check both external and internal ALBs. Internal ALBs with old TLS policies allow downgrade attacks from within the VPC.

### 6. IAM policies

```
grep -rn 'resources.*=.*\["\*"\]' --include="*.tf"
grep -rn '"iam:\*"\|"s3:\*"\|"ec2:\*"\|"sts:\*"' --include="*.tf"
```

Wildcard resources (`"*"`) with broad actions are the norm in startup Terraform but become a liability at scale. Prioritize:
- `iam:*` on `*` — can create backdoor roles
- `sts:*` on `*` — can assume any role in the account
- `s3:*` on `*` — can read/delete any bucket
- `kms:*` on `*` — can decrypt any encrypted resource

For OIDC/GitHub Actions roles, check the `sub` condition. `repo:Org/*` allows any repo in the org to assume the role. Should be scoped to specific repos and branches.

Also check: same role used for both `execution_role_arn` and `task_role_arn` on ECS tasks. These should be separate — execution role (ECR pull, log write) vs task role (what the app code uses at runtime).

### 7. S3 buckets

```
grep -rn "aws_s3_bucket " --include="*.tf"         # list all buckets
grep -rn "public_access_block" --include="*.tf"     # which have blocks?
grep -rn "aws_s3_bucket_versioning" --include="*.tf" # which have versioning?
grep -rn "server_side_encryption" --include="*.tf"   # which have encryption?
```

Every bucket should have:
- `aws_s3_bucket_public_access_block` (all four flags true)
- Server-side encryption (AES256 minimum, KMS preferred)
- Versioning (for any bucket holding data you can't regenerate)

Check CORS configurations: `allowed_origins = ["*"]` with write methods (PUT, POST, DELETE) allows any website to upload/delete objects via cross-origin requests.

Check bucket policies for `Principal = "*"` — even with conditions (VPC endpoint, source IP), this grants all AWS principals access within the condition scope.

### 8. API Gateway

```
grep -rn "authorization.*NONE" --include="*.tf"
grep -rn "api_key_required.*false\|api_key_required" --include="*.tf"
```

Endpoints with `authorization = "NONE"` and no API key are public. Check if this is intentional (public read API) or a TODO that was never done (look for comments like `# Update as per your authorization mechanism`).

Check for throttling: `aws_api_gateway_usage_plan` with `throttle` and `quota` settings. Missing throttling means any client can hit the API at unlimited rate.

### 9. State management

```
grep -rn "backend " --include="*.tf"
grep -rn "dynamodb_table\|use_lockfile" --include="*.tf"
```

For Terraform >= 1.10, S3 native locking is the default. DynamoDB locking TODOs in backends are stale if the installed version is 1.10+. Check `terraform version` to confirm.

State bucket itself should have versioning and encryption enabled (check separately, usually provisioned outside the main Terraform).

### 10. Configuration surface area

For small teams (2-5 engineers) with few environments (dev/prod), watch for:
- Variable maps with 3+ keys when only 2 environments are active
- Both map lookups (`var.x[local.environment]`) and ternaries (`local.environment == "production" ? X : Y`) used for the same binary decision
- The same value derived differently in different files (`terraform.workspace` vs `var.environment` vs `local.environment`)
- Duplicated values across files (SSO role ARNs in both locals.tf and iam/roles.tf)

Count the total tunable parameters vs the actual degrees of freedom. If you have 80 values describing a 1-bit choice (dev or prod), the configuration surface area hides misconfigurations. The LLM-RDS-public-with-0.0.0.0/0 pattern is a worked example: the decision was scattered across three resources in two files with inconsistent count guards, invisible during review.

The fix for overparameterized binary configs: two `.tfvars` files (one per environment) and a single `is_production` boolean for conditional resources.

## Anti-patterns — Quick Reference

| Pattern | Where to find it | Why it's bad |
|---------|-----------------|--------------|
| `publicly_accessible = true` on RDS | rds-*.tf | Database reachable from internet |
| `cidr_blocks = ["0.0.0.0/0"]` on data store SG | security_groups/*.tf | Anyone can connect |
| `ssl_policy = "ELBSecurityPolicy-2015-05"` | *_alb.tf | TLS 1.0 enabled |
| `authorization = "NONE"` on API Gateway | apigateway_*.tf | Public unauthenticated endpoint |
| Literal token/key in HCL | provider blocks, task defs | Credential in git history |
| `image = "...:latest"` on sidecar | task-definition.tf | Unpinned dependency |
| `execution_role_arn = task_role_arn` | task-definition.tf | Excess container privileges |
| `from_port = 0, to_port = 65535` | security_groups/*.tf | All-port access |
| `allowed_origins = ["*"]` with write methods | s3.tf CORS config | Cross-origin upload/delete |
| No `access_policies` on OpenSearch | opensearch.tf | Potentially public cluster |
| `lifecycle { ignore_changes = [environment] }` | lambda.tf | Drift suppression |
| Variable map with dead keys | variables.tf | Noise, cognitive load |
| `-p"$PASSWORD"` in shell command | Lambda scripts | Password in process list |

## Reporting Format

When producing a discovery report, structure findings as:

1. Configuration surface area analysis (overparameterization)
2. Committed credentials (grep the whole repo)
3. Network security audit (RDS, SGs, ALBs, OpenSearch)
4. IAM audit (wildcard policies, role separation)
5. Data store security (S3, DynamoDB, encryption, backups)
6. CI/CD security (GHA tokens, OIDC scope, image pinning)
7. Deployment pattern assessment (multi-repo, module usage, state management)

Each finding: location (file:line), what's wrong, why it matters, fix with effort estimate. Group by severity (CRITICAL, HIGH, MEDIUM, LOW). Tie structural issues (surface area) to concrete vulnerabilities they hide.
