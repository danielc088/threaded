import {
  Stats,
  WardrobeItem,
  Outfit,
  Rating,
  ItemFeatures,
  OutfitRequest,
  OutfitRatingRequest,
  OutfitRatingResponse,
  ModelRetrainResponse,
  AddItemResponse,
  DeleteItemResponse,
  ApiError as ApiErrorType, // Rename the imported type
} from '../types';

const API_BASE = 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Request failed with status ${response.status}`;
    
    try {
      const error = JSON.parse(errorText);
      errorMessage = error.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    
    throw new ApiError(response.status, errorMessage);
  }
  
  return response.json();
}


// Wardrobe endpoints
export const getStats = async (): Promise<Stats> => {
  const response = await fetch(`${API_BASE}/wardrobe/stats`);
  return handleResponse<Stats>(response);
};

export const getWardrobeItems = async (itemType?: 'shirt' | 'pants' | 'shoes'): Promise<WardrobeItem[]> => {
  const endpoint = itemType 
    ? `${API_BASE}/wardrobe/items?item_type=${itemType}`
    : `${API_BASE}/wardrobe/items`;
  
  const response = await fetch(endpoint);
  return handleResponse<WardrobeItem[]>(response);
};

export const addWardrobeItem = async (
  itemType: 'shirt' | 'pants' | 'shoes',
  imageUri: string
): Promise<AddItemResponse> => {
  const formData = new FormData();
  
  const imageResponse = await fetch(imageUri);
  const blob = await imageResponse.blob();
  const file = new File([blob], 'upload.jpg', { type: blob.type || 'image/jpeg' });
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE}/wardrobe/items?item_type=${itemType}`, {
    method: 'POST',
    body: formData,
  });
  
  return handleResponse<AddItemResponse>(response);
};

export const deleteWardrobeItem = async (clothingId: string): Promise<DeleteItemResponse> => {
  const response = await fetch(`${API_BASE}/wardrobe/items/${clothingId}`, {
    method: 'DELETE',
  });
  
  return handleResponse<DeleteItemResponse>(response);
};

export const getItemFeatures = async (clothingId: string): Promise<ItemFeatures> => {
  const response = await fetch(`${API_BASE}/wardrobe/items/${clothingId}/features`);
  return handleResponse<ItemFeatures>(response);
};

export const getItemImageUrl = (clothingId: string): string => {
  return `${API_BASE}/images/${clothingId}`;
};

// Outfit endpoints
export const getRandomOutfit = async (): Promise<Outfit> => {
  const response = await fetch(`${API_BASE}/outfits/random`);
  return handleResponse<Outfit>(response);
};

export const completeOutfit = async (request: OutfitRequest): Promise<Outfit> => {
  const response = await fetch(`${API_BASE}/outfits/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  return handleResponse<Outfit>(response);
};

export const rateOutfit = async (request: OutfitRatingRequest): Promise<OutfitRatingResponse> => {
  const response = await fetch(`${API_BASE}/outfits/rate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  return handleResponse<OutfitRatingResponse>(response);
};

// Model endpoints
export const retrainModel = async (): Promise<ModelRetrainResponse> => {
  const response = await fetch(`${API_BASE}/model/retrain`, {
    method: 'POST',
  });
  
  return handleResponse<ModelRetrainResponse>(response);
};

// Ratings endpoints
export const getRatings = async (): Promise<Rating[]> => {
  const response = await fetch(`${API_BASE}/ratings`);
  return handleResponse<Rating[]>(response);
};

// Health check
export const healthCheck = async (): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE}/`);
  return handleResponse<{ message: string }>(response);
};

// Export all as a single API object (alternative approach)
export const api = {
  wardrobe: {
    getStats,
    getItems: getWardrobeItems,
    addItem: addWardrobeItem,
    deleteItem: deleteWardrobeItem,
    getItemFeatures,
    getItemImageUrl,
  },
  outfits: {
    getRandom: getRandomOutfit,
    complete: completeOutfit,
    rate: rateOutfit,
  },
  model: {
    retrain: retrainModel,
  },
  ratings: {
    getAll: getRatings,
  },
  health: healthCheck,
};