CREATE TABLE IF NOT EXISTS web_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_url VARCHAR(255) NOT NULL,
    category_name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS web_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    post_content LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    post_created VARCHAR(255),
    time_crawler VARCHAR(255),
    author VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 