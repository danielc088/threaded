import React from 'react';
import { Image, ImageStyle, StyleProp } from 'react-native';
import { getItemImageUrl } from '../../services/api';

interface ClothingImageProps {
  clothingId: string;
  style: StyleProp<ImageStyle>;
  resizeMode?: 'cover' | 'contain' | 'stretch' | 'center';
}

export const ClothingImage: React.FC<ClothingImageProps> = ({ 
  clothingId, 
  style, 
  resizeMode = 'contain' 
}) => {
  return (
    <Image 
      source={{ uri: getItemImageUrl(clothingId) }}
      style={style}
      resizeMode={resizeMode}
    />
  );
};