# Troop 202 Website

Modern, secure static website for Boy Scout Troop 202 hosted on AWS with automated CI/CD deployment.

🌐 **Live Site**: [https://troop202.site](https://troop202.site)

## Architecture Overview

This website uses a modern AWS-based architecture for high performance, security, and reliability:

### Infrastructure Components
- **Static Website Hosting**: S3 bucket with CloudFront CDN for global performance
- **SSL/TLS**: AWS Certificate Manager with automated renewal
- **Security**: WAF (Web Application Firewall) with rate limiting and threat protection
- **DNS**: Route 53 for domain management with both apex and www domains
- **Monitoring**: CloudWatch logs with KMS encryption for security
- **CI/CD**: GitHub Actions with OIDC authentication (no stored secrets)

### Stack Architecture
The infrastructure is split into independent stacks for faster development iterations:

1. **Foundation Stack** (`foundation.yaml`)
   - S3 buckets (website + CloudFront logs)
   - WAF Web ACL with security rules
   - KMS key for log encryption
   - Origin Access Control (OAC) for secure S3 access
   - *Deploy time: ~2-3 minutes*

2. **CloudFront Stack** (`cloudfront.yaml`)
   - CloudFront distribution with security headers
   - Route 53 DNS records (apex + www)
   - S3 bucket policy for CloudFront access
   - *Deploy time: ~15-20 minutes (due to CloudFront propagation)*

3. **Monitoring Stack** (`monitoring.yaml`)
   - CloudWatch log groups for website and access logs
   - KMS-encrypted logs with configurable retention
   - *Deploy time: ~1-2 minutes*

## Deployment Workflows

### Infrastructure Deployment
- **Trigger**: Push to `main` with CloudFormation changes or manual dispatch
- **Workflow**: `.github/workflows/deploy-infrastructure.yml`
- **Process**: Sequential deployment of foundation → CloudFront → monitoring
- **Permissions**: Uses OIDC role with least-privilege AWS access

### Content Deployment
- **Trigger**: Push to `main` with `website/` changes, after infrastructure deployment, or manual dispatch
- **Workflow**: `.github/workflows/deploy-content.yml` 
- **Process**: Syncs `website/` folder to S3, invalidates CloudFront cache
- **Optimization**: Different cache headers for HTML vs static assets

## Development Setup

### Prerequisites
- AWS CLI configured with appropriate permissions
- GitHub repository secrets configured:
  - `AWS_ROLE_ARN`: IAM role for GitHub Actions OIDC
  - `HOSTED_ZONE_ID`: Route 53 hosted zone for domain

### Local Development
1. Clone the repository
2. Edit files in the `website/` directory
3. Test locally by opening `website/index.html` in a browser
4. Commit and push to trigger automated deployment

### Infrastructure Management
All infrastructure is defined as code in the `cloudformation/` directory:

```
cloudformation/
├── foundation.yaml          # Core infrastructure (S3, WAF, KMS)
├── cloudfront.yaml         # CDN and DNS configuration  
├── monitoring.yaml         # Logging and monitoring
├── ssl-certificate.yaml   # SSL certificate (deploy once)
├── github-actions-setup.yaml # CI/CD permissions setup
└── github-actions-iam-policy.json # IAM policy definition
```

## Key Features

### Security
- **HTTPS Enforced**: All traffic redirected to HTTPS
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **WAF Protection**: Rate limiting, bot protection, OWASP rule sets
- **Origin Security**: S3 bucket not publicly accessible, only via CloudFront

### Performance  
- **Global CDN**: CloudFront edge locations worldwide
- **Optimized Caching**: Different strategies for HTML vs static assets
- **HTTP/2 + HTTP/3**: Modern protocol support
- **Compression**: Automatic gzip/brotli compression

### Reliability
- **Multi-Stack Architecture**: Independent deployments reduce blast radius
- **Automated Rollbacks**: CloudFormation handles failed deployments
- **Infrastructure as Code**: Reproducible, version-controlled infrastructure
- **Monitoring**: CloudWatch logs and metrics for observability

## Troubleshooting

### Common Issues

**KMS Tagging Permissions**: If you see KMS tagging errors during deployment, the GitHub Actions role has been configured with full KMS permissions (`kms:*`) to handle CloudFormation's complex tagging requirements.

**Empty S3 Bucket**: If the website shows Access Denied errors, ensure the content deployment workflow has run successfully to upload files from `website/` to S3.

**Stack Dependencies**: Deploy stacks in order: foundation → CloudFront → monitoring. The content deployment requires both foundation and CloudFront stacks to exist.

**CloudFront Propagation**: CloudFront deployments take 15-20 minutes. DNS changes may take additional time to propagate globally.

### Manual Commands

Deploy infrastructure locally (requires AWS admin permissions):
```bash
# Foundation stack (required first)
aws cloudformation deploy \
  --template-file cloudformation/foundation.yaml \
  --stack-name prod-troop202-foundation \
  --parameter-overrides Environment=prod \
  --capabilities CAPABILITY_IAM

# CloudFront stack (requires foundation)
aws cloudformation deploy \
  --template-file cloudformation/cloudfront.yaml \
  --stack-name prod-troop202-cloudfront \
  --parameter-overrides Environment=prod HostedZoneId=<your-zone-id> \
  --capabilities CAPABILITY_IAM
```

Upload content manually:
```bash
aws s3 sync website/ s3://prod-troop202-website-<account-id>/ --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

## Repository Structure

```
.
├── .github/
│   └── workflows/           # GitHub Actions CI/CD workflows
├── cloudformation/          # AWS infrastructure templates
├── website/                # Static website content
│   ├── index.html         # Homepage
│   └── error.html         # 404 error page
└── README.md              # This file
```

---

Built with ❤️ for Boy Scout Troop 202
