# AWS4 Shape Library Reference

Source: `mxgraph.aws4` stencil library (1032 shapes, updated Jan 2026). Full list: [references/aws4-shapes.txt](aws4-shapes.txt).

## Finding Shape Names

**Grep the full list** to find the exact shape name for any AWS service:
```
grep -i "load balancer" references/aws4-shapes.txt
→ application load balancer
→ classic load balancer
→ elastic load balancing
→ gateway load balancer
→ network load balancer
```

Then convert spaces to underscores for the `resIcon`/`prIcon` value:
```
"application load balancer" → mxgraph.aws4.application_load_balancer
"nat gateway"               → mxgraph.aws4.nat_gateway
"secrets manager"           → mxgraph.aws4.secrets_manager
```

## Icon Patterns

**resourceIcon** (small square, 45-50px, category-colored — for individual resources):
```
shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{name};fillColor={category_color}
```

**productIcon** (larger 80x100, dark fill #232F3E — for service-level labels):
```
shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.{name};fillColor=#232F3E
```

**Direct shape** (some shapes are used without wrapper — `users`, `client`, `traditional_server`):
```
shape=mxgraph.aws4.{name}
```

## Category Colors

| Category | Fill Color | Example services |
|----------|-----------|-----------------|
| Compute | `#ED7100` | EC2, ECS, Fargate, Lambda, Batch |
| Containers | `#ED7100` | ECR, ECS, EKS, Fargate |
| Networking | `#8C4FFF` | VPC, Route 53, CloudFront, API Gateway, Direct Connect |
| Database | `#C925D1` | RDS, Aurora, DynamoDB, ElastiCache, Neptune, Redshift |
| Storage | `#3F8624` | S3, EBS, EFS, FSx, Glacier, Backup |
| Security | `#DD344C` | IAM, Cognito, GuardDuty, WAF, Secrets Manager, KMS |
| AI/ML | `#01A88D` | Bedrock, SageMaker, Rekognition, Comprehend, Lex |
| App Integration | `#E7157B` | SQS, SNS, EventBridge, Step Functions, AppSync |
| Management | `#E7157B` | CloudWatch, CloudFormation, CloudTrail, Config |
| Analytics | `#8C4FFF` | Athena, EMR, Kinesis, Glue, QuickSight, OpenSearch |
| Developer Tools | `#C925D1` | CodeBuild, CodePipeline, CodeDeploy, X-Ray |

## Group / Container Shapes

Groups use `shape=mxgraph.aws4.group` with group-specific fill/stroke (not resourceIcon/productIcon):

| Group | Shape name | Typical styling |
|-------|-----------|----------------|
| AWS Cloud | `group_aws_cloud` | `fillColor=none;strokeColor=#232F3E;dashed=1` |
| VPC | `group_vpc` | `fillColor=none;strokeColor=#8C4FFF` |
| Availability Zone | `group_availability_zone` | `fillColor=none;strokeColor=#147EBA;dashed=1` |
| Public Subnet | `group_subnet` | `fillColor=#E9F3E6;strokeColor=#248814` |
| Private Subnet | `group_subnet` | `fillColor=#E6F2F8;strokeColor=#147EBA` |
| Security Group | `group_security_group` | `fillColor=none;strokeColor=#DD344C` |
| Region | `group_region` | `fillColor=none;strokeColor=#00A4A6;dashed=1` |
| Auto Scaling Group | `group_auto_scaling_group` | `fillColor=none;strokeColor=#ED7100;dashed=1` |
| EC2 Instance | `group_ec2_instance_contents` | `fillColor=none;strokeColor=#ED7100` |
| ELB | `group_elastic_load_balancing` | `fillColor=none;strokeColor=#8C4FFF` |
