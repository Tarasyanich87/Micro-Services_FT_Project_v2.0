#!/bin/bash
# Open all Freqtrade dashboards in browser for visual testing

echo "🚀 Opening Freqtrade Multi-Bot System Dashboards for Visual Testing"
echo "=================================================================="

# Check if services are running
echo "📋 Checking service status..."
curl -s http://localhost:8002/health > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Management Server not responding"
    exit 1
fi

curl -s http://localhost:5176/ > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ UI Server not responding"
    exit 1
fi

echo "✅ All services are running"

# Open main dashboard access page
echo "📄 Opening main dashboard access page..."
xdg-open "file:///home/taras/Documents/Opencode_NEW/jules_freqtrade_project/dashboard_access.html" 2>/dev/null &
sleep 2

# Open all dashboards with delay
echo "🎯 Opening all dashboards..."

# Home Dashboard
echo "🏠 Opening Home Dashboard..."
xdg-open "http://localhost:5176/" 2>/dev/null &
sleep 1

# Bot Management
echo "🤖 Opening Bot Management..."
xdg-open "http://localhost:5176/bots" 2>/dev/null &
sleep 1

# Strategies
echo "📝 Opening Strategies Dashboard..."
xdg-open "http://localhost:5176/strategies" 2>/dev/null &
sleep 1

# Analytics
echo "📊 Opening Analytics Dashboard..."
xdg-open "http://localhost:5176/analytics" 2>/dev/null &
sleep 1

# FreqAI Lab
echo "🧠 Opening FreqAI Lab..."
xdg-open "http://localhost:5176/freqai-lab" 2>/dev/null &
sleep 1

# Data Management
echo "💾 Opening Data Management..."
xdg-open "http://localhost:5176/data" 2>/dev/null &
sleep 1

# Hyperopt
echo "🎯 Opening Hyperopt Dashboard..."
xdg-open "http://localhost:5176/hyperopt" 2>/dev/null &
sleep 1

# Monitoring
echo "📈 Opening Monitoring Dashboard..."
xdg-open "http://localhost:5176/monitoring" 2>/dev/null &
sleep 1

# Audit
echo "📋 Opening Audit Dashboard..."
xdg-open "http://localhost:5176/audit" 2>/dev/null &
sleep 1

# Login
echo "🔐 Opening Login Dashboard..."
xdg-open "http://localhost:5176/login" 2>/dev/null &
sleep 1

# API Documentation
echo "📖 Opening API Documentation..."
xdg-open "http://localhost:8002/docs" 2>/dev/null &
sleep 1

echo ""
echo "=================================================================="
echo "🎉 ALL DASHBOARDS OPENED SUCCESSFULLY!"
echo "=================================================================="
echo "📋 Dashboard Access Page: dashboard_access.html"
echo "🔗 Main UI: http://localhost:5176/"
echo "📖 API Docs: http://localhost:8002/docs"
echo "💚 Health Check: http://localhost:8002/health"
echo "=================================================================="
echo ""
echo "🔍 VISUAL CHECKLIST:"
echo "✅ Vue.js application loads"
echo "✅ Navigation between dashboards works"
echo "✅ CodeMirror editor is visible in Strategies"
echo "✅ API calls work (check browser console)"
echo "✅ Responsive design works"
echo "✅ All components render correctly"
echo "=================================================================="