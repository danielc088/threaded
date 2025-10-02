import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal } from 'react-native';
import { styles } from '../../styles/theme';
import { WardrobeItem, ItemCategory } from '../../types';
import { ClothingImage } from '../shared/ClothingImage';

interface ItemPickerModalProps {
  visible: boolean;
  items: WardrobeItem[];
  category: ItemCategory;
  onSelectItem: (item: WardrobeItem) => void;
  onClose: () => void;
}

export const ItemPickerModal: React.FC<ItemPickerModalProps> = ({
  visible,
  items,
  category,
  onSelectItem,
  onClose,
}) => {
  // Get category label for display
  const getCategoryLabel = (cat: ItemCategory): string => {
    const labels: { [key in ItemCategory]: string } = {
      'all': 'all',
      'shirt': 'tops',
      'pants': 'bottoms',
      'shoes': 'shoes'
    };
    return labels[cat];
  };

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.pickerModal}>
          <Text style={styles.pickerModalTitle}>
            choose {getCategoryLabel(category)}
          </Text>
          
          <ScrollView style={styles.pickerScroll}>
            <View style={styles.pickerGrid}>
              {items.map((item, index) => (
                <TouchableOpacity
                  key={item.id}
                  style={[
                    styles.pickerItem,
                    (index + 1) % 3 === 0 && { marginRight: 0 }
                  ]}
                  onPress={() => onSelectItem(item)}
                >
                  <ClothingImage 
                    clothingId={item.clothing_id}
                    style={styles.pickerItemImage}
                  />
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
          
          <TouchableOpacity
            style={styles.closePickerButton}
            onPress={onClose}
          >
            <Text style={styles.closePickerButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};