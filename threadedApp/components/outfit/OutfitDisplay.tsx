import React from 'react';
import { View, Text } from 'react-native';
import { styles } from '../../styles/theme';
import { Outfit } from '../../types';
import { ClothingImage } from '../shared/ClothingImage';

interface OutfitDisplayProps {
  outfit: Outfit;
}

export const OutfitDisplay: React.FC<OutfitDisplayProps> = ({ outfit }) => {
  return (
    <View style={styles.currentOutfitSection}>
      <View style={styles.outfitImages}>
        <View style={styles.outfitImageContainer}>
          <ClothingImage 
            clothingId={outfit.shirt}
            style={styles.outfitImage}
          />
        </View>
        
        <View style={styles.outfitImageContainer}>
          <ClothingImage 
            clothingId={outfit.pants}
            style={styles.outfitImage}
          />
        </View>
        
        <View style={styles.outfitImageContainer}>
          <ClothingImage 
            clothingId={outfit.shoes}
            style={styles.outfitImage}
          />
        </View>
      </View>
    </View>
  );
};