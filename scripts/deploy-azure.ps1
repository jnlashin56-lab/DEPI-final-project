# Deploy the FastAPI backend to Azure Container Apps.
# Prerequisites: Azure CLI (az), Docker not required (uses ACR cloud build).
#
# Usage:
#   1. Fill in the variables below (or pass as parameters).
#   2. Run: .\scripts\deploy-azure.ps1
#
# After deploy:
#   - Set VITE_API_BASE on Vercel to the printed API URL and redeploy the frontend.

param(
    [string]$ResourceGroup = "depi-rg",
    [string]$Location = "westeurope",
    [string]$AcrName = "depiacr$(Get-Random -Maximum 99999)",
    [string]$ContainerAppName = "cultural-recommender-api",
    [string]$ContainerEnvName = "depi-env",
    [string]$ImageName = "cultural-api",
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$AzureApiKey = $env:AZURE_API_KEY,
    [string]$AdminUsername = $env:ADMIN_USERNAME,
    [string]$AdminPassword = $env:ADMIN_PASSWORD,
    [string]$JwtSecret = $env:JWT_SECRET
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI (az) is not installed. Install from https://learn.microsoft.com/cli/azure/install-azure-cli"
}

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Logging in to Azure..."
    az login | Out-Null
}

if (-not $DatabaseUrl) {
    $DatabaseUrl = Read-Host "Supabase DATABASE_URL (postgresql://...?sslmode=require)"
}
if (-not $AzureApiKey) {
    $AzureApiKey = Read-Host "AZURE_API_KEY" -AsSecureString
    $AzureApiKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($AzureApiKey)
    )
}
if (-not $AdminPassword) {
    $AdminPassword = Read-Host "ADMIN_PASSWORD (for /admin login)" -AsSecureString
    $AdminPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword)
    )
}
if (-not $AdminUsername) { $AdminUsername = "admin" }
if (-not $JwtSecret) { $JwtSecret = [guid]::NewGuid().ToString("N") }

Write-Host "`n=== Creating resource group ===" -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location | Out-Null

Write-Host "=== Creating Azure Container Registry ===" -ForegroundColor Cyan
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true | Out-Null

Write-Host "=== Building Docker image in ACR (may take 10-15 min) ===" -ForegroundColor Cyan
Push-Location $ProjectRoot
az acr build --registry $AcrName --image "${ImageName}:latest" . 
Pop-Location

Write-Host "=== Creating Container Apps environment ===" -ForegroundColor Cyan
az containerapp env create `
    --name $ContainerEnvName `
    --resource-group $ResourceGroup `
    --location $Location | Out-Null

$acrLoginServer = az acr show --name $AcrName --query loginServer -o tsv
$acrPassword = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv

Write-Host "=== Deploying Container App ===" -ForegroundColor Cyan
az containerapp create `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --environment $ContainerEnvName `
    --image "${acrLoginServer}/${ImageName}:latest" `
    --registry-server $acrLoginServer `
    --registry-username $AcrName `
    --registry-password $acrPassword `
    --target-port 8000 `
    --ingress external `
    --cpu 1.0 `
    --memory 4.0Gi `
    --min-replicas 1 `
    --max-replicas 1 `
    --secrets `
        database-url=$DatabaseUrl `
        azure-api-key=$AzureApiKey `
        admin-password=$AdminPassword `
        jwt-secret=$JwtSecret `
    --env-vars `
        DATABASE_URL=secretref:database-url `
        AZURE_API_KEY=secretref:azure-api-key `
        ADMIN_USERNAME=$AdminUsername `
        ADMIN_PASSWORD=secretref:admin-password `
        JWT_SECRET=secretref:jwt-secret `
        EMBEDDING_MODEL=intfloat/multilingual-e5-base | Out-Null

$fqdn = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
$apiUrl = "https://$fqdn"

Write-Host "`n=== Deployment complete ===" -ForegroundColor Green
Write-Host "API URL: $apiUrl"
Write-Host "Health:  $apiUrl/health"
Write-Host "Docs:    $apiUrl/docs"
Write-Host "`nNext steps:"
Write-Host "  1. Open $apiUrl/health and confirm database=true"
Write-Host "  2. In Vercel, set environment variable:"
Write-Host "       VITE_API_BASE=$apiUrl"
Write-Host "  3. Redeploy the frontend on Vercel"
