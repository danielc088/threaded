// API Response Types
export interface Stats {
  total_items: number;
  wardrobe_items: {
    shirt?: number;
    pants?: number;
    shoes?: number;
  };
  total_ratings: number;
  avg_rating: number;
  active_model: string | null;
  cached_features?: number;
  cached_predictions?: number;
}

export interface WardrobeItem {
  id: number;
  clothing_id: string;
  item_type: 'shirt' | 'pants' | 'shoes';
  file_path: string;
  uploaded_at: string;
  dominant_color?: string;
  secondary_color?: string;
  avg_brightness?: number;
  avg_saturation?: number;
  avg_hue?: number;
  color_variance?: number;
  edge_density?: number;
  texture_contrast?: number;
}

export interface Outfit {
  shirt: string;
  pants: string;
  shoes: string;
  score: number;
  score_source: 'user_rating_1' | 'user_rating_2' | 'user_rating_3' | 'user_rating_4' | 'user_rating_5' | 'cached_ml' | 'new_ml' | 'exploration_random' | 'exploration_with_fixed' | 'random';
  fixed_item?: string;
}

export interface Rating {
  id: number;
  shirt_id: string;
  pants_id: string;
  shoes_id: string;
  rating: number;
  rated_at: string;
  source?: string;
  notes?: string;
}

export interface ItemFeatures {
  clothing_id: string;
  item_type: string;
  dominant_color?: string;
  secondary_color?: string;
  uploaded_at?: string;
  style?: string;
  fit_type?: string;
  pattern_type?: string;
  has_graphic?: boolean;
  formality_score?: number;
  versatility_score?: number;
  season_suitability?: string;
  color_description?: string;
  closest_palette?: string;
}

// Request Types
export interface OutfitRequest {
  item_type: 'shirt' | 'pants' | 'shoes';
  item_id: string;
}

export interface OutfitRatingRequest {
  shirt_id: string;
  pants_id: string;
  shoes_id: string;
  rating: number;
  notes?: string;
}

export interface OutfitRatingResponse {
  success: boolean;
  message: string;
  rating_count: number;
  should_retrain: boolean;
}

export interface ModelRetrainResponse {
  success: boolean;
  message: string;
  accuracy?: number;
}

export interface AddItemResponse {
  success: boolean;
  clothing_id: string;
  message: string;
}

export interface DeleteItemResponse {
  success: boolean;
  message: string;
}

// UI State Types
export type Tab = 'wardrobe' | 'outfits' | 'stats';

export type ItemCategory = 'all' | 'shirt' | 'pants' | 'shoes';

export interface LoadingState {
  isLoading: boolean;
  message: string;
  submessage?: string;
}

// Error Types
export interface ApiError {
  detail: string;
}