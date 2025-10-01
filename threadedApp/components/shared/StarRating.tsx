import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Platform } from 'react-native';
import { styles } from '../../styles/theme';

interface StarRatingProps {
  rating: number | null;
  onRate: (rating: number) => void;
  disabled?: boolean;
}

export const StarRating: React.FC<StarRatingProps> = ({ rating, onRate, disabled = false }) => {
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);

  const getStarDisplay = (star: number) => {
    // If disabled and already rated, show the rating
    if (disabled && rating !== null) {
      return star <= rating ? '★' : '☆';
    }
    
    // If hovering, show up to hovered star
    if (hoveredStar !== null) {
      return star <= hoveredStar ? '★' : '☆';
    }
    
    // If rated but not disabled, show the rating
    if (rating !== null) {
      return star <= rating ? '★' : '☆';
    }
    
    // Default empty
    return '☆';
  };

  return (
    <View style={styles.starButtons}>
      {[1, 2, 3, 4, 5].map((star) => (
        <TouchableOpacity
          key={star}
          style={styles.starButton}
          onPress={() => onRate(star)}
          onPressIn={() => setHoveredStar(star)}
          onPressOut={() => setHoveredStar(null)}
          // @ts-ignore - Web-specific events
          onMouseEnter={Platform.OS === 'web' ? () => setHoveredStar(star) : undefined}
          onMouseLeave={Platform.OS === 'web' ? () => setHoveredStar(null) : undefined}
          disabled={disabled}
        >
          <Text style={styles.starText}>
            {getStarDisplay(star)}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};