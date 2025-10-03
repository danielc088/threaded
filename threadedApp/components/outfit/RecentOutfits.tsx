import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { styles, colors, spacing, borderRadius } from '../../styles/theme';
import { Rating } from '../../types';
import { ClothingImage } from '../shared/ClothingImage';

interface RecentOutfitsProps {
  ratings: Rating[];
  onOutfitPress: (rating: Rating) => void;
}

export const RecentOutfits: React.FC<RecentOutfitsProps> = ({ ratings, onOutfitPress }) => {
  if (ratings.length === 0) {
    return null;
  }

  const recentRatings = ratings.slice(0, 10);

  return (
    <View style={styles.recentSection}>
      <Text style={styles.recentSectionTitle}>recently rated</Text>
      
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={true}
        contentContainerStyle={localStyles.scrollContent}
      >
        {recentRatings.map((item, index) => (
          <TouchableOpacity
            key={`${item.shirt_id}-${item.pants_id}-${item.shoes_id}-${index}`}
            style={styles.recentOutfitCard}
            onPress={() => onOutfitPress(item)}
            activeOpacity={0.7}
          >
            <View style={styles.recentOutfitImageContainer}>
              <ClothingImage clothingId={item.shirt_id} style={styles.recentOutfitImage} />
            </View>
            <View style={styles.recentOutfitImageContainer}>
              <ClothingImage clothingId={item.pants_id} style={styles.recentOutfitImage} />
            </View>
            <View style={styles.recentOutfitImageContainer}>
              <ClothingImage clothingId={item.shoes_id} style={styles.recentOutfitImage} />
            </View>
            <View style={styles.recentOutfitRating}>
              <Text style={styles.recentRatingStars}>
                {'★'.repeat(item.rating)}{'☆'.repeat(5 - item.rating)}
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const localStyles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: spacing.xl,
    gap: spacing.xxxl,
  },
});