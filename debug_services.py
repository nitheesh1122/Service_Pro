#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Service, ServiceProvider

with app.app_context():
    services = Service.query.filter_by(is_active=True).all()
    print('Available Services:')
    for service in services:
        print(f'  ID: {service.id}, Category: "{service.category}", Base Price: {service.base_price}')
    
    # Check a few providers
    providers = ServiceProvider.query.limit(3).all()
    print('\nSample Providers:')
    for provider in providers:
        print(f'  Provider ID: {provider.id}, Services: "{provider.service_categories}"')
