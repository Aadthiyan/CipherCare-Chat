# CipherCare Authentication Setup - Quick Start
# Run this script to set up and test the authentication system

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "CipherCare Authentication System - Quick Start" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Function to check if command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Step 1: Check Prerequisites
Write-Host "`n📋 Step 1: Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-CommandExists python)) {
    Write-Host "❌ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

if (-not (Test-CommandExists node)) {
    Write-Host "❌ Node.js not found! Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python found: $((python --version))" -ForegroundColor Green
Write-Host "✅ Node.js found: $((node --version))" -ForegroundColor Green

# Step 2: Install Python Dependencies
Write-Host "`n📦 Step 2: Installing Python dependencies..." -ForegroundColor Yellow

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Gray
& .venv\Scripts\Activate.ps1

Write-Host "Installing requirements..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

Write-Host "✅ Python dependencies installed" -ForegroundColor Green

# Step 3: Check Environment Configuration
Write-Host "`n🔧 Step 3: Checking environment configuration..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ .env file found" -ForegroundColor Green

# Check for required environment variables
$envContent = Get-Content .env -Raw
$requiredVars = @("DATABASE_URL", "JWT_SECRET_KEY", "BREVO_API_KEY")
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not ($envContent -match "$var=.+")) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "⚠️  Warning: Missing or empty environment variables:" -ForegroundColor Yellow
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Yellow
    }
    Write-Host "`n💡 Please update your .env file with these values" -ForegroundColor Cyan
    
    if ($missingVars -contains "BREVO_API_KEY") {
        Write-Host "`n   Get Brevo API key from: https://app.brevo.com" -ForegroundColor Cyan
    }
    
    if ($missingVars -contains "JWT_SECRET_KEY") {
        Write-Host "`n   Generate JWT secret: openssl rand -hex 32" -ForegroundColor Cyan
    }
} else {
    Write-Host "✅ All required environment variables are set" -ForegroundColor Green
}

# Step 4: Setup Database
Write-Host "`n🗄️  Step 4: Setting up database..." -ForegroundColor Yellow

$setupResult = python setup_auth.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database setup completed" -ForegroundColor Green
} else {
    Write-Host "❌ Database setup failed! Check errors above" -ForegroundColor Red
    exit 1
}

# Step 5: Install Frontend Dependencies
Write-Host "`n📦 Step 5: Installing frontend dependencies..." -ForegroundColor Yellow

Push-Location frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages..." -ForegroundColor Gray
    npm install
} else {
    Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
}

Pop-Location

Write-Host "✅ Frontend setup complete" -ForegroundColor Green

# Success Summary
Write-Host "`n" + "=" * 70 -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green

Write-Host "`n🚀 To start the application:" -ForegroundColor Cyan
Write-Host "`n1. Start Backend (in terminal 1):" -ForegroundColor White
Write-Host "   .venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray

Write-Host "`n2. Start Frontend (in terminal 2):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray

Write-Host "`n3. Access Application:" -ForegroundColor White
Write-Host "   Login: http://localhost:3000/auth/login" -ForegroundColor Gray
Write-Host "   Signup: http://localhost:3000/auth/signup" -ForegroundColor Gray
Write-Host "   Dashboard: http://localhost:3000/dashboard" -ForegroundColor Gray

Write-Host "`n🔐 Default Credentials:" -ForegroundColor White
Write-Host "   Username: attending | Password: password123" -ForegroundColor Gray
Write-Host "   Username: resident  | Password: password123" -ForegroundColor Gray

Write-Host "`n⚠️  Change default passwords in production!" -ForegroundColor Yellow

Write-Host "`n📚 Documentation:" -ForegroundColor White
Write-Host "   See AUTH_IMPLEMENTATION_GUIDE.md for detailed information" -ForegroundColor Gray

Write-Host ""
