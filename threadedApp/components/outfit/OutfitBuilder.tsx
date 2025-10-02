import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { styles, colors, spacing, borderRadius, fontSize, fonts } from '../../styles/theme';
import { SelectedItems } from '../../types';
import { ClothingImage } from '../shared/ClothingImage';

interface OutfitBuilderProps {
  selectedItems: SelectedItems;
  onSelectItem: (type: 'shirt' | 'pants' | 'shoes') => void;
  onClearItem: (type: 'shirt' | 'pants' | 'shoes') => void;
  onGenerate: () => void;
  loading: boolean;
}

export const OutfitBuilder: React.FC<OutfitBuilderProps> = ({
  selectedItems,
  onSelectItem,
  onClearItem,
  onGenerate,
  loading,
}) => {
  const categories: Array<{ type: 'shirt' | 'pants' | 'shoes'; label: string }> = [
    { type: 'shirt', label: 'top' },
    { type: 'pants', label: 'bottom' },
    { type: 'shoes', label: 'shoes' },
  ];

  return (
    <View style={builderStyles.container}>
      <View style={builderStyles.slotsContainer}>
        {categories.map(({ type, label }) => (
          <View key={type} style={builderStyles.slot}>
            {selectedItems[type] ? (
              <View style={builderStyles.selectedItemContainer}>
                <ClothingImage
                  clothingId={selectedItems[type]!}
                  style={builderStyles.selectedItemImage}
                />
                <TouchableOpacity
                  style={builderStyles.removeButton}
                  onPress={() => onClearItem(type)}
                >
                  <MaterialCommunityIcons name="close-circle" size={24} color={colors.error} />
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity
                style={builderStyles.emptySlot}
                onPress={() => onSelectItem(type)}
                activeOpacity={0.7}
              >
                <MaterialCommunityIcons name="hanger" size={40} color={colors.textLighter} />
                <Text style={builderStyles.emptySlotText}>add {label}</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
      </View>

      <TouchableOpacity
        style={[builderStyles.generateButton, loading && builderStyles.generateButtonDisabled]}
        onPress={onGenerate}
        disabled={loading}
        activeOpacity={0.7}
      >
        <MaterialCommunityIcons 
          name="auto-fix" 
          size={24} 
          color={colors.primaryDark} 
          style={builderStyles.generateIcon}
        />
        <Text style={builderStyles.generateButtonText}>
          {loading ? 'generating...' : 'fill empty slots'}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const builderStyles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxxl,
  },
  slotsContainer: {
    gap: spacing.md,
    marginBottom: spacing.xl,
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
  generateButton: {
    backgroundColor: colors.primaryLight,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  generateButtonDisabled: {
    opacity: 0.5,
  },
  generateIcon: {
    marginRight: spacing.sm,
  },
  generateButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
});