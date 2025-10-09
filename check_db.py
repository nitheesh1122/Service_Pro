#!/usr/bin/env python3

import sys
import os
sys.path.append('d:\\ServicePro')

try:
    from app import app, db, Service, ServiceProvider

    with app.app_context():
        services = Service.query.filter_by(is_active=True).all()
        print('Available Services:')
        for service in services:
            print(f'  ID: {service.id}, Category: "{service.category}", Base Price: {service.base_price}')

        # Check a few providers
        providers = ServiceProvider.query.limit(5).all()
        print(f'\nFound {len(providers)} providers:')

        for provider in providers:
            print(f'  Provider ID: {provider.id}, User ID: {provider.user_id}, Services: "{provider.service_categories}"')

        # Check if there are any users
        from app import User
        users = User.query.filter_by(role='provider').limit(5).all()
        print(f'\nFound {len(users)} provider users:')
        for user in users:
            print(f'  User: {user.name} ({user.email}), Provider ID: {getattr(user.service_provider, "id", "None")}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
