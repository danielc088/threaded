import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, Platform, Animated } from 'react-native';
import { styles } from '../../styles/theme';

interface StarRatingProps {
  rating: number | null;
  onRate: (rating: number) => void;
  disabled?: boolean;
}

export const StarRating: React.FC<StarRatingProps> = ({ rating, onRate, disabled = false }) => {
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);
  const scaleAnims = useRef([...Array(5)].map(() => new Animated.Value(1))).current;

  const getStarDisplay = (star: number) => {
    if (disabled && rating !== null) {
      return star <= rating ? '★' : '☆';
    }
    
    if (hoveredStar !== null) {
      return star <= hoveredStar ? '★' : '☆';
    }
    
    if (rating !== null) {
      return star <= rating ? '★' : '☆';
    }
    
    return '☆';
  };

  const handlePressIn = (star: number) => {
    setHoveredStar(star);
    Animated.timing(scaleAnims[star - 1], {
      toValue: 1.15,
      duration: 100,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = (star: number) => {
    setHoveredStar(null);
    Animated.timing(scaleAnims[star - 1], {
      toValue: 1,
      duration: 100,
      useNativeDriver: true,
    }).start();
  };

  const handlePress = (star: number) => {
    onRate(star);
    Animated.sequence([
      Animated.timing(scaleAnims[star - 1], {
        toValue: 1.2,
        duration: 100,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnims[star - 1], {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  };

  return (
    <View style={styles.starButtons}>
      {[1, 2, 3, 4, 5].map((star) => (
        <Animated.View
          key={star}
          style={{
            transform: [{ scale: scaleAnims[star - 1] }],
          }}
        >
          <TouchableOpacity
            style={styles.starButton}
            onPress={() => handlePress(star)}
            onPressIn={() => handlePressIn(star)}
            onPressOut={() => handlePressOut(star)}
            // @ts-ignore - Web-specific events
            onMouseEnter={Platform.OS === 'web' ? () => handlePressIn(star) : undefined}
            onMouseLeave={Platform.OS === 'web' ? () => handlePressOut(star) : undefined}
            disabled={disabled}
          >
            <Text style={styles.starText}>
              {getStarDisplay(star)}
            </Text>
          </TouchableOpacity>
        </Animated.View>
      ))}
    </View>
  );
};