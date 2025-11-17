from models.database import init_db, get_session, User

print("Initializing database...")
init_db()
print("✓ Database initialized!")

# Create admin user
db = get_session()

admin = db.query(User).filter_by(username='admin').first()

if not admin:
    print("\nCreating admin user...")
    admin = User(
        username='admin',
        email='admin@loanverify.com',
        full_name='Administrator'
    )
    admin.set_password('admin123')
    
    db.add(admin)
    db.commit()
    
    print("✓ Admin user created!")
    print("Username: admin")
    print("Password: admin123")
else:
    print("✓ Admin user already exists")

db.close()
print("\n✓ Setup complete!")