from app import app
from db import db
from sqlalchemy import text

# Create table without foreign key first
with app.app_context():
    # Drop the table if it exists to start fresh
    try:
        db.session.execute(text("DROP TABLE IF EXISTS client_progress_photos"))
        db.session.commit()
        print("Dropped existing table")
    except:
        pass
    
    # Create table without foreign key
    create_table_sql = """
    CREATE TABLE client_progress_photos (
        photo_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT NOT NULL,
        before_photo_url VARCHAR(500) NULL,
        after_photo_url VARCHAR(500) NULL,
        uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    db.session.execute(text(create_table_sql))
    db.session.commit()
    print("Table created successfully")
