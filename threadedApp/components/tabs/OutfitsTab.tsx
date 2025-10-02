import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { styles, colors, spacing, borderRadius, fontSize, fonts } from '../../styles/theme';
import { Outfit, Rating, WardrobeItem, ItemCategory, LoadingState, SelectedItems, BuildOutfitRequest } from '../../types';
import { getRandomOutfit, buildOutfit, rateOutfit, getRatings, getWardrobeItems, retrainModel } from '../../services/api';
import { OutfitDisplay } from '../outfit/OutfitDisplay';
import { RecentOutfits } from '../outfit/RecentOutfits';
import { StarRating } from '../shared/StarRating';
import { ItemPickerModal } from '../modals/ItemPickerModal';
import { ClothingImage } from '../shared/ClothingImage';

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

  const openItemPicker = (slot: 'shirt' | 'pants' | 'shoes') => {
    setCurrentPickerSlot(slot);
    setPickerCategory(slot);
    loadPickerItems(slot);
    setPickerModalVisible(true);
  };

  const loadPickerItems = async (category: ItemCategory) => {
    try {
      const itemType = category === 'all' ? undefined : category;
      const data = await getWardrobeItems(itemType);
      setPickerItems(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load items');
      console.error('Load picker items error:', error);
    }
  };

  const selectItemForSlot = (item: WardrobeItem) => {
    if (!currentPickerSlot) return;
    
    setPickerModalVisible(false);
    const newSelectedItems = {
      ...selectedItems,
      [currentPickerSlot]: item.clothing_id,
    };
    setSelectedItems(newSelectedItems);
    setCurrentPickerSlot(null);
    
    // Check if all three items are now selected
    if (newSelectedItems.shirt && newSelectedItems.pants && newSelectedItems.shoes) {
      // Auto-generate the outfit to get scoring
      generateOutfitFromBuilder(newSelectedItems);
    } else {
      setCurrentOutfit(null);
      setLastRating(null);
    }
  };

  const clearItemSlot = (slot: 'shirt' | 'pants' | 'shoes') => {
    setSelectedItems(prev => ({
      ...prev,
      [slot]: null,
    }));
    
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

  const categories: Array<{ type: 'shirt' | 'pants' | 'shoes'; label: string }> = [
    { type: 'shirt', label: 'top' },
    { type: 'pants', label: 'bottom' },
    { type: 'shoes', label: 'shoes' },
  ];

  return (
    <View style={styles.tabContent}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>outfits</Text>
        </View>

        {/* Top Fill Button */}
        <View style={localStyles.topButtonContainer}>
          <TouchableOpacity
            style={[localStyles.fillButton, loading && localStyles.fillButtonDisabled]}
            onPress={() => generateOutfitFromBuilder()}
            disabled={loading}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons 
              name="auto-fix" 
              size={24} 
              color="#065f46" 
              style={localStyles.fillButtonIcon}
            />
            <Text style={localStyles.fillButtonText}>
              {loading ? 'generating...' : 'fill empty slots'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Outfit Builder Slots */}
        <View style={localStyles.builderContainer}>
          <View style={localStyles.slotsContainer}>
            {categories.map(({ type, label }) => (
              <View key={type} style={localStyles.slot}>
                {selectedItems[type] ? (
                  <View style={localStyles.selectedItemContainer}>
                    <ClothingImage
                      clothingId={selectedItems[type]!}
                      style={localStyles.selectedItemImage}
                    />
                    <TouchableOpacity
                      style={localStyles.removeButton}
                      onPress={() => clearItemSlot(type)}
                    >
                      <MaterialCommunityIcons name="close-circle" size={24} color={colors.error} />
                    </TouchableOpacity>
                  </View>
                ) : (
                  <TouchableOpacity
                    style={localStyles.emptySlot}
                    onPress={() => openItemPicker(type)}
                    activeOpacity={0.7}
                  >
                    <MaterialCommunityIcons name="hanger" size={40} color={colors.textLighter} />
                    <Text style={localStyles.emptySlotText}>add {label}</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
          </View>
        </View>

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

const localStyles = StyleSheet.create({
  topButtonContainer: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xl,
  },
  fillButton: {
    backgroundColor: colors.primaryLight,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  fillButtonDisabled: {
    opacity: 0.5,
  },
  fillButtonIcon: {
    marginRight: spacing.sm,
  },
  fillButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  builderContainer: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxxl,
  },
  slotsContainer: {
    gap: spacing.md,
  },
  slot: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  emptySlot: {
    height: 180,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.borderDark,
    borderStyle: 'dashed',
    borderRadius: borderRadius.md,
    padding: spacing.xl,
  },
  emptySlotText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLighter,
    marginTop: spacing.sm,
  },
  selectedItemContainer: {
    position: 'relative',
    height: 180,
    padding: spacing.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectedItemImage: {
    width: '100%',
    height: '100%',
  },
  removeButton: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    backgroundColor: colors.background,
    borderRadius: borderRadius.full,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
});