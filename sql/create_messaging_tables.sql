-- Create messaging tables if they don't exist

-- Enhanced messages table
CREATE TABLE IF NOT EXISTS messages_new (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_user_id INT NOT NULL,
    body TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text' NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at DATETIME NULL,
    delivered_at DATETIME NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at DATETIME NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (sender_user_id) REFERENCES users(user_id)
);

-- Enhanced conversations table
CREATE TABLE IF NOT EXISTS conversations_new (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    relationship_id INT UNIQUE NOT NULL,
    conversation_type VARCHAR(20) DEFAULT 'direct' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL
);

-- Conversation participants table
CREATE TABLE IF NOT EXISTS conversation_participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_read_at DATETIME NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY unique_conversation_user (conversation_id, user_id)
);

-- Online users table
CREATE TABLE IF NOT EXISTS online_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    socket_id VARCHAR(255) NOT NULL,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_online BOOLEAN DEFAULT TRUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Migrate existing data if needed
-- Note: This assumes existing tables might exist with different structure

-- Drop old tables if they exist and rename new ones
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;

RENAME TABLE messages_new TO messages;
RENAME TABLE conversations_new TO conversations;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_user_id);
CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at);
CREATE INDEX IF NOT EXISTS idx_participants_conversation ON conversation_participants(conversation_id);
CREATE INDEX IF NOT EXISTS idx_participants_user ON conversation_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_online_users_user ON online_users(user_id);
