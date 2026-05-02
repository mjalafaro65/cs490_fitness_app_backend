-- Create client_progress_photos table
CREATE TABLE IF NOT EXISTS client_progress_photos (
    photo_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    before_photo_url VARCHAR(500) NULL,
    after_photo_url VARCHAR(500) NULL,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(user_id)
);
