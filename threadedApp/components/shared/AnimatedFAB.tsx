import React, { useRef, useEffect } from 'react';
import { TouchableOpacity, Text, Animated } from 'react-native';
import { styles } from '../../styles/theme';

interface AnimatedFABProps {
  onPress: () => void;
}

export const AnimatedFAB: React.FC<AnimatedFABProps> = ({ onPress }) => {
  const scaleAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Simple entry animation
    Animated.spring(scaleAnim, {
      toValue: 1,
      tension: 80,
      friction: 10,
      useNativeDriver: true,
    }).start();
  }, []);

  const handlePress = () => {
    // Quick subtle feedback
    Animated.sequence([
      Animated.timing(scaleAnim, {
        toValue: 0.95,
        duration: 100,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
    
    onPress();
  };

  return (
    <Animated.View
      style={{
        transform: [{ scale: scaleAnim }],
      }}
    >
      <TouchableOpacity
        style={styles.fab}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </Animated.View>
  );
};