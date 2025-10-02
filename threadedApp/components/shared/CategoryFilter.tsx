import React from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { styles } from '../../styles/theme';
import { ItemCategory } from '../../types';

interface CategoryFilterProps {
  category: ItemCategory;
  onCategoryChange: (category: ItemCategory) => void;
  categories?: ItemCategory[];
}

const getCategoryLabel = (category: ItemCategory): string => {
  const labels: { [key in ItemCategory]: string } = {
    'all': 'all',
    'shirt': 'tops',
    'pants': 'bottoms',
    'shoes': 'shoes'
  };
  return labels[category];
};

export const CategoryFilter: React.FC<CategoryFilterProps> = ({ 
  category, 
  onCategoryChange,
  categories = ['all', 'shirt', 'pants', 'shoes']
}) => {
  return (
    <View style={styles.filterContainerWrapper}>
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        contentContainerStyle={styles.filterContentContainer}
        style={styles.filterScroll}
      >
        {categories.map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[styles.filterChip, category === cat && styles.filterChipActive]}
            onPress={() => onCategoryChange(cat)}
          >
            <Text style={[styles.filterChipText, category === cat && styles.filterChipTextActive]}>
              {getCategoryLabel(cat)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};