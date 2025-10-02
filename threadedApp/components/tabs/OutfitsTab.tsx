import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { FontAwesome6 } from '@expo/vector-icons';
import { styles } from '../../styles/theme';
import { Outfit, Rating, WardrobeItem, ItemCategory, LoadingState, SelectedItems, BuildOutfitRequest } from '../../types';
import { getRandomOutfit, buildOutfit, rateOutfit, getRatings, getWardrobeItems, retrainModel } from '../../services/api';
import { OutfitDisplay } from '../outfit/OutfitDisplay';
import { OutfitBuilder } from '../outfit/OutfitBuilder';
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
  const [currentPickerSlot, setCurrentPickerSlot] = useState<'shirt' | 'pants' | 'shoes' | null>(null);
  const [selectedItems, setSelectedItems] = useState<SelectedItems>({
    shirt: null,
    pants: null,
    shoes: null,
  });

  useEffect(() => {
    loadRecentRatings();
  }, []);

  useEffect(() => {
    if (autoGenerateItem) {
      const itemType = autoGenerateItem.type as 'shirt' | 'pants' | 'shoes';
      setSelectedItems({
        shirt: null,
        pants: null,
        shoes: null,
        [itemType]: autoGenerateItem.id,
      });
      generateOutfitFromBuilder({ [itemType]: autoGenerateItem.id });
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

  const generateOutfitFromBuilder = async (items: Partial<SelectedItems> = selectedItems) => {
    setLoading(true);
    setLastRating(null);
    
    try {
      const request: BuildOutfitRequest = {
        shirt_id: items.shirt || undefined,
        pants_id: items.pants || undefined,
        shoes_id: items.shoes || undefined,
      };
      
      console.log('Generating outfit with:', request);
      
      const data = await buildOutfit(request);
      setCurrentOutfit(data);
      
      // Update selected items to show what was generated
      setSelectedItems({
        shirt: data.shirt,
        pants: data.pants,
        shoes: data.shoes,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outfit');
      console.error('Generate outfit error:', error);
    }
    setLoading(false);
  };

  const generateRandomOutfit = async () => {
    setLoading(true);
    setLastRating(null);
    
    try {
      const data = await getRandomOutfit();
      setCurrentOutfit(data);
      
      // Update selected items to show what was generated
      setSelectedItems({
        shirt: data.shirt,
        pants: data.pants,
        shoes: data.shoes,
      });
    } catch (error) {
      Alert.alert('Error', 'No outfit could be generated');
      console.error('Random outfit error:', error);
    }
    setLoading(false);
  };

  const openItemPicker = (slot: 'shirt' | 'pants' | 'shoes') => {
    setCurrentPickerSlot(slot);
    
    // Set picker category to match the slot
    setPickerCategory(slot);
    
    // Load items ONLY for that specific category
    loadPickerItems(slot);
    setPickerModalVisible(true);
  };

  const loadPickerItems = async (category: ItemCategory) => {
    try {
      // Only load items for the specific category (never 'all')
      const itemType = category === 'all' ? undefined : category;
      const data = await getWardrobeItems(itemType);
      
      // No need to randomize since we're filtering by type
      setPickerItems(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load items');
      console.error('Load picker items error:', error);
    }
  };

  const selectItemForSlot = (item: WardrobeItem) => {
    if (!currentPickerSlot) return;
    
    setPickerModalVisible(false);
    setSelectedItems(prev => ({
      ...prev,
      [currentPickerSlot]: item.clothing_id,
    }));
    setCurrentPickerSlot(null);
    
    // Clear current outfit when user changes selection
    setCurrentOutfit(null);
    setLastRating(null);
  };

  const clearItemSlot = (slot: 'shirt' | 'pants' | 'shoes') => {
    setSelectedItems(prev => ({
      ...prev,
      [slot]: null,
    }));
    
    // If we had a current outfit, clear it
    setCurrentOutfit(null);
    setLastRating(null);
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
      
      // After rating, reset the builder so user can build another
      setTimeout(() => {
        setSelectedItems({ shirt: null, pants: null, shoes: null });
        setCurrentOutfit(null);
        setLastRating(null);
      }, 1500);
      
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
      console.error('Rate outfit error:', error);
    }
  };

  const handleRecentOutfitPress = (rating: Rating) => {
    const outfit: Outfit = {
      shirt: rating.shirt_id,
      pants: rating.pants_id,
      shoes: rating.shoes_id,
      score: rating.rating / 5,
      score_source: `user_rating_${rating.rating}` as any,
    };
    
    setCurrentOutfit(outfit);
    setSelectedItems({
      shirt: rating.shirt_id,
      pants: rating.pants_id,
      shoes: rating.shoes_id,
    });
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
        </View>

        <OutfitBuilder
          selectedItems={selectedItems}
          onSelectItem={openItemPicker}
          onClearItem={clearItemSlot}
          onGenerate={() => generateOutfitFromBuilder()}
          loading={loading}
        />

        {loading ? (
          <View style={styles.outfitLoadingContainer}>
            <ActivityIndicator size="large" color="#6ee7b7" />
            <Text style={styles.outfitLoadingText}>generating outfit...</Text>
          </View>
        ) : currentOutfit ? (
          <>
            <View style={styles.ratingSection}>
              <Text style={styles.ratingLabel}>rate this outfit</Text>
              <StarRating 
                rating={lastRating}
                onRate={handleRateOutfit}
                disabled={lastRating !== null}
              />
            </View>
          </>
        ) : null}

        <RecentOutfits 
          ratings={recentRatings}
          onOutfitPress={handleRecentOutfitPress}
        />
      </ScrollView>

      <ItemPickerModal
        visible={pickerModalVisible}
        items={pickerItems}
        category={pickerCategory}
        onSelectItem={selectItemForSlot}
        onClose={() => {
          setPickerModalVisible(false);
          setCurrentPickerSlot(null);
        }}
      />
    </View>
  );
};