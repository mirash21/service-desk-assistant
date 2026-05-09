#!/bin/bash
# Script to setup SSL certificates with Let's Encrypt
# Usage: sudo ./setup_ssl.sh admin.yourdomain.com

set -e

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "❌ Usage: sudo $0 <your-domain.com>"
    echo "Example: sudo $0 admin.example.com"
    exit 1
fi

echo "🔒 Setting up SSL for $DOMAIN"
echo "=============================="

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "⚠️  certbot not found. Installing..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Stop Nginx temporarily (certbot needs port 80)
echo "🛑 Stopping Nginx..."
systemctl stop nginx

# Obtain certificate
echo "📜 Obtaining SSL certificate..."
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"

# Start Nginx
echo "▶️  Starting Nginx..."
systemctl start nginx

echo ""
echo "✅ SSL certificate obtained successfully!"
echo "📄 Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "🔑 Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo ""
echo "Next steps:"
echo "1. Update nginx.conf with your domain name"
echo "2. Copy nginx.conf to /etc/nginx/sites-available/"
echo "3. Enable the site and reload Nginx"
echo ""
echo "Auto-renewal test:"
echo "sudo certbot renew --dry-run"
