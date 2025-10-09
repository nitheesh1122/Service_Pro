# ServicePro - Smart Household Service Management System

A comprehensive web application that connects house owners with local service providers (plumbers, electricians, cleaners, etc.) based on location and service requirements.

## 🚀 Features

### 👥 User Roles

#### 🏠 **Home Owners (Users)**
- Register and login securely
- Search for service providers by location (pincode) and service category
- View provider profiles, ratings, and reviews
- Book services with date/time selection
- Cancel or modify bookings
- Rate and review completed services
- Real-time chat with service providers

#### 🧑‍🔧 **Service Providers**
- Register and await admin approval
- Set service categories and serviceable areas
- Configure availability and pricing
- Accept/reject booking requests
- Update booking status (Pending → In-progress → Completed)
- View earnings and job history
- Chat with customers

#### 🧑‍💼 **Admin**
- Secure admin login
- Approve/reject service provider registrations
- Manage service categories
- Monitor platform usage and analytics
- View feedback and ratings
- Generate reports

### 🛠️ Core Features

- **📍 Location-Based Search**: Find providers by pincode/zip code
- **📅 Booking System**: Schedule services with date/time selection
- **💬 Real-Time Chat**: WebSocket-based messaging system
- **⭐ Rating & Review System**: Rate completed services
- **📊 Analytics Dashboard**: Admin monitoring and reporting
- **📱 Responsive Design**: Mobile-friendly interface
- **🔐 Secure Authentication**: Session-based login system

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Real-time Communication**: Flask-SocketIO
- **Authentication**: Flask-Login
- **ORM**: SQLAlchemy

## 📋 Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ServicePro
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Option A: Using MySQL Command Line
```bash
mysql -u root -p < database_setup.sql
```

#### Option B: Manual Setup
1. Create MySQL database:
```sql
CREATE DATABASE servicepro_db;
```

2. Update database configuration in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/servicepro_db'
```

### 5. Environment Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=mysql+pymysql://username:password@localhost/servicepro_db
FLASK_ENV=development
FLASK_DEBUG=True
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 👤 Default Login Credentials

### Admin Account
- **Email**: admin@servicepro.com
- **Password**: admin123

## 📁 Project Structure

```
ServicePro/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── database_setup.sql    # Database setup script
├── README.md            # Project documentation
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Homepage
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── user_dashboard.html      # User dashboard
│   ├── provider_dashboard.html  # Provider dashboard
│   ├── admin_dashboard.html     # Admin dashboard
│   ├── search_results.html     # Search results
│   ├── book_service.html       # Booking page
│   └── chat.html              # Chat interface
└── static/             # Static files (CSS, JS, images)
```

## 🗄️ Database Schema

### Core Tables

1. **user** - User accounts (homeowners, providers, admin)
2. **service_provider** - Provider-specific information
3. **service** - Available service categories
4. **booking** - Service booking records
5. **review** - User reviews and ratings
6. **message** - Chat messages

### Key Relationships
- Users can be homeowners, providers, or admin
- Service providers have additional profile information
- Bookings connect users with providers for specific services
- Reviews are linked to completed bookings
- Messages enable communication between users

## 🎯 Usage Guide

### For Homeowners
1. **Register** as a user
2. **Search** for service providers by location and service type
3. **Book** services with preferred date/time
4. **Chat** with providers for details
5. **Rate** completed services

### For Service Providers
1. **Register** as a service provider
2. **Wait** for admin approval
3. **Complete** profile with services and areas
4. **Accept** booking requests
5. **Update** job status as work progresses

### For Admins
1. **Login** with admin credentials
2. **Review** pending provider applications
3. **Approve/Reject** provider registrations
4. **Monitor** platform activity
5. **Manage** service categories

## 🔧 Configuration

### Database Configuration
Update the database connection string in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/servicepro_db'
```

### Email Configuration (Future Enhancement)
Add email settings to `.env`:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 🚀 Deployment

### Production Deployment
1. Set `FLASK_ENV=production`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure a reverse proxy (Nginx)
4. Set up SSL certificates
5. Use a production database

### Docker Deployment (Future Enhancement)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🔮 Future Enhancements

- **📍 Google Maps Integration**: Location-based provider matching
- **💳 Payment Integration**: Online payment processing
- **📱 Mobile App**: Native mobile applications
- **🤖 AI Recommendations**: Smart provider suggestions
- **🔔 Push Notifications**: Real-time alerts
- **📊 Advanced Analytics**: Detailed reporting and insights
- **🌐 Multi-language Support**: Internationalization
- **📄 Invoice Generation**: Automatic invoice creation

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify MySQL is running
   - Check database credentials
   - Ensure database exists

2. **Import Errors**
   - Activate virtual environment
   - Install all requirements: `pip install -r requirements.txt`

3. **Socket.IO Issues**
   - Check if port 5000 is available
   - Verify WebSocket support in browser

### Logs
Check application logs for detailed error information:
```bash
python app.py 2>&1 | tee app.log
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Email: support@servicepro.com
- Documentation: [Project Wiki]
- Issues: [GitHub Issues]

---

**ServicePro** - Connecting homeowners with trusted service providers since 2024! 🏠🔧 