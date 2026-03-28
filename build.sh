#!/bin/bash

echo "🚀 Building Smart CPMS Project..."

# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Clear old static files and collect new ones
echo "📁 Collecting Static Files..."
python manage.py collectstatic --noinput --clear

# Step 3: Run database migrations
echo "⚙️ Running Database Migrations..."
python manage.py migrate --noinput

echo "✅ Build Completed Successfully!"
