"""
database schema creation for threaded wardrobe system
creates all tables needed for the application including caching tables
"""
import sqlite3
from pathlib import Path

def create_database(db_path="data/database/threaded.db"):
    """create the sqlite database and all tables"""
    
    # ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # wardrobe items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            clothing_id VARCHAR(50) NOT NULL,
            item_type VARCHAR(20) NOT NULL,
            file_path VARCHAR(255) NOT NULL,
            
            -- cv features
            dominant_color VARCHAR(7),
            secondary_color VARCHAR(7),
            avg_brightness REAL,
            avg_saturation REAL,
            avg_hue REAL,
            color_variance REAL,
            edge_density REAL,
            texture_contrast REAL,
            
            -- metadata
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, clothing_id)
        )
    """)
    
    # genai features table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS genai_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wardrobe_item_id INTEGER NOT NULL,
            
            pattern_type VARCHAR(50),
            has_graphic BOOLEAN DEFAULT FALSE,
            style VARCHAR(50),
            fit_type VARCHAR(50),
            formality_score REAL,
            versatility_score REAL,
            season_suitability TEXT,
            occasion_tags TEXT,
            style_tags TEXT,
            color_description TEXT,
            
            FOREIGN KEY (wardrobe_item_id) REFERENCES wardrobe_items (id)
        )
    """)
    
    # colour palettes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS color_palettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            color_1 VARCHAR(7) NOT NULL,
            color_2 VARCHAR(7),
            color_3 VARCHAR(7),
            color_4 VARCHAR(7),
            color_5 VARCHAR(7),
            source VARCHAR(100),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            
            UNIQUE(name)
        )
    """)
    
    # outfit ratings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfit_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            
            shirt_id VARCHAR(50),
            pants_id VARCHAR(50),
            shoes_id VARCHAR(50),
            outfit_hash VARCHAR(64) NOT NULL,
            
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            rating_source VARCHAR(20) DEFAULT 'manual',
            
            rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, outfit_hash)
        )
    """)
    
    # daily outfits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            outfit_date DATE NOT NULL,
            
            shirt_id VARCHAR(50),
            pants_id VARCHAR(50),
            shoes_id VARCHAR(50),
            outfit_hash VARCHAR(64) NOT NULL,
            
            ml_score REAL,
            user_rating INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, outfit_date)
        )
    """)
    
    # user preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            
            score_threshold REAL DEFAULT 0.5,
            preferred_image_type VARCHAR(20) DEFAULT 'bg_removed',
            grid_columns INTEGER DEFAULT 5,
            auto_rate_prompts BOOLEAN DEFAULT TRUE,
            daily_outfit_reminder BOOLEAN DEFAULT FALSE,
            model_retrain_frequency INTEGER DEFAULT 7,
            
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id)
        )
    """)
    
    # cache engineered features for outfit combinations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfit_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            outfit_hash VARCHAR(64) NOT NULL,
            feature_blob BLOB NOT NULL,
            feature_version VARCHAR(20) DEFAULT 'v1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, outfit_hash, feature_version)
        )
    """)
    
    # cache ml model predictions for outfits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfit_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            outfit_hash VARCHAR(64) NOT NULL,
            model_version VARCHAR(20) NOT NULL,
            predicted_rating REAL NOT NULL,
            predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, outfit_hash, model_version)
        )
    """)
    
    # track model training history and versions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            version VARCHAR(20) NOT NULL,
            training_samples INTEGER NOT NULL,
            accuracy_score REAL,
            feature_count INTEGER,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_path VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, version)
        )
    """)
    
    # create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wardrobe_items_user_type ON wardrobe_items(user_id, item_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outfit_ratings_user_hash ON outfit_ratings(user_id, outfit_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_outfits_user_date ON daily_outfits(user_id, outfit_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_color_palettes_active ON color_palettes(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outfit_features_user_hash ON outfit_features(user_id, outfit_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outfit_features_version ON outfit_features(user_id, feature_version)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outfit_predictions_user_model ON outfit_predictions(user_id, model_version)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outfit_predictions_hash ON outfit_predictions(user_id, outfit_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_versions_user_active ON model_versions(user_id, is_active)")
    
    # insert default user daniel (user_id = 1)
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, display_name) VALUES 
        (1, 'daniel', 'Daniel')
    """)
    
    # insert default preferences for daniel
    cursor.execute("""
        INSERT OR IGNORE INTO user_preferences (user_id, score_threshold) VALUES 
        (1, 0.5)
    """)
    
    conn.commit()
    conn.close()
    return db_path

if __name__ == "__main__":
    create_database()