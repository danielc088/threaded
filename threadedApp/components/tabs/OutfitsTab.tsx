import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { FontAwesome6 } from '@expo/vector-icons';
import { styles } from '../../styles/theme';
import { Outfit, Rating, WardrobeItem, ItemCategory, LoadingState } from '../../types';
import { getRandomOutfit, completeOutfit, rateOutfit, getRatings, getWardrobeItems, retrainModel } from '../../services/api';
import { OutfitDisplay } from '../outfit/OutfitDisplay';
import { RecentOutfits } from '../outfit/RecentOutfits';
import { StarRating } from '../shared/StarRating';
import { ItemPickerModal } from '../modals/ItemPickerModal';

interface OutfitsTabProps {
  loadStats: () => Promise<void>;
  autoGenerateItem: {type: string, id: string} | null;
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

export const OutfitsTab: React.FC<OutfitsTabProps> = ({ 
  loadStats, 
  autoGenerateItem, 
  setAutoGenerateItem, 
  setLoadingState 
}) => {
  const [currentOutfit, setCurrentOutfit] = useState<Outfit | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [lastRating, setLastRating] = useState<number | null>(null);
  const [recentRatings, setRecentRatings] = useState<Rating[]>([]);
  const [pickerModalVisible, setPickerModalVisible] = useState<boolean>(false);
  const [pickerItems, setPickerItems] = useState<WardrobeItem[]>([]);
  const [pickerCategory, setPickerCategory] = useState<ItemCategory>('all');

  useEffect(() => {
    loadRecentRatings();
  }, []);

  useEffect(() => {
    if (autoGenerateItem) {
      generateOutfitWithItem(autoGenerateItem.type as 'shirt' | 'pants' | 'shoes', autoGenerateItem.id);
      setAutoGenerateItem(null);
    }
  }, [autoGenerateItem]);

  const loadRecentRatings = async () => {
    try {
      const data = await getRatings();
      setRecentRatings(data.slice(0, 3));
    } catch (error) {
      console.log('Error loading ratings:', error);
    }
  };

  const generateOutfitWithItem = async (itemType: 'shirt' | 'pants' | 'shoes', itemId: string) => {
    setLoading(true);
    setLastRating(null);
    
    try {
      const data = await completeOutfit({ item_type: itemType, item_id: itemId });
      setCurrentOutfit(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
    }
    setLoading(false);
  };

  const generateRandomOutfit = async () => {
    setLoading(true);
    setLastRating(null);
    try {
      const data = await getRandomOutfit();
      setCurrentOutfit(data);
    } catch (error) {
      Alert.alert('Error', 'No outfit could be generated');
    }
    setLoading(false);
  };

  const openItemPicker = async () => {
    try {
      const itemType = pickerCategory === 'all' ? undefined : pickerCategory;
      const data = await getWardrobeItems(itemType);
      
      const randomizedData = pickerCategory === 'all' ? shuffleArray(data) : data;
      setPickerItems(randomizedData);
      setPickerModalVisible(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to load items');
    }
  };

  const selectItemForOutfit = async (item: WardrobeItem) => {
    setPickerModalVisible(false);
    generateOutfitWithItem(item.item_type as 'shirt' | 'pants' | 'shoes', item.clothing_id);
  };

  const handleRateOutfit = async (rating: number) => {
    if (!currentOutfit) return;
    
    try {
      const result = await rateOutfit({
        shirt_id: currentOutfit.shirt,
        pants_id: currentOutfit.pants,
        shoes_id: currentOutfit.shoes,
        rating: rating,
      });
      
      setLastRating(rating);
      loadStats();
      loadRecentRatings();
      
      if (result.should_retrain) {
        Alert.alert('Rating saved!', `Training new model with ${result.rating_count} ratings...`);
        
        setLoadingState({ isLoading: true, message: 'Training new model...', submessage: 'Please wait' });
        try {
          await retrainModel();
          await loadStats();
        } catch (error) {
          console.error('Retraining error:', error);
        } finally {
          setLoadingState({ isLoading: false, message: '' });
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save rating');
    }
  };

  const handlePickerCategoryChange = async (newCategory: ItemCategory) => {
    setPickerCategory(newCategory);
    try {
      const itemType = newCategory === 'all' ? undefined : newCategory;
      const data = await getWardrobeItems(itemType);
      const randomizedData = newCategory === 'all' ? shuffleArray(data) : data;
      setPickerItems(randomizedData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load items');
    }
  };

  const handleRecentOutfitPress = (rating: Rating) => {
    // Convert the rating back to an outfit format
    const outfit: Outfit = {
      shirt: rating.shirt_id,
      pants: rating.pants_id,
      shoes: rating.shoes_id,
      score: rating.rating / 5, // Convert 1-5 rating to 0-1 score
      score_source: `user_rating_${rating.rating}` as any,
    };
    
    setCurrentOutfit(outfit);
    setLastRating(rating.rating);
  };

  return (
    <View style={styles.tabContent}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>outfits</Text>
        </View>

        <View style={styles.generateSection}>
          <TouchableOpacity
            style={styles.generateButtonImproved}
            onPress={generateRandomOutfit}
            disabled={loading}
          >
            <View style={styles.generateButtonIcon}>
              <FontAwesome6 name="shuffle" size={24} color="#065f46" />
            </View>
            <Text style={styles.generateButtonTextImproved}>generate random outfit</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.generateButtonImproved}
            onPress={openItemPicker}
            disabled={loading}
          >
            <View style={styles.generateButtonIcon}>
              <FontAwesome6 name="wrench" size={24} color="#065f46" />
            </View>
            <Text style={styles.generateButtonTextImproved}>build outfit around item</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.outfitLoadingContainer}>
            <ActivityIndicator size="large" color="#6ee7b7" />
            <Text style={styles.outfitLoadingText}>generating outfit...</Text>
          </View>
        ) : currentOutfit ? (
          <>
            <OutfitDisplay outfit={currentOutfit} />

            <View style={styles.ratingSection}>
              <Text style={styles.ratingLabel}>rate this outfit</Text>
              <StarRating 
                rating={lastRating}
                onRate={handleRateOutfit}
                disabled={lastRating !== null}
              />
            </View>
          </>
        ) : (
          <View style={styles.emptyOutfitState}>
            <Text style={styles.emptyStateText}>generate an outfit to get started...</Text>
          </View>
        )}

        <RecentOutfits 
          ratings={recentRatings}
          onOutfitPress={handleRecentOutfitPress}
        />
      </ScrollView>

      <ItemPickerModal
        visible={pickerModalVisible}
        items={pickerItems}
        category={pickerCategory}
        onCategoryChange={handlePickerCategoryChange}
        onSelectItem={selectItemForOutfit}
        onClose={() => setPickerModalVisible(false)}
      />
    </View>
  );
};