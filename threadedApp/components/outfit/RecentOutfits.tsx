import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { styles } from '../../styles/theme';
import { Rating } from '../../types';
import { ClothingImage } from '../shared/ClothingImage';

interface RecentOutfitsProps {
  ratings: Rating[];
  onOutfitPress?: (rating: Rating) => void;
}

export const RecentOutfits: React.FC<RecentOutfitsProps> = ({ ratings, onOutfitPress }) => {
  if (ratings.length === 0) return null;

  return (
    <View style={styles.recentSection}>
      <Text style={styles.recentSectionTitle}>recently rated</Text>
      
      <View style={styles.recentCardsContainer}>
        {ratings.map((rating) => (
          <TouchableOpacity 
            key={rating.id} 
            style={styles.recentOutfitCard}
            onPress={() => onOutfitPress?.(rating)}
            activeOpacity={0.7}
          >
            <View style={styles.recentOutfitImageContainer}>
              <ClothingImage 
                clothingId={rating.shirt_id}
                style={styles.recentOutfitImage}
              />
            </View>
            
            <View style={styles.recentOutfitImageContainer}>
              <ClothingImage 
                clothingId={rating.pants_id}
                style={styles.recentOutfitImage}
              />
            </View>
            
            <View style={styles.recentOutfitImageContainer}>
              <ClothingImage 
                clothingId={rating.shoes_id}
                style={styles.recentOutfitImage}
              />
            </View>
            
            <View style={styles.recentOutfitRating}>
              <Text style={styles.recentRatingStars}>
                {'★'.repeat(rating.rating)}{'☆'.repeat(5 - rating.rating)}
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};