import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator, useWindowDimensions } from 'react-native';
import { styles, spacing } from '../../styles/theme';
import { WardrobeItem, ItemFeatures, ItemCategory, Tab, LoadingState } from '../../types';
import { getWardrobeItems, deleteWardrobeItem, addWardrobeItem, getItemFeatures } from '../../services/api';
import { ClothingImage } from '../shared/ClothingImage';
import { CategoryFilter } from '../shared/CategoryFilter';
import { ItemDetailsModal } from '../modals/ItemDetailsModal';
import { AddItemModal } from '../modals/AddItemModal';
import { AnimatedFAB } from '../shared/AnimatedFAB';

interface WardrobeTabProps {
  loadStats: () => Promise<void>;
  setCurrentTab: (tab: Tab) => void;
  setAutoGenerateItem: (item: {type: string, id: string} | null) => void;
  setLoadingState: (state: LoadingState) => void;
}

const shuffleArray = <T,>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

const getNumColumns = (width: number) => {
  if (width < 600) return 2;    // Phone/narrow - 2 columns (bigger items)
  if (width < 900) return 3;    // Tablet/half screen - 3 columns
  if (width < 1200) return 4;   // Desktop medium - 4 columns
  if (width < 1600) return 5;   // Desktop large - 5 columns
  return 6;                      // Very large desktop - 6 columns (smaller items)
};

export const WardrobeTab: React.FC<WardrobeTabProps> = ({ 
  loadStats, 
  setCurrentTab, 
  setAutoGenerateItem, 
  setLoadingState 
}) => {
  const [category, setCategory] = useState<ItemCategory>('all');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<WardrobeItem | null>(null);
  const [itemModalVisible, setItemModalVisible] = useState<boolean>(false);
  const [itemFeatures, setItemFeatures] = useState<ItemFeatures | null>(null);
  const [addModalVisible, setAddModalVisible] = useState<boolean>(false);
  const [uploadCategory, setUploadCategory] = useState<'shirt' | 'pants' | 'shoes'>('shirt');
  const [containerWidth, setContainerWidth] = useState(0);
  
  const windowDimensions = useWindowDimensions();
  const numColumns = getNumColumns(windowDimensions.width);

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
      const itemType = category === 'all' ? undefined : category;
      const data = await getWardrobeItems(itemType);
      
      if (category === 'all') {
        setItems(shuffleArray(data));
      } else {
        setItems(data);
      }
    } catch (error) {
      console.error('Error loading items:', error);
      Alert.alert('Error', 'Failed to load wardrobe items');
    }
    setLoading(false);
  };

  const openItemModal = async (item: WardrobeItem) => {
    setSelectedItem(item);
    setItemModalVisible(true);
    
    try {
      const data = await getItemFeatures(item.clothing_id);
      setItemFeatures(data);
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
    
    if (typeof window !== 'undefined' && window.confirm) {
      const confirmed = window.confirm(`Are you sure you want to delete ${selectedItem.clothing_id}?`);
      if (!confirmed) return;
    } else {
      Alert.alert(
        'Delete item',
        `Are you sure you want to delete ${selectedItem.clothing_id}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: async () => {
              await performDelete();
            },
          },
        ]
      );
      return;
    }
    
    await performDelete();
  };

  const performDelete = async () => {
    if (!selectedItem) return;
    
    closeItemModal();
    setLoadingState({ isLoading: true, message: 'Deleting item...', submessage: 'Please wait' });
    
    try {
      await deleteWardrobeItem(selectedItem.clothing_id);
      await loadItems();
      await loadStats();
      setLoadingState({ isLoading: false, message: '' });
      Alert.alert('Success', 'Item deleted successfully');
    } catch (error) {
      setLoadingState({ isLoading: false, message: '' });
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete item';
      Alert.alert('Error', errorMessage);
    }
  };

  const createOutfitWithItem = async () => {
    if (!selectedItem) return;
    
    closeItemModal();
    setAutoGenerateItem({
      type: selectedItem.item_type,
      id: selectedItem.clothing_id
    });
    setCurrentTab('outfits');
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
            mediaTypes: ['images'],
            allowsEditing: true,
            aspect: [3, 4],
            quality: 0.8,
          })
        : await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ['images'],
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
    setAddModalVisible(false);
    setLoadingState({ isLoading: true, message: 'Uploading...', submessage: 'Please wait' });
    
    try {
      await addWardrobeItem(uploadCategory, imageUri);
      
      setLoadingState({ isLoading: true, message: 'Processing...', submessage: 'Extracting features' });

      setTimeout(async () => {
        await loadItems();
        await loadStats();
        setLoadingState({ isLoading: false, message: '' });
      }, 2000);
    } catch (error) {
      setLoadingState({ isLoading: false, message: '' });
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload image';
      Alert.alert('Error', errorMessage);
    }
  };

  // Calculate with proper padding
  const gap = spacing.lg;
  const containerPadding = spacing.md; // Add some padding back
  const availableWidth = (containerWidth || windowDimensions.width) - (containerPadding * 2);
  const totalGapWidth = gap * (numColumns - 1);
  const itemWidth = (availableWidth - totalGapWidth) / numColumns;

  return (
    <View 
      style={styles.tabContent}
      onLayout={(e) => setContainerWidth(e.nativeEvent.layout.width)}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>wardrobe</Text>
      </View>

      <CategoryFilter 
        category={category}
        onCategoryChange={setCategory}
      />

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6ee7b7" />
        </View>
      ) : (
        <ScrollView style={styles.itemsScroll}>
          <View style={[styles.itemsGrid, { 
            gap: gap, 
            paddingHorizontal: containerPadding,
            paddingBottom: 100 
          }]}>
            {items.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={[
                  styles.itemCard,
                  { 
                    width: itemWidth,
                    marginRight: 0,
                    marginBottom: 0,
                  }
                ]}
                onPress={() => openItemModal(item)}
                activeOpacity={0.7}
              >
                <ClothingImage 
                  clothingId={item.clothing_id}
                  style={styles.itemImage}
                />
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      )}

      <AnimatedFAB onPress={() => setAddModalVisible(true)} />

      <ItemDetailsModal
        visible={itemModalVisible}
        item={selectedItem}
        features={itemFeatures}
        onClose={closeItemModal}
        onDelete={deleteItem}
        onCreateOutfit={createOutfitWithItem}
      />

      <AddItemModal
        visible={addModalVisible}
        category={uploadCategory}
        onCategoryChange={setUploadCategory}
        onTakePhoto={() => pickImage('camera')}
        onChooseFromGallery={() => pickImage('gallery')}
        onClose={() => setAddModalVisible(false)}
      />
    </View>
  );
};