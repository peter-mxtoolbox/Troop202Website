# Troop 202 Website Infrastructure

This repository contains CloudFormation templates and GitHub Actions workflows for deploying a secure, scalable static website infrastructure on AWS.

## 🏗️ Architecture Overview

The infrastructure consists of:

- **SSL Certificate**: Managed by AWS Certificate Manager with DNS validation
- **S3 Bucket**: Secure storage for website content with versioning and encryption
- **CloudFront Distribution**: Global CDN with security headers and WAF protection
- **WAF (Web Application Firewall)**: Protection against common web attacks
- **CloudWatch Monitoring**: Logs and metrics with custom dashboard
- **Route 53**: DNS management (external requirement)

## 📁 Project Structure

```
cloudformation/
├── ssl-certificate.yaml        # SSL certificate with SSM parameter storage
├── static-website.yaml         # Main website infrastructure
└── README.md                  # This file

.github/workflows/
├── deploy-infrastructure.yml   # Deploy CloudFormation stacks
└── deploy-content.yml          # Deploy website content to S3

website/                        # Your website files go here
└── index.html                 # Required: main landing page
```

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **Route 53 Hosted Zone** for `troop202.site`
3. **GitHub Secrets** configured (see setup section)
4. **Website Content** in the `website/` directory

### 1. Setup GitHub Secrets

Configure the following secrets in your GitHub repository settings:

```bash
AWS_ROLE_ARN=arn:aws:iam::YOUR-ACCOUNT:role/GitHubActionsRole
HOSTED_ZONE_ID=Z1234567890ABC  # Your Route 53 hosted zone ID
```

### 2. Setup AWS IAM Role for GitHub Actions

Create an IAM role with OIDC trust relationship for GitHub Actions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR-ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:YOUR-USERNAME/Troop202Website:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Attach these managed policies to the role:
- `PowerUserAccess` (or create custom policy with specific permissions)

### 3. Deploy Infrastructure

#### Option A: Manual Deployment via GitHub Actions

1. Go to **Actions** tab in your GitHub repository
2. Select **Deploy Infrastructure** workflow
3. Click **Run workflow**
4. Choose your environment (dev/staging/prod)
5. Enter your Route 53 Hosted Zone ID
6. Click **Run workflow**

#### Option B: Automatic Deployment

Push changes to the `main` branch or CloudFormation files to trigger automatic deployment to the `prod` environment.

### 4. Deploy Website Content

1. Add your website files to the `website/` directory
2. Ensure you have an `index.html` file
3. Push changes to trigger automatic content deployment
4. Or use the **Deploy Website Content** workflow manually

## 🔧 Configuration Options

### Environment Variables

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `Environment` | Deployment environment | `prod` | `dev`, `staging`, `prod` |
| `DomainName` | Primary domain name | `troop202.site` | Any valid domain |
| `PriceClass` | CloudFront price class | `PriceClass_100` | `PriceClass_All`, `PriceClass_200`, `PriceClass_100` |

### Security Features

- **SSL/TLS**: Automatic HTTPS with AWS Certificate Manager
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **WAF Protection**: AWS managed rules + rate limiting
- **S3 Security**: Private bucket with Origin Access Control
- **Encryption**: Server-side encryption for all data at rest

### Performance Optimizations

- **Global CDN**: CloudFront with optimized caching
- **Compression**: Automatic gzip/brotli compression
- **HTTP/2**: Latest HTTP protocol support
- **Cache Control**: Optimized cache headers for different file types

## 📊 Monitoring & Observability

### CloudWatch Dashboard

Access your monitoring dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=prod-Troop202-Website
```

### Key Metrics

- Request count and error rates
- Data transfer and bandwidth usage
- WAF blocked/allowed requests
- SSL certificate expiration monitoring

### Log Groups

- CloudFront access logs: `/aws/cloudfront/prod-troop202`
- S3 access logs: Stored in dedicated S3 bucket

## 🔒 Security Best Practices

### Implemented Security Measures

1. **Origin Access Control (OAC)**: CloudFront-only access to S3
2. **Public Access Block**: Prevents accidental public S3 exposure
3. **WAF Rules**: Protection against OWASP Top 10 vulnerabilities
4. **Security Headers**: Comprehensive browser security
5. **Encryption**: AES-256 for S3, TLS 1.2+ for CloudFront
6. **Versioning**: S3 object versioning for recovery

### SSL Certificate Management

- Automatic DNS validation via Route 53
- Stored in SSM Parameter Store for cross-stack reference
- 90-day expiration monitoring and auto-renewal

## 🛠️ Maintenance

### Regular Tasks

1. **Monitor Certificate Expiration**: Automatic renewal by AWS
2. **Review WAF Logs**: Check for blocked attacks
3. **Update Security Rules**: Keep WAF rules current
4. **Backup Content**: S3 versioning provides automatic backup

### Updating Infrastructure

1. Modify CloudFormation templates
2. Commit changes to repository
3. GitHub Actions will deploy automatically
4. Monitor deployment in Actions tab

### Cost Optimization

- Use `PriceClass_100` for cost-effective global distribution
- Enable S3 lifecycle policies for old object versions
- Monitor CloudWatch costs and adjust retention periods

## 🚨 Troubleshooting

### Common Issues

#### SSL Certificate Validation Fails
- Verify Route 53 hosted zone is correct
- Check domain ownership
- Ensure DNS propagation is complete

#### CloudFront 403 Errors
- Verify S3 bucket policy allows CloudFront access
- Check Origin Access Control configuration
- Ensure files exist in S3 bucket

#### WAF Blocking Legitimate Traffic
- Review WAF logs in CloudWatch
- Adjust rate limits if needed
- Whitelist known good IP ranges if required

### Support Resources

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Certificate Manager Documentation](https://docs.aws.amazon.com/acm/)

## 📝 Development Workflow

### Making Changes

1. **Infrastructure Changes**: Edit CloudFormation templates
2. **Content Changes**: Update files in `website/` directory
3. **Workflow Changes**: Modify GitHub Actions workflows
4. **Test Changes**: Use dev/staging environments first

### Branch Protection

It's recommended to:
1. Require pull requests for `main` branch
2. Enable status checks for workflows
3. Require reviews before merging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in a dev environment
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Need Help?** Open an issue in this repository or contact the development team.