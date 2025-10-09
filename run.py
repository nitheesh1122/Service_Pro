#!/usr/bin/env python3
"""
ServicePro - Startup Script
Run this file to start the ServicePro application
"""

from app import app, socketio

if __name__ == '__main__':
    print("🚀 Starting ServicePro...")
    print("📱 Application will be available at: http://localhost:5000")
    print("👤 Admin login: admin@servicepro.com / admin123")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 ServicePro stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting ServicePro: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt") 