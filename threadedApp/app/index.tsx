// Improved React Native app with your requested changes
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

type Screen = 'menu' | 'manage' | 'random' | 'chosen' | 'outfit-display';

const App: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('menu');
  const [stats, setStats] = useState<Stats | null>(null);
  const [currentOutfit, setCurrentOutfit] = useState<Outfit | null>(null);

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

  const renderScreen = () => {
    switch (currentScreen) {
      case 'menu':
        return <MainMenuScreen stats={stats} setCurrentScreen={setCurrentScreen} />;
      case 'manage':
        return <ManageWardrobeScreen setCurrentScreen={setCurrentScreen} loadStats={loadStats} />;
      case 'random':
        return <RandomOutfitScreen setCurrentScreen={setCurrentScreen} setCurrentOutfit={setCurrentOutfit} />;
      case 'chosen':
        return <ChosenOutfitScreen setCurrentScreen={setCurrentScreen} setCurrentOutfit={setCurrentOutfit} />;
      case 'outfit-display':
        return <OutfitDisplayScreen setCurrentScreen={setCurrentScreen} loadStats={loadStats} currentOutfit={currentOutfit} />;
      default:
        return <MainMenuScreen stats={stats} setCurrentScreen={setCurrentScreen} />;
    }
  };

  return (
    <View style={styles.container}>
      {renderScreen()}
    </View>
  );
};

// Main Menu Screen
interface MainMenuScreenProps {
  stats: Stats | null;
  setCurrentScreen: (screen: Screen) => void;
}

const MainMenuScreen: React.FC<MainMenuScreenProps> = ({ stats, setCurrentScreen }) => {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.centerContent}>
      <View style={styles.logoContainer}>
        <Text style={styles.asciiArt}>
{` _______  __   __  ______    _______  _______  ______   _______  ______  
|       ||  | |  ||    _ |  |       ||   _   ||      | |       ||      | 
|_     _||  |_|  ||   | ||  |    ___||  |_|  ||  _    ||    ___||  _    |
  |   |  |       ||   |_||_ |   |___ |       || | |   ||   |___ | | |   |
  |   |  |       ||    __  ||    ___||       || |_|   ||    ___|| |_|   |
  |   |  |   _   ||   |  | ||   |___ |   _   ||       ||   |___ |       |
  |___|  |__| |__||___|  |_||_______||__| |__||______| |_______||______| `}
        </Text>
        
        <Text style={styles.asciiSubtitle}>a project by daniel cao</Text>
      </View>

      {stats && (
        <View style={styles.statsContainer}>
          <Text style={styles.statsText}>
            {`wardrobe: ${stats.total_items || 0} items`}
          </Text>
          <Text style={styles.statsText}>
            {`ratings given: ${stats.total_ratings}`}
          </Text>
          <Text style={styles.statsText}>
            {`ratings until next model update: ${5 - (stats.total_ratings % 5)}`}
          </Text>
        </View>
      )}

      <View style={styles.menuButtonsContainer}>
        <TouchableOpacity style={styles.menuButton} onPress={() => setCurrentScreen('manage')}>
          <Text style={styles.menuButtonText}>manage wardrobe</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.menuButton} onPress={() => setCurrentScreen('random')}>
          <Text style={styles.menuButtonText}>random recommendation</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.menuButton} onPress={() => setCurrentScreen('chosen')}>
          <Text style={styles.menuButtonText}>chosen item recommendation</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

// Manage Wardrobe Screen
interface ManageWardrobeScreenProps {
  setCurrentScreen: (screen: Screen) => void;
  loadStats: () => Promise<void>;
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

const ManageWardrobeScreen: React.FC<ManageWardrobeScreenProps> = ({ setCurrentScreen, loadStats }) => {
  const [category, setCategory] = useState<string>('shirt');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [mode, setMode] = useState<'view' | 'delete' | 'add'>('view');
  const [uploadStep, setUploadStep] = useState<'initial' | 'uploading' | 'processing' | 'complete'>('initial');
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [modalImage, setModalImage] = useState<string>('');
  const [itemFeatures, setItemFeatures] = useState<ItemFeatures | null>(null);

  useEffect(() => {
    loadItems();
  }, [category]);

  const loadItems = async (): Promise<void> => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/wardrobe/items?item_type=${category}`);
      const data = await response.json();
      setItems(data);
    } catch (error) {
      console.error('Error loading items:', error);
      Alert.alert('Error', 'Failed to load items');
    }
    setLoading(false);
  };

  const deleteItem = async (clothingId: string): Promise<void> => {
    Alert.alert(
      'Delete Item',
      `Are you sure you want to delete ${clothingId}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            await performDelete(clothingId);
          },
        },
      ]
    );
  };

  const performDelete = async (clothingId: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/wardrobe/items/${clothingId}`, {
        method: 'DELETE',
      });
      
      const result = await response.json();
      
      if (response.ok) {
        Alert.alert('Success', `Successfully deleted ${clothingId}`);
        await loadItems();
        await loadStats();
      } else {
        Alert.alert('Error', result.detail || 'Failed to delete item');
      }
    } catch (error) {
      Alert.alert('Error', `Failed to delete item: ${error}`);
    }
  };

  const openImageModal = (clothingId: string) => {
    setModalImage(clothingId);
    setModalVisible(true);
    // Fetch item features
    fetchItemFeatures(clothingId);
  };

  const fetchItemFeatures = async (clothingId: string) => {
    try {
      const response = await fetch(`${API_BASE}/wardrobe/items/${clothingId}/features`);
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched features:', data); // Debug log
        setItemFeatures(data);
      } else {
        console.log('Failed to fetch features, status:', response.status);
        setItemFeatures(null);
      }
    } catch (error) {
      console.log('Could not fetch item features:', error);
      setItemFeatures(null);
    }
  };

  const pickImage = async (source: 'camera' | 'gallery'): Promise<void> => {
    if (mode !== 'add') return;
    
    try {
      const ImagePicker = await import('expo-image-picker');
      
      if (source === 'camera') {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission needed', 'Camera permission is required to take photos');
          return;
        }
      } else {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission needed', 'Gallery permission is required to select photos');
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
        const selectedImage = result.assets[0];
        uploadImage(selectedImage.uri);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image');
      console.error('Image picker error:', error);
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

      const response = await fetch(`${API_BASE}/wardrobe/items?item_type=${category}`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStep('processing');
        
        setTimeout(() => {
          setUploadStep('complete');
          
          setTimeout(() => {
            setMode('view');
            setUploadStep('initial');
            loadItems();
            loadStats();
            Alert.alert('Success!', result.message || `${category} added to wardrobe!`);
          }, 2000);
        }, 2000);
      } else {
        Alert.alert('Upload Failed', result.detail || 'Failed to upload');
        setMode('view');
        setUploadStep('initial');
      }
    } catch (error) {
      Alert.alert('Error', `Failed to upload: ${error}`);
      setMode('view');
      setUploadStep('initial');
    }
  };

  const renderAddMode = () => {
    if (uploadStep === 'initial') {
      return (
        <View style={styles.uploadContainer}>
          <Text style={styles.uploadHeader}>Add New {category.charAt(0).toUpperCase() + category.slice(1)}</Text>
          <Text style={styles.uploadText}>Choose how to add your {category}:</Text>
          
          <TouchableOpacity style={styles.uploadButton} onPress={() => pickImage('camera')}>
            <Text style={styles.uploadButtonText}>Take Photo</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.uploadButton} onPress={() => pickImage('gallery')}>
            <Text style={styles.uploadButtonText}>Choose from Gallery</Text>
          </TouchableOpacity>
          
          <Text style={styles.uploadSubtext}>Supported: JPG, PNG (max 10MB)</Text>
          
          <TouchableOpacity style={styles.cancelButton} onPress={() => setMode('view')}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      );
    } else if (uploadStep === 'uploading') {
      return (
        <View style={styles.uploadContainer}>
          <ActivityIndicator size="large" color="#00ff41" />
          <Text style={styles.uploadText}>Uploading image...</Text>
        </View>
      );
    } else if (uploadStep === 'processing') {
      return (
        <View style={styles.uploadContainer}>
          <ActivityIndicator size="large" color="#00aaff" />
          <Text style={styles.uploadText}>Processing image...</Text>
          <Text style={styles.uploadSubtext}>• Removing background</Text>
          <Text style={styles.uploadSubtext}>• Extracting features</Text>
          <Text style={styles.uploadSubtext}>• Analyzing style</Text>
        </View>
      );
    } else {
      return (
        <View style={styles.uploadContainer}>
          <Text style={styles.uploadText}>Upload Complete!</Text>
          <Text style={styles.uploadSubtext}>Item added to wardrobe</Text>
        </View>
      );
    }
  };

  return (
    <ScrollView style={styles.screen}>
      <Text style={styles.sectionHeader}>╭─ manage wardrobe ─────────────────────────────╮</Text>

      <Text style={styles.prompt}>select category:</Text>

      <View style={styles.categoryButtons}>
        {['shirt', 'pants', 'shoes'].map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[styles.categoryButton, category === cat && styles.categoryButtonActive]}
            onPress={() => setCategory(cat)}
          >
            <Text style={[styles.categoryButtonText, category === cat && styles.categoryButtonTextActive]}>
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.prompt}>mode:</Text>

      <View style={styles.modeButtons}>
        <TouchableOpacity
          style={[styles.modeButton, mode === 'view' && styles.modeButtonActive]}
          onPress={() => setMode('view')}
        >
          <Text style={[styles.modeButtonText, mode === 'view' && styles.modeButtonTextActive]}>
            VIEW
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.modeButton, mode === 'add' && styles.modeButtonActive]}
          onPress={() => setMode('add')}
        >
          <Text style={[styles.modeButtonText, mode === 'add' && styles.modeButtonTextActive]}>
            ADD
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.modeButton, mode === 'delete' && styles.modeButtonActive]}
          onPress={() => setMode('delete')}
        >
          <Text style={[styles.modeButtonText, mode === 'delete' && styles.modeButtonTextActive]}>
            DELETE
          </Text>
        </TouchableOpacity>
      </View>

      {mode === 'add' ? (
        renderAddMode()
      ) : loading ? (
        <ActivityIndicator size="large" color="#00ff41" />
      ) : (
        <View style={styles.itemsList}>
          <Text style={styles.itemsHeader}>
            {items.length > 0 
              ? `| ${category.toUpperCase()} (${items.length} items):`
              : `| no ${category} found in wardrobe`
            }
          </Text>
          
          <View style={styles.imageGrid}>
            {items.map((item) => (
              <View key={item.id} style={mode === 'delete' ? styles.gridImageItemWithDelete : styles.gridImageItem}>
                <TouchableOpacity onPress={() => openImageModal(item.clothing_id)}>
                  <Image 
                    source={{ uri: `${API_BASE}/images/${item.clothing_id}` }}
                    style={styles.gridImageLarge}
                    resizeMode="contain"
                  />
                </TouchableOpacity>
                
                {mode === 'delete' && (
                  <TouchableOpacity 
                    style={styles.deleteButtonGrid} 
                    onPress={() => deleteItem(item.clothing_id)}
                  >
                    <Text style={styles.deleteButtonText}>DELETE</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
          </View>
          
        </View>
      )}

      <TouchableOpacity style={styles.backButton} onPress={() => setCurrentScreen('menu')}>
        <Text style={styles.backButtonText}>← back to main menu</Text>
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={styles.modalContent}>
            <Image 
              source={{ uri: `${API_BASE}/images/${modalImage}` }}
              style={styles.modalImage}
              resizeMode="contain"
            />
            <Text style={styles.modalText}>{modalImage}</Text>
            
            {itemFeatures && (
              <View style={styles.featuresContainer}>
                <Text style={styles.featuresHeader}>KEY FEATURES</Text>
                
                <View style={styles.featuresGrid}>
                  {itemFeatures.dominant_color && (
                    <View style={styles.featureItem}>
                      <Text style={styles.featureLabel}>Dominant Color:</Text>
                      <View style={[styles.colorSwatch, { backgroundColor: itemFeatures.dominant_color }]} />
                    </View>
                  )}
                  
                  {itemFeatures.secondary_color && (
                    <View style={styles.featureItem}>
                      <Text style={styles.featureLabel}>Secondary Color:</Text>
                      <View style={[styles.colorSwatch, { backgroundColor: itemFeatures.secondary_color }]} />
                    </View>
                  )}
                  
                  {itemFeatures.closest_palette && (
                    <View style={styles.featureItem}>
                      <Text style={styles.featureLabel}>Closest Palette:</Text>
                      <Text style={styles.featureValue}>{itemFeatures.closest_palette}</Text>
                    </View>
                  )}
                  
                  {itemFeatures.fit_type && itemFeatures.fit_type !== 'N/A' && (
                    <View style={styles.featureItem}>
                      <Text style={styles.featureLabel}>Fit:</Text>
                      <Text style={styles.featureValue}>{itemFeatures.fit_type}</Text>
                    </View>
                  )}
                  
                  {itemFeatures.style && (
                    <View style={styles.featureItem}>
                      <Text style={styles.featureLabel}>Style:</Text>
                      <Text style={styles.featureValue}>{itemFeatures.style}</Text>
                    </View>
                  )}
                </View>
              </View>
            )}
            
            <TouchableOpacity 
              style={styles.modalCloseButton}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.modalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </ScrollView>
  );
};

// Random Outfit Screen
interface RandomOutfitScreenProps {
  setCurrentScreen: (screen: Screen) => void;
  setCurrentOutfit: (outfit: Outfit | null) => void;
}

const RandomOutfitScreen: React.FC<RandomOutfitScreenProps> = ({ setCurrentScreen, setCurrentOutfit }) => {
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    generateOutfit();
  }, []);

  const generateOutfit = async (): Promise<void> => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/outfits/random`);
      if (response.ok) {
        const data = await response.json();
        setCurrentOutfit(data);
        setCurrentScreen('outfit-display');
      } else {
        Alert.alert('Error', 'No outfit could be generated');
        setLoading(false);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.screen}>
      <Text style={styles.sectionHeader}>╭─ random recommendation ───────────────────────╮</Text>

      <View style={styles.generateContainer}>
        {loading ? (
          <>
            <ActivityIndicator size="large" color="#00ff41" />
            <Text style={styles.generateText}>generating your random recommendation...</Text>
          </>
        ) : (
          <>
            <Text style={styles.generateText}>
              {`| something went wrong generating your outfit
|
| tap the button below to try again`}
            </Text>
            <TouchableOpacity style={styles.primaryButton} onPress={generateOutfit}>
              <Text style={styles.primaryButtonText}>try again</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      <TouchableOpacity style={styles.backButton} onPress={() => setCurrentScreen('menu')}>
        <Text style={styles.backButtonText}>← back to main menu</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

// Chosen Outfit Screen
interface ChosenOutfitScreenProps {
  setCurrentScreen: (screen: Screen) => void;
  setCurrentOutfit: (outfit: Outfit | null) => void;
}

const ChosenOutfitScreen: React.FC<ChosenOutfitScreenProps> = ({ setCurrentScreen, setCurrentOutfit }) => {
  const [itemType, setItemType] = useState<string>('shirt');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    loadItems();
  }, [itemType]);

  const loadItems = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/wardrobe/items?item_type=${itemType}`);
      const data = await response.json();
      setItems(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load items');
    }
  };

  const generateOutfit = async (itemId: string): Promise<void> => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/outfits/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_type: itemType,
          item_id: itemId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentOutfit(data);
        setCurrentScreen('outfit-display');
      } else {
        Alert.alert('Error', 'No outfit could be generated with that item');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
    }
    setLoading(false);
  };

  return (
    <ScrollView style={styles.screen}>
      <Text style={styles.sectionHeader}>╭─ chosen item recommendation ──────────────────╮</Text>

      <Text style={styles.prompt}>choose item type to keep:</Text>

      <View style={styles.categoryButtons}>
        {['shirt', 'pants', 'shoes'].map((type) => (
          <TouchableOpacity
            key={type}
            style={[styles.categoryButton, itemType === type && styles.categoryButtonActive]}
            onPress={() => setItemType(type)}
          >
            <Text style={[styles.categoryButtonText, itemType === type && styles.categoryButtonTextActive]}>
              {type}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.prompt}>select {itemType} to use:</Text>

      <View style={styles.itemsGrid}>
        {items.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={styles.itemGridItem}
            onPress={() => generateOutfit(item.clothing_id)}
            disabled={loading}
          >
            <Image 
              source={{ uri: `${API_BASE}/images/${item.clothing_id}` }}
              style={styles.itemGridImage}
              resizeMode="contain"
            />
            <Text style={styles.itemGridText}>{item.clothing_id.split('_')[1] || item.clothing_id}</Text>
            {loading && (
              <ActivityIndicator size="small" color="#00ff41" />
            )}
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity style={styles.backButton} onPress={() => setCurrentScreen('menu')}>
        <Text style={styles.backButtonText}>← back to main menu</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

// Outfit Display Screen
interface OutfitDisplayScreenProps {
  setCurrentScreen: (screen: Screen) => void;
  loadStats: () => Promise<void>;
  currentOutfit: Outfit | null;
}

const OutfitDisplayScreen: React.FC<OutfitDisplayScreenProps> = ({ setCurrentScreen, loadStats, currentOutfit }) => {
  const [hasRated, setHasRated] = useState<boolean>(false);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [modalImage, setModalImage] = useState<string>('');

  useEffect(() => {
    if (currentOutfit) {
      setHasRated(false);
      setUserRating(null);
    }
  }, [currentOutfit]);

  const rateOutfit = async (rating: number): Promise<void> => {
    if (!currentOutfit) return;

    try {
      const response = await fetch(`${API_BASE}/outfits/rate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
        setUserRating(rating);
        
        let message = `You rated this outfit ${rating}/5 stars.\n\n${result.message || 'Thanks for your feedback!'}`;
        
        if (result.should_retrain) {
          message += `\n\nYou've rated ${result.rating_count} outfits! Training new model...`;
          Alert.alert('Rating Saved!', message, [{ text: 'OK' }]);
          
          try {
            const retrainResponse = await fetch(`${API_BASE}/model/retrain`, {
              method: 'POST',
            });
            const retrainResult = await retrainResponse.json();
            
            if (retrainResult.success) {
              Alert.alert('Model Updated!', `New model trained with ${result.rating_count} ratings. Accuracy: ${(retrainResult.accuracy * 100).toFixed(1)}%`);
            }
          } catch (retrainError) {
            console.error('Retraining error:', retrainError);
          }
        } else {
          Alert.alert('Rating Saved!', message, [{ text: 'OK' }]);
        }
        
        loadStats();
      } else {
        Alert.alert('Error', 'Failed to save rating');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save rating');
    }
  };

  const openImageModal = (clothingId: string) => {
    setModalImage(clothingId);
    setModalVisible(true);
  };

  if (!currentOutfit) {
    return (
      <View style={styles.screen}>
        <Text style={styles.sectionHeader}>No outfit to display</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => setCurrentScreen('menu')}>
          <Text style={styles.backButtonText}>← back to main menu</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen}>
      <Text style={styles.sectionHeader}>╭─ your recommendation ─────────────────────────╮</Text>

      <View style={styles.outfitDisplay}>
        <Text style={styles.outfitHeader}>generated outfit</Text>
        
        <Text style={styles.outfitText}>
          {`shirt:  ${currentOutfit.shirt}
pants:  ${currentOutfit.pants}
shoes:  ${currentOutfit.shoes}

score:  ${(currentOutfit.score * 100).toFixed(0)}% (${currentOutfit.score_source})
${currentOutfit.fixed_item ? `fixed:  ${currentOutfit.fixed_item}` : ''}`}
        </Text>

        <View style={styles.outfitImagesVertical}>
          <TouchableOpacity 
            style={styles.outfitImageContainerVertical}
            onPress={() => openImageModal(currentOutfit.shirt)}
          >
            <Text style={styles.outfitImageLabel}>SHIRT</Text>
            <Image 
              source={{ uri: `${API_BASE}/images/${currentOutfit.shirt}` }}
              style={styles.outfitImageExtraLarge}
              resizeMode="contain"
            />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.outfitImageContainerVertical}
            onPress={() => openImageModal(currentOutfit.pants)}
          >
            <Text style={styles.outfitImageLabel}>PANTS</Text>
            <Image 
              source={{ uri: `${API_BASE}/images/${currentOutfit.pants}` }}
              style={styles.outfitImageExtraLarge}
              resizeMode="contain"
            />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.outfitImageContainerVertical}
            onPress={() => openImageModal(currentOutfit.shoes)}
          >
            <Text style={styles.outfitImageLabel}>SHOES</Text>
            <Image 
              source={{ uri: `${API_BASE}/images/${currentOutfit.shoes}` }}
              style={styles.outfitImageExtraLarge}
              resizeMode="contain"
            />
          </TouchableOpacity>
        </View>

        <Text style={styles.ratingHeader}>please rate this outfit:</Text>
        <Text style={styles.ratingSubtext}>1 = hate it, 5 = love it</Text>

        <View style={styles.ratingButtons}>
          {[1, 2, 3, 4, 5].map((rating) => (
            <TouchableOpacity
              key={rating}
              style={[
                styles.ratingButton,
                hasRated && userRating === rating && styles.ratingButtonSelected
              ]}
              onPress={() => rateOutfit(rating)}
            >
              <Text style={[
                styles.ratingButtonText,
                hasRated && userRating === rating && styles.ratingButtonTextSelected
              ]}>
                {'★'.repeat(rating)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {hasRated && (
          <View style={styles.ratingConfirmation}>
            <Text style={styles.ratingConfirmationText}>
              You rated this outfit {userRating}/5 stars!
            </Text>
          </View>
        )}
      </View>

      <TouchableOpacity style={styles.backButton} onPress={() => setCurrentScreen('menu')}>
        <Text style={styles.backButtonText}>← back to main menu</Text>
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={styles.modalContent}>
            <Image 
              source={{ uri: `${API_BASE}/images/${modalImage}` }}
              style={styles.modalImage}
              resizeMode="contain"
            />
            <Text style={styles.modalText}>{modalImage}</Text>
            <TouchableOpacity 
              style={styles.modalCloseButton}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.modalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </ScrollView>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  screen: {
    flex: 1,
    padding: 25,
    backgroundColor: '#000000',
  },
  centerContent: {
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    width: '100%',
    marginBottom: 20,
  },
  asciiArt: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 11,
    textAlign: 'left',
    marginTop: 50,
    marginBottom: 10,
  },
  asciiSubtitle: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 5,
  },
  statsContainer: {
    backgroundColor: '#001a00',
    borderColor: '#00cc33',
    borderWidth: 2,
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
    width: '100%',
    maxWidth: 400,
  },
  statsText: {
    color: '#00cc33',
    fontFamily: 'Courier',
    fontSize: 13,
    marginBottom: 5,
    textAlign: 'center',
  },
  menuButtonsContainer: {
    width: '100%',
    maxWidth: 400,
  },
  menuButton: {
    backgroundColor: '#001100',
    borderColor: '#00ff41',
    borderWidth: 2,
    padding: 20,
    marginBottom: 15,
    borderRadius: 5,
    minHeight: 70,
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuButtonText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 18,
    textAlign: 'center',
  },
  sectionHeader: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 30,
    marginTop: 50,
  },
  backButton: {
    backgroundColor: '#331100',
    borderColor: '#ffaa00',
    borderWidth: 2,
    padding: 20,
    marginTop: 30,
    borderRadius: 5,
  },
  backButtonText: {
    color: '#ffaa00',
    fontFamily: 'Courier',
    fontSize: 18,
  },
  primaryButton: {
    backgroundColor: '#001155',
    borderColor: '#00aaff',
    borderWidth: 2,
    padding: 20,
    marginBottom: 30,
    borderRadius: 5,
  },
  primaryButtonText: {
    color: '#00aaff',
    fontFamily: 'Courier',
    fontSize: 18,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  prompt: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 18,
    marginBottom: 15,
  },
  categoryButtons: {
    flexDirection: 'row',
    marginBottom: 25,
  },
  categoryButton: {
    flex: 1,
    backgroundColor: '#002200',
    borderColor: '#00ff41',
    borderWidth: 2,
    padding: 15,
    marginHorizontal: 3,
    borderRadius: 5,
  },
  categoryButtonActive: {
    backgroundColor: '#003300',
  },
  categoryButtonText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  categoryButtonTextActive: {
    color: '#ffffff',
  },
  modeButtons: {
    flexDirection: 'row',
    marginBottom: 25,
  },
  modeButton: {
    flex: 1,
    backgroundColor: '#002200',
    borderColor: '#00ff41',
    borderWidth: 2,
    padding: 15,
    marginHorizontal: 3,
    borderRadius: 5,
  },
  modeButtonActive: {
    backgroundColor: '#003300',
  },
  modeButtonText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  modeButtonTextActive: {
    color: '#ffffff',
  },
  itemsList: {
    marginBottom: 25,
  },
  itemsHeader: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 18,
    marginBottom: 15,
  },
  itemsFooter: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 18,
    marginTop: 15,
  },
  imageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    marginVertical: 15,
  },
  gridImageItem: {
    width: '45%',
    alignItems: 'center',
    marginBottom: 20,
    padding: 15,
    backgroundColor: '#002200',
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#00ff41',
  },
  gridImageLarge: {
    width: 200,
    height: 200,
    marginBottom: 10,
  },
  gridImageItemWithDelete: {
    width: '45%',
    alignItems: 'center',
    marginBottom: 25,
    padding: 20,
    backgroundColor: '#002200',
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#00ff41',
  },
  deleteButtonGrid: {
    backgroundColor: '#550000',
    borderColor: '#ff4444',
    borderWidth: 2,
    padding: 12,
    borderRadius: 5,
    marginTop: 10,
    width: '100%',
  },
  deleteButtonText: {
    color: '#ff4444',
    fontFamily: 'Courier',
    fontSize: 14,
    textAlign: 'center',
  },
  generateContainer: {
    borderColor: '#00ff41',
    borderWidth: 2,
    padding: 25,
    marginBottom: 25,
    backgroundColor: '#001100',
    borderRadius: 10,
  },
  generateText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    marginBottom: 25,
    lineHeight: 22,
  },
  itemsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    marginBottom: 25,
  },
  itemGridItem: {
    width: '45%',
    alignItems: 'center',
    marginBottom: 20,
    padding: 15,
    borderColor: '#00ff41',
    borderWidth: 2,
    backgroundColor: '#001100',
    borderRadius: 8,
  },
  itemGridImage: {
    width: 160,
    height: 160,
    marginBottom: 8,
  },
  itemGridText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 12,
    textAlign: 'center',
  },
  outfitDisplay: {
    borderColor: '#00ff41',
    borderWidth: 2,
    padding: 25,
    marginBottom: 25,
    backgroundColor: '#001100',
    borderRadius: 10,
  },
  outfitHeader: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 20,
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: 20,
    textTransform: 'uppercase',
  },
  outfitText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    marginBottom: 25,
    lineHeight: 22,
  },
  outfitImagesVertical: {
    marginBottom: 30,
  },
  outfitImageContainerVertical: {
    alignItems: 'center',
    marginBottom: 15,
    padding: 15,
    backgroundColor: '#002200',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#00ff41',
  },
  outfitImageLabel: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 14,
    marginBottom: 8,
    fontWeight: 'bold',
  },
  outfitImageExtraLarge: {
    width: 280,
    height: 280,
    marginVertical: 10,
  },
  ratingHeader: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 18,
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: 10,
  },
  ratingSubtext: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    opacity: 0.8,
  },
  ratingButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
    paddingHorizontal: 10,
  },
  ratingButton: {
    backgroundColor: '#444400',
    borderColor: '#ffff00',
    borderWidth: 2,
    padding: 12,
    minWidth: 55,
    borderRadius: 8,
    marginHorizontal: 2,
  },
  ratingButtonText: {
    color: '#ffff00',
    fontFamily: 'Courier',
    fontSize: 14,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  ratingButtonTextSelected: {
    color: '#ffffff',
    fontFamily: 'Courier',
    fontSize: 14,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  ratingButtonSelected: {
    backgroundColor: '#006600',
    borderColor: '#00ff00',
    borderWidth: 2,
    padding: 12,
    minWidth: 55,
    borderRadius: 8,
    marginHorizontal: 2,
  },
  ratingConfirmation: {
    backgroundColor: '#002200',
    borderColor: '#00ff41',
    borderWidth: 1,
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
    alignItems: 'center',
  },
  ratingConfirmationText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 14,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  uploadContainer: {
    borderColor: '#00ff41',
    borderWidth: 2,
    padding: 30,
    marginBottom: 25,
    backgroundColor: '#001100',
    borderRadius: 10,
    alignItems: 'center',
  },
  uploadHeader: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  uploadText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  uploadButton: {
    backgroundColor: '#001a00',
    borderColor: '#00cc33',
    borderWidth: 2,
    padding: 20,
    marginBottom: 15,
    borderRadius: 5,
    width: '100%',
  },
  uploadButtonText: {
    color: '#00cc33',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  uploadSubtext: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 10,
    opacity: 0.7,
  },
  cancelButton: {
    backgroundColor: '#331100',
    borderColor: '#ffaa00',
    borderWidth: 2,
    padding: 15,
    borderRadius: 5,
    marginTop: 10,
    width: '100%',
  },
  cancelButtonText: {
    color: '#ffaa00',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#001100',
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
    borderColor: '#00ff41',
    borderWidth: 2,
    width: '90%',
    maxHeight: '90%',
  },
  modalImage: {
    width: 300,
    height: 300,
    marginBottom: 15,
  },
  modalText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 16,
    marginBottom: 20,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  featuresContainer: {
    width: '100%',
    maxWidth: 350,
    backgroundColor: '#002200',
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
    borderColor: '#00ff41',
    borderWidth: 1,
    alignSelf: 'center',
  },
  featuresHeader: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  featuresGrid: {
    alignItems: 'center',
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
    width: '100%',
  },
  featureLabel: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 12,
    flex: 1,
  },
  featureValue: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 12,
    fontWeight: 'bold',
    flex: 1,
    textAlign: 'right',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  colorSwatch: {
    width: 30,
    height: 30,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#00ff41',
  },
  featureText: {
    color: '#00ff41',
    fontFamily: 'Courier',
    fontSize: 12,
    marginBottom: 5,
  },
  modalCloseButton: {
    backgroundColor: '#331100',
    borderColor: '#ffaa00',
    borderWidth: 2,
    padding: 15,
    borderRadius: 5,
    width: '100%',
  },
  modalCloseText: {
    color: '#ffaa00',
    fontFamily: 'Courier',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: 'bold',
  },
});

export default App;