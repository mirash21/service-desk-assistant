#!/bin/bash
# Script to setup Basic Authentication for Admin Panel
# Usage: sudo ./setup_basic_auth.sh

set -e

echo "🔐 Setting up Basic Authentication for Admin Panel"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo)"
    exit 1
fi

# Check if htpasswd is available
if ! command -v htpasswd &> /dev/null; then
    echo "⚠️  htpasswd not found. Installing apache2-utils..."
    apt-get update && apt-get install -y apache2-utils
fi

# Prompt for username
read -p "Enter admin username [admin]: " USERNAME
USERNAME=${USERNAME:-admin}

# Prompt for password
read -s -p "Enter admin password: " PASSWORD
echo ""

# Create .htpasswd file
HTPASSWD_FILE="/etc/nginx/.htpasswd"
echo "📝 Creating $HTPASSWD_FILE..."

htpasswd -cb $HTPASSWD_FILE "$USERNAME" "$PASSWORD"

# Set proper permissions
chmod 640 $HTPASSWD_FILE
chown root:www-data $HTPASSWD_FILE

echo ""
echo "✅ Basic Auth configured successfully!"
echo "📄 File: $HTPASSWD_FILE"
echo "👤 Username: $USERNAME"
echo ""
echo "Next steps:"
echo "1. Copy nginx.conf to /etc/nginx/sites-available/admin-panel.conf"
echo "2. Update server_name in nginx.conf with your domain"
echo "3. Setup SSL certificates with Let's Encrypt"
echo "4. Enable the site: sudo ln -s /etc/nginx/sites-available/admin-panel.conf /etc/nginx/sites-enabled/"
echo "5. Test config: sudo nginx -t"
echo "6. Reload Nginx: sudo systemctl reload nginx"
