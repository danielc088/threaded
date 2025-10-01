import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { styles } from '../../styles/theme';
import { WardrobeItem, ItemFeatures, ItemCategory, Tab, LoadingState } from '../../types';
import { getWardrobeItems, deleteWardrobeItem, addWardrobeItem, getItemFeatures } from '../../services/api';
import { ClothingImage } from '../shared/ClothingImage';
import { CategoryFilter } from '../shared/CategoryFilter';
import { ItemDetailsModal } from '../modals/ItemDetailsModal';
import { AddItemModal } from '../modals/AddItemModal';

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

  return (
    <View style={styles.tabContent}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Wardrobe</Text>
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
          <View style={styles.itemsGrid}>
            {items.map((item, index) => (
              <TouchableOpacity
                key={item.id}
                style={[
                  styles.itemCard,
                  (index + 1) % 3 === 0 && { marginRight: 0 }
                ]}
                onPress={() => openItemModal(item)}
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

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setAddModalVisible(true)}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

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