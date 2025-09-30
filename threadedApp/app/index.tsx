import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  Image,
  ActivityIndicator,
  Modal,
  FlatList,
} from 'react-native';

const API_BASE = 'http://localhost:8000';

interface Stats {
  total_items: number;
  wardrobe_items: {
    shirt?: number;
    pants?: number;
    shoes?: number;
  };
  total_ratings: number;
  avg_rating: number;
  active_model: string | null;
}

interface WardrobeItem {
  id: number;
  clothing_id: string;
  item_type: string;
}

interface Outfit {
  shirt: string;
  pants: string;
  shoes: string;
  score: number;
  score_source: string;
  fixed_item?: string;
}

interface Rating {
  id: number;
  shirt_id: string;
  pants_id: string;
  shoes_id: string;
  rating: number;
  rated_at: string;
}

interface ItemFeatures {
  dominant_color?: string;
  secondary_color?: string;
  avg_brightness?: number;
  avg_saturation?: number;
  pattern_type?: string;
  style?: string;
  fit_type?: string;
  formality_score?: number;
  versatility_score?: number;
  closest_palette?: string;
}

type Tab = 'wardrobe' | 'outfits' | 'stats';

const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<Tab>('wardrobe');
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/wardrobe/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.log('Error loading stats:', error);
    }
  };

  const renderTab = () => {
    switch (currentTab) {
      case 'wardrobe':
        return <WardrobeTab loadStats={loadStats} setCurrentTab={setCurrentTab} />;
      case 'outfits':
        return <OutfitsTab loadStats={loadStats} />;
      case 'stats':
        return <StatsTab stats={stats} />;
      default:
        return <WardrobeTab loadStats={loadStats} setCurrentTab={setCurrentTab} />;
    }
  };

  return (
    <View style={styles.container}>
      {renderTab()}
      
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={styles.tabButton}
          onPress={() => setCurrentTab('wardrobe')}
        >
          <Text style={[styles.tabButtonText, currentTab === 'wardrobe' && styles.tabButtonTextActive]}>
            Wardrobe
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.tabButton}
          onPress={() => setCurrentTab('outfits')}
        >
          <Text style={[styles.tabButtonText, currentTab === 'outfits' && styles.tabButtonTextActive]}>
            Outfits
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.tabButton}
          onPress={() => setCurrentTab('stats')}
        >
          <Text style={[styles.tabButtonText, currentTab === 'stats' && styles.tabButtonTextActive]}>
            Stats
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const getCategoryLabel = (category: string): string => {
  const labels: { [key: string]: string } = {
    'all': 'All',
    'shirt': 'Shirts',
    'pants': 'Pants',
    'shoes': 'Shoes'
  };
  return labels[category] || category;
};

const shuffleArray = <T,>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

interface WardrobeTabProps {
  loadStats: () => Promise<void>;
  setCurrentTab: (tab: Tab) => void;
}

const WardrobeTab: React.FC<WardrobeTabProps> = ({ loadStats, setCurrentTab }) => {
  const [category, setCategory] = useState<string>('all');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<WardrobeItem | null>(null);
  const [itemModalVisible, setItemModalVisible] = useState<boolean>(false);
  const [itemFeatures, setItemFeatures] = useState<ItemFeatures | null>(null);
  const [addModalVisible, setAddModalVisible] = useState<boolean>(false);
  const [uploadCategory, setUploadCategory] = useState<string>(category === 'all' ? 'shirt' : category);
  const [uploadStep, setUploadStep] = useState<'initial' | 'uploading' | 'processing' | 'complete'>('initial');

  useEffect(() => {
    loadItems();
  }, [category]);

  useEffect(() => {
    if (category !== 'all') {
      setUploadCategory(category);
    }
  }, [category]);

  const loadItems = async (): Promise<void> => {
    setLoading(true);
    try {
      const endpoint = category === 'all' 
        ? `${API_BASE}/wardrobe/items`
        : `${API_BASE}/wardrobe/items?item_type=${category}`;
      const response = await fetch(endpoint);
      const data = await response.json();
      
      if (category === 'all') {
        setItems(shuffleArray(data));
      } else {
        setItems(data);
      }
    } catch (error) {
      console.error('Error loading items:', error);
    }
    setLoading(false);
  };

  const openItemModal = async (item: WardrobeItem) => {
    setSelectedItem(item);
    setItemModalVisible(true);
    
    try {
      const response = await fetch(`${API_BASE}/wardrobe/items/${item.clothing_id}/features`);
      if (response.ok) {
        const data = await response.json();
        setItemFeatures(data);
      } else {
        setItemFeatures(null);
      }
    } catch (error) {
      setItemFeatures(null);
    }
  };

  const closeItemModal = () => {
    setItemModalVisible(false);
    setSelectedItem(null);
    setItemFeatures(null);
  };

  const deleteItem = async () => {
    if (!selectedItem) return;
    
    Alert.alert(
      'Delete item',
      `Are you sure you want to delete this item?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${API_BASE}/wardrobe/items/${selectedItem.clothing_id}`, {
                method: 'DELETE',
              });
              
              if (response.ok) {
                Alert.alert('Success', 'Item deleted');
                closeItemModal();
                loadItems();
                loadStats();
              } else {
                Alert.alert('Error', 'Failed to delete item');
              }
            } catch (error) {
              Alert.alert('Error', 'Failed to delete item');
            }
          },
        },
      ]
    );
  };

  const createOutfitWithItem = async () => {
    if (!selectedItem) return;
    
    try {
      const response = await fetch(`${API_BASE}/outfits/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_type: selectedItem.item_type,
          item_id: selectedItem.clothing_id,
        }),
      });
      
      if (response.ok) {
        closeItemModal();
        setCurrentTab('outfits');
      } else {
        Alert.alert('Error', 'Failed to generate outfit');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
    }
  };

  const pickImage = async (source: 'camera' | 'gallery'): Promise<void> => {
    try {
      const ImagePicker = await import('expo-image-picker');
      
      if (source === 'camera') {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission needed', 'Camera permission is required');
          return;
        }
      } else {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission needed', 'Gallery permission is required');
          return;
        }
      }

      const result = source === 'camera' 
        ? await ImagePicker.launchCameraAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            allowsEditing: true,
            aspect: [3, 4],
            quality: 0.8,
          })
        : await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            allowsEditing: true,
            aspect: [3, 4],
            quality: 0.8,
          });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        uploadImage(result.assets[0].uri);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const uploadImage = async (imageUri: string): Promise<void> => {
    setUploadStep('uploading');
    
    try {
      const formData = new FormData();
      const filename = imageUri.split('/').pop() || 'image.jpg';
      
      formData.append('file', {
        uri: imageUri,
        name: filename,
        type: 'image/jpeg',
      } as any);

      const response = await fetch(`${API_BASE}/wardrobe/items?item_type=${uploadCategory}`, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.ok) {
        setUploadStep('processing');
        
        setTimeout(() => {
          setUploadStep('complete');
          setTimeout(() => {
            setAddModalVisible(false);
            setUploadStep('initial');
            loadItems();
            loadStats();
          }, 1500);
        }, 2000);
      } else {
        Alert.alert('Upload failed', 'Failed to upload image');
        setUploadStep('initial');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to upload');
      setUploadStep('initial');
    }
  };

  return (
    <View style={styles.tabContent}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Wardrobe</Text>
      </View>

      <View style={styles.filterContainerWrapper}>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false} 
          contentContainerStyle={styles.filterContentContainer}
          style={styles.filterScroll}
        >
          {['all', 'shirt', 'pants', 'shoes'].map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[styles.filterChip, category === cat && styles.filterChipActive]}
              onPress={() => setCategory(cat)}
            >
              <Text style={[styles.filterChipText, category === cat && styles.filterChipTextActive]}>
                {getCategoryLabel(cat)}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6ee7b7" />
        </View>
      ) : (
        <ScrollView style={styles.itemsScroll}>
          <View style={styles.itemsGrid}>
            {items.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={styles.itemCard}
                onPress={() => openItemModal(item)}
              >
                <Image 
                  source={{ uri: `${API_BASE}/images/${item.clothing_id}` }}
                  style={styles.itemImage}
                  resizeMode="contain"
                />
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      )}

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setAddModalVisible(true)}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      <Modal
        visible={itemModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={closeItemModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.itemModal}>
            <ScrollView>
              {selectedItem && (
                <>
                  <Image 
                    source={{ uri: `${API_BASE}/images/${selectedItem.clothing_id}` }}
                    style={styles.itemModalImage}
                    resizeMode="contain"
                  />
                  
                  {itemFeatures && (
                    <View style={styles.descriptionSection}>
                      <Text style={styles.descriptionHeader}>Description</Text>
                      
                      <View style={styles.featuresList}>
                        {itemFeatures.dominant_color && (
                          <View style={styles.featureRow}>
                            <Text style={styles.featureLabel}>Dominant color</Text>
                            <View style={[styles.colorSwatch, { backgroundColor: itemFeatures.dominant_color }]} />
                          </View>
                        )}
                        
                        {itemFeatures.secondary_color && (
                          <View style={styles.featureRow}>
                            <Text style={styles.featureLabel}>Secondary color</Text>
                            <View style={[styles.colorSwatch, { backgroundColor: itemFeatures.secondary_color }]} />
                          </View>
                        )}
                        
                        {itemFeatures.style && (
                          <View style={styles.featureRow}>
                            <Text style={styles.featureLabel}>Style</Text>
                            <Text style={styles.featureValue}>{itemFeatures.style}</Text>
                          </View>
                        )}
                        
                        {itemFeatures.fit_type && itemFeatures.fit_type !== 'N/A' && (
                          <View style={styles.featureRow}>
                            <Text style={styles.featureLabel}>Fit</Text>
                            <Text style={styles.featureValue}>{itemFeatures.fit_type}</Text>
                          </View>
                        )}
                        
                        {itemFeatures.closest_palette && (
                          <View style={styles.featureRow}>
                            <Text style={styles.featureLabel}>Palette</Text>
                            <Text style={styles.featureValue}>{itemFeatures.closest_palette}</Text>
                          </View>
                        )}
                      </View>
                    </View>
                  )}
                </>
              )}
            </ScrollView>
            
            <View style={styles.itemModalButtons}>
              <TouchableOpacity
                style={styles.createOutfitButton}
                onPress={createOutfitWithItem}
              >
                <Text style={styles.createOutfitButtonText}>Create outfit</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={deleteItem}
              >
                <Text style={styles.deleteButtonText}>Delete</Text>
              </TouchableOpacity>
            </View>
            
            <TouchableOpacity
              style={styles.closeModalButton}
              onPress={closeItemModal}
            >
              <Text style={styles.closeModalButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <Modal
        visible={addModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => {
          setAddModalVisible(false);
          setUploadStep('initial');
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.addModal}>
            {uploadStep === 'initial' ? (
              <>
                <Text style={styles.addModalTitle}>Add item</Text>
                
                <Text style={styles.addModalLabel}>Select category</Text>
                <View style={styles.categoryButtons}>
                  {['shirt', 'pants', 'shoes'].map((cat) => (
                    <TouchableOpacity
                      key={cat}
                      style={[styles.categoryButton, uploadCategory === cat && styles.categoryButtonActive]}
                      onPress={() => setUploadCategory(cat)}
                    >
                      <Text style={[styles.categoryButtonText, uploadCategory === cat && styles.categoryButtonTextActive]}>
                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
                
                <TouchableOpacity style={styles.uploadButton} onPress={() => pickImage('camera')}>
                  <Text style={styles.uploadButtonText}>Take photo</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.uploadButton} onPress={() => pickImage('gallery')}>
                  <Text style={styles.uploadButtonText}>Choose from gallery</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setAddModalVisible(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
              </>
            ) : uploadStep === 'uploading' ? (
              <>
                <ActivityIndicator size="large" color="#6ee7b7" />
                <Text style={styles.uploadStatusText}>Uploading...</Text>
              </>
            ) : uploadStep === 'processing' ? (
              <>
                <ActivityIndicator size="large" color="#6ee7b7" />
                <Text style={styles.uploadStatusText}>Processing...</Text>
              </>
            ) : (
              <>
                <Text style={styles.uploadStatusText}>Complete!</Text>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

interface OutfitsTabProps {
  loadStats: () => Promise<void>;
}

const OutfitsTab: React.FC<OutfitsTabProps> = ({ loadStats }) => {
  const [currentOutfit, setCurrentOutfit] = useState<Outfit | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [hasRated, setHasRated] = useState<boolean>(false);
  const [recentRatings, setRecentRatings] = useState<Rating[]>([]);
  const [pickerModalVisible, setPickerModalVisible] = useState<boolean>(false);
  const [pickerItems, setPickerItems] = useState<WardrobeItem[]>([]);
  const [pickerCategory, setPickerCategory] = useState<string>('all');

  useEffect(() => {
    loadRecentRatings();
  }, []);

  const loadRecentRatings = async () => {
    try {
      const response = await fetch(`${API_BASE}/ratings`);
      if (response.ok) {
        const data = await response.json();
        setRecentRatings(data.slice(0, 3));
      }
    } catch (error) {
      console.log('Error loading ratings:', error);
    }
  };

  const generateRandomOutfit = async () => {
    setLoading(true);
    setHasRated(false);
    try {
      const response = await fetch(`${API_BASE}/outfits/random`);
      if (response.ok) {
        const data = await response.json();
        setCurrentOutfit(data);
      } else {
        Alert.alert('Error', 'No outfit could be generated');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
    }
    setLoading(false);
  };

  const openItemPicker = async () => {
    try {
      const endpoint = pickerCategory === 'all' 
        ? `${API_BASE}/wardrobe/items`
        : `${API_BASE}/wardrobe/items?item_type=${pickerCategory}`;
      const response = await fetch(endpoint);
      const data = await response.json();
      setPickerItems(data);
      setPickerModalVisible(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to load items');
    }
  };

  const selectItemForOutfit = async (item: WardrobeItem) => {
    setPickerModalVisible(false);
    setLoading(true);
    setHasRated(false);
    
    try {
      const response = await fetch(`${API_BASE}/outfits/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_type: item.item_type,
          item_id: item.clothing_id,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentOutfit(data);
      } else {
        Alert.alert('Error', 'Failed to generate outfit');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
    }
    setLoading(false);
  };

  const rateOutfit = async (rating: number) => {
    if (!currentOutfit) return;
    
    try {
      const response = await fetch(`${API_BASE}/outfits/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          shirt_id: currentOutfit.shirt,
          pants_id: currentOutfit.pants,
          shoes_id: currentOutfit.shoes,
          rating: rating,
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setHasRated(true);
        loadStats();
        loadRecentRatings();
        
        if (result.should_retrain) {
          Alert.alert('Rating saved!', `Training new model with ${result.rating_count} ratings...`);
          
          try {
            await fetch(`${API_BASE}/model/retrain`, { method: 'POST' });
          } catch (error) {
            console.error('Retraining error:', error);
          }
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save rating');
    }
  };

  return (
    <View style={styles.tabContent}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Outfits</Text>
        </View>

        <View style={styles.generateSection}>
          <TouchableOpacity
            style={styles.generateButtonImproved}
            onPress={generateRandomOutfit}
            disabled={loading}
          >
            <View style={styles.generateButtonIcon}>
              <Text style={styles.generateButtonIconText}>R</Text>
            </View>
            <Text style={styles.generateButtonTextImproved}>Generate random</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.generateButtonImproved}
            onPress={openItemPicker}
            disabled={loading}
          >
            <View style={styles.generateButtonIcon}>
              <Text style={styles.generateButtonIconText}>B</Text>
            </View>
            <Text style={styles.generateButtonTextImproved}>Build around item</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.outfitLoadingContainer}>
            <ActivityIndicator size="large" color="#6ee7b7" />
            <Text style={styles.loadingText}>Generating outfit...</Text>
          </View>
        ) : currentOutfit ? (
          <View style={styles.currentOutfitSection}>
            <View style={styles.outfitImages}>
              <View style={styles.outfitImageContainer}>
                <Image 
                  source={{ uri: `${API_BASE}/images/${currentOutfit.shirt}` }}
                  style={styles.outfitImage}
                  resizeMode="contain"
                />
              </View>
              
              <View style={styles.outfitImageContainer}>
                <Image 
                  source={{ uri: `${API_BASE}/images/${currentOutfit.pants}` }}
                  style={styles.outfitImage}
                  resizeMode="contain"
                />
              </View>
              
              <View style={styles.outfitImageContainer}>
                <Image 
                  source={{ uri: `${API_BASE}/images/${currentOutfit.shoes}` }}
                  style={styles.outfitImage}
                  resizeMode="contain"
                />
              </View>
            </View>

            <Text style={styles.matchScore}>
              {(currentOutfit.score * 100).toFixed(0)}% match
            </Text>

            <View style={styles.ratingSection}>
              <Text style={styles.ratingLabel}>Rate this outfit</Text>
              <View style={styles.starButtons}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <TouchableOpacity
                    key={star}
                    style={styles.starButton}
                    onPress={() => rateOutfit(star)}
                    disabled={hasRated}
                  >
                    <Text style={styles.starText}>
                      {hasRated ? '★' : '☆'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              
              {hasRated && (
                <TouchableOpacity
                  style={styles.generateAnotherButton}
                  onPress={generateRandomOutfit}
                >
                  <Text style={styles.generateAnotherButtonText}>Generate another</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        ) : (
          <View style={styles.emptyOutfitState}>
            <Text style={styles.emptyStateText}>Generate an outfit to get started</Text>
          </View>
        )}

        {recentRatings.length > 0 && (
          <View style={styles.recentSection}>
            <Text style={styles.recentSectionTitle}>Recently rated</Text>
            
            <View style={styles.recentCardsContainer}>
              {recentRatings.map((rating) => (
                <View key={rating.id} style={styles.recentOutfitCard}>
                  <View style={styles.recentOutfitImageContainer}>
                    <Image 
                      source={{ uri: `${API_BASE}/images/${rating.shirt_id}` }}
                      style={styles.recentOutfitImage}
                      resizeMode="contain"
                    />
                  </View>
                  
                  <View style={styles.recentOutfitImageContainer}>
                    <Image 
                      source={{ uri: `${API_BASE}/images/${rating.pants_id}` }}
                      style={styles.recentOutfitImage}
                      resizeMode="contain"
                    />
                  </View>
                  
                  <View style={styles.recentOutfitImageContainer}>
                    <Image 
                      source={{ uri: `${API_BASE}/images/${rating.shoes_id}` }}
                      style={styles.recentOutfitImage}
                      resizeMode="contain"
                    />
                  </View>
                  
                  <View style={styles.recentOutfitRating}>
                    <Text style={styles.recentRatingStars}>
                      {'★'.repeat(rating.rating)}{'☆'.repeat(5 - rating.rating)}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      <Modal
        visible={pickerModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setPickerModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.pickerModal}>
            <Text style={styles.pickerModalTitle}>Choose item</Text>
            
            <View style={styles.filterContainerWrapper}>
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={false} 
                contentContainerStyle={styles.filterContentContainer}
                style={styles.filterScroll}
              >
                {['all', 'shirt', 'pants', 'shoes'].map((cat) => (
                  <TouchableOpacity
                    key={cat}
                    style={[styles.filterChip, pickerCategory === cat && styles.filterChipActive]}
                    onPress={async () => {
                      setPickerCategory(cat);
                      const endpoint = cat === 'all' 
                        ? `${API_BASE}/wardrobe/items`
                        : `${API_BASE}/wardrobe/items?item_type=${cat}`;
                      const response = await fetch(endpoint);
                      const data = await response.json();
                      setPickerItems(data);
                    }}
                  >
                    <Text style={[styles.filterChipText, pickerCategory === cat && styles.filterChipTextActive]}>
                      {getCategoryLabel(cat)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
            
            <ScrollView style={styles.pickerScroll}>
              <View style={styles.pickerGrid}>
                {pickerItems.map((item) => (
                  <TouchableOpacity
                    key={item.id}
                    style={styles.pickerItem}
                    onPress={() => selectItemForOutfit(item)}
                  >
                    <Image 
                      source={{ uri: `${API_BASE}/images/${item.clothing_id}` }}
                      style={styles.pickerItemImage}
                      resizeMode="contain"
                    />
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
            
            <TouchableOpacity
              style={styles.closePickerButton}
              onPress={() => setPickerModalVisible(false)}
            >
              <Text style={styles.closePickerButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

interface StatsTabProps {
  stats: Stats | null;
}

const StatsTab: React.FC<StatsTabProps> = ({ stats }) => {
  const shirtCount = stats?.wardrobe_items?.shirt || 0;
  const pantsCount = stats?.wardrobe_items?.pants || 0;
  const shoesCount = stats?.wardrobe_items?.shoes || 0;
  const totalCombinations = shirtCount * pantsCount * shoesCount;

  return (
    <View style={styles.tabContent}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Stats</Text>
      </View>
      
      <ScrollView style={styles.statsContent}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Items in wardrobe</Text>
          <Text style={styles.statValue}>{stats?.total_items || 0}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Total outfit combinations</Text>
          <Text style={styles.statValue}>{totalCombinations}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Outfits rated</Text>
          <Text style={styles.statValue}>{stats?.total_ratings || 0}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Ratings until next update</Text>
          <Text style={styles.statValue}>
            {stats ? 5 - (stats.total_ratings % 5) : 5}
          </Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Current model</Text>
          <Text style={styles.statValue}>
            {stats?.active_model || 'No model yet'}
          </Text>
        </View>
        
        <View style={styles.projectCredit}>
          <Text style={styles.projectCreditText}>a project by daniel cao</Text>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  tabContent: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingBottom: 20,
    paddingTop: 10,
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  tabButtonText: {
    fontSize: 14,
    color: '#9ca3af',
    fontWeight: '500',
  },
  tabButtonTextActive: {
    color: '#059669',
    borderBottomWidth: 2,
    borderBottomColor: '#059669',
    paddingBottom: 6,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '600',
    color: '#059669',
  },
  filterContainerWrapper: {
    alignItems: 'center',
    marginBottom: 20,
  },
  filterScroll: {
    maxWidth: 400,
  },
  filterContentContainer: {
    paddingHorizontal: 20,
  },
  filterChip: {
    backgroundColor: '#f3f4f6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: '#6ee7b7',
  },
  filterChipText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  filterChipTextActive: {
    color: '#065f46',
  },
  itemsScroll: {
    flex: 1,
    paddingHorizontal: 20,
  },
  itemsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingBottom: 100,
  },
  itemCard: {
    width: '31%',
    aspectRatio: 0.75,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: 8,
  },
  itemImage: {
    width: '100%',
    height: '100%',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 90,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#6ee7b7',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  fabText: {
    fontSize: 32,
    color: '#065f46',
    fontWeight: '300',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  itemModal: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingBottom: 40,
    maxHeight: '85%',
  },
  itemModalImage: {
    width: '100%',
    height: 300,
    marginBottom: 20,
  },
  descriptionSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  descriptionHeader: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 16,
  },
  featuresList: {
    gap: 12,
  },
  featureRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  featureLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  featureValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  colorSwatch: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  itemModalButtons: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 12,
    marginBottom: 12,
  },
  createOutfitButton: {
    flex: 1,
    backgroundColor: '#6ee7b7',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  createOutfitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#065f46',
  },
  deleteButton: {
    flex: 1,
    backgroundColor: '#fee2e2',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#dc2626',
  },
  closeModalButton: {
    marginHorizontal: 20,
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  closeModalButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
  },
  addModal: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    paddingBottom: 40,
  },
  addModalTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 20,
  },
  addModalLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
    marginBottom: 12,
  },
  categoryButtons: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
  },
  categoryButton: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  categoryButtonActive: {
    backgroundColor: '#6ee7b7',
  },
  categoryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  categoryButtonTextActive: {
    color: '#065f46',
  },
  uploadButton: {
    backgroundColor: '#6ee7b7',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  uploadButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#065f46',
  },
  cancelButton: {
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
  },
  uploadStatusText: {
    fontSize: 16,
    color: '#374151',
    marginTop: 16,
    textAlign: 'center',
  },
  generateSection: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 24,
    gap: 12,
  },
  generateButtonImproved: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#6ee7b7',
  },
  generateButtonIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ecfdf5',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  generateButtonIconText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#047857',
  },
  generateButtonTextImproved: {
    fontSize: 14,
    fontWeight: '600',
    color: '#047857',
    textAlign: 'center',
  },
  outfitLoadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 12,
  },
  currentOutfitSection: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  outfitImages: {
    gap: 12,
    marginBottom: 16,
  },
  outfitImageContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#000000',
  },
  outfitImage: {
    width: 240,
    height: 240,
  },
  matchScore: {
    fontSize: 18,
    fontWeight: '600',
    color: '#059669',
    textAlign: 'center',
    marginBottom: 24,
  },
  ratingSection: {
    alignItems: 'center',
  },
  ratingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 16,
  },
  starButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  starButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  starText: {
    fontSize: 32,
    color: '#fbbf24',
  },
  generateAnotherButton: {
    backgroundColor: '#6ee7b7',
    borderRadius: 12,
    padding: 14,
    marginTop: 20,
    paddingHorizontal: 32,
  },
  generateAnotherButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#065f46',
  },
  emptyOutfitState: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#9ca3af',
  },
  recentSection: {
    paddingTop: 32,
    paddingBottom: 100,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  recentSectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 16,
    paddingHorizontal: 20,
  },
  recentCardsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 100,
    paddingHorizontal: 20,
  },
  recentOutfitCard: {
    width: 200,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  recentOutfitImageContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 8,
    alignItems: 'center',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  recentOutfitImage: {
    width: 140,
    height: 140,
  },
  recentOutfitRating: {
    alignItems: 'center',
    marginTop: 4,
  },
  recentRatingStars: {
    fontSize: 14,
    color: '#fbbf24',
  },
  pickerModal: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingBottom: 40,
    maxHeight: '85%',
  },
  pickerModalTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: '#374151',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  pickerScroll: {
    flex: 1,
    paddingHorizontal: 20,
  },
  pickerGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  pickerItem: {
    width: '31%',
    aspectRatio: 0.75,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: 8,
  },
  pickerItemImage: {
    width: '100%',
    height: '100%',
  },
  closePickerButton: {
    marginHorizontal: 20,
    marginTop: 16,
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  closePickerButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
  },
  statsContent: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  statCard: {
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '600',
    color: '#059669',
  },
  projectCredit: {
    marginTop: 40,
    alignItems: 'center',
  },
  projectCreditText: {
    fontSize: 24,
    color: '#6b7280',
  },
});

export default App;