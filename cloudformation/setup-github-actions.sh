#!/bin/bash

# Setup script for GitHub Actions IAM Role and OIDC Provider
# Usage: ./setup-github-actions.sh [github-org] [github-repo] [github-branch]

set -euo pipefail

# Configuration
GITHUB_ORG="${1:-peter-mxtoolbox}"
GITHUB_REPO="${2:-Troop202Website}"
GITHUB_BRANCH="${3:-main}"
STACK_NAME="troop202-github-actions-setup"
REGION="us-east-1"
TEMPLATE_FILE="github-actions-setup.yaml"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation
validate_inputs() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check if template file exists
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "CloudFormation template not found: $TEMPLATE_FILE"
        exit 1
    fi
    
    log_info "✅ All prerequisites validated"
}

# Check if OIDC provider already exists
check_existing_oidc() {
    local oidc_exists
    oidc_exists=$(aws iam list-open-id-connect-providers \
        --query 'OpenIDConnectProviderList[?contains(Arn, `token.actions.githubusercontent.com`)].Arn' \
        --output text)
    
    if [ -n "$oidc_exists" ]; then
        log_warning "GitHub OIDC provider already exists: $oidc_exists"
        log_warning "The template will attempt to create a new one, which may fail."
        log_warning "Consider updating the template to use the existing provider or delete the existing one."
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
}

# Deploy the CloudFormation stack
deploy_stack() {
    log_info "Deploying GitHub Actions setup stack..."
    log_info "GitHub Org: $GITHUB_ORG"
    log_info "GitHub Repo: $GITHUB_REPO"
    log_info "GitHub Branch: $GITHUB_BRANCH"
    log_info "Stack Name: $STACK_NAME"
    log_info "Region: $REGION"
    echo
    
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --parameter-overrides \
            GitHubOrg="$GITHUB_ORG" \
            GitHubRepo="$GITHUB_REPO" \
            GitHubBranch="$GITHUB_BRANCH" \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags \
            Project="Troop202Website" \
            ManagedBy="CLI-Deployment" \
            GitHubOrg="$GITHUB_ORG" \
            GitHubRepo="$GITHUB_REPO" \
        --no-fail-on-empty-changeset
    
    if [ $? -eq 0 ]; then
        log_success "Stack deployed successfully!"
    else
        log_error "Stack deployment failed"
        exit 1
    fi
}

# Get outputs and provide next steps
show_outputs() {
    log_info "Retrieving stack outputs..."
    
    # Get the role ARN
    ROLE_ARN=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`GitHubActionsRoleArn`].OutputValue' \
        --output text)
    
    if [ -z "$ROLE_ARN" ]; then
        log_error "Could not retrieve Role ARN from stack outputs"
        exit 1
    fi
    
    echo
    log_success "🎉 GitHub Actions setup completed successfully!"
    echo
    log_info "📋 Next Steps:"
    echo
    echo "1. 🔐 Add the following secrets to your GitHub repository:"
    echo "   Repository: https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/secrets/actions"
    echo
    echo "   Secret Name: AWS_ROLE_ARN"
    echo "   Secret Value: $ROLE_ARN"
    echo
    echo "   Secret Name: HOSTED_ZONE_ID"
    echo "   Secret Value: <your-route53-hosted-zone-id-for-troop202.site>"
    echo
    echo "2. 🚀 You can now run the GitHub Actions workflows to deploy your infrastructure:"
    echo "   - Go to Actions tab in your GitHub repository"
    echo "   - Run 'Deploy Infrastructure' workflow"
    echo
    log_info "💡 The IAM role ARN has also been stored in SSM Parameter: /github-actions/troop202/role-arn"
    echo
}

# Cleanup function for failed deployments
cleanup_on_failure() {
    if [ $? -ne 0 ]; then
        log_warning "Deployment failed. Checking for partial stack creation..."
        
        if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" >/dev/null 2>&1; then
            log_warning "Stack exists but deployment failed. You may want to delete it manually:"
            log_warning "aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"
        fi
    fi
}

# Set up trap for cleanup
trap cleanup_on_failure EXIT

# Main execution
main() {
    echo
    log_info "🚀 Setting up GitHub Actions OIDC and IAM Role for Troop 202"
    echo
    
    validate_inputs
    check_existing_oidc
    deploy_stack
    show_outputs
    
    # Disable the trap since we succeeded
    trap - EXIT
}

# Show usage if help is requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [github-org] [github-repo] [github-branch]"
    echo
    echo "This script deploys a CloudFormation template that creates:"
    echo "  - GitHub OIDC Identity Provider"
    echo "  - IAM Role with appropriate permissions"
    echo "  - IAM Policy for infrastructure deployment"
    echo
    echo "Parameters:"
    echo "  github-org     GitHub organization or username (default: peter-mxtoolbox)"
    echo "  github-repo    GitHub repository name (default: Troop202Website)"
    echo "  github-branch  GitHub branch for OIDC trust (default: main)"
    echo
    echo "Prerequisites:"
    echo "  - AWS CLI installed and configured"
    echo "  - Appropriate AWS permissions to create IAM resources"
    echo "  - CloudFormation template file: github-actions-setup.yaml"
    echo
    exit 0
fi

# Run main function
main "$@"