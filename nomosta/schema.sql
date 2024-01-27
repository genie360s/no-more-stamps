-- Create table 'user'
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    fullname TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table 'document'
CREATE TABLE document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_name VARCHAR(255),
    document_file BLOB,
    timestamped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Create table 'qrcode'
CREATE TABLE qrcode (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_code_image BLOB,
    company_name VARCHAR(255),
    time_issued TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    company_location VARCHAR(255),
    phrase_word VARCHAR(255),
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
