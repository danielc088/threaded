import React from 'react';
import { View, Text, TouchableOpacity, Modal } from 'react-native';
import { styles } from '../../styles/theme';
import { ItemCategory } from '../../types';

interface AddItemModalProps {
  visible: boolean;
  category: ItemCategory;
  onCategoryChange: (category: 'shirt' | 'pants' | 'shoes') => void;
  onTakePhoto: () => void;
  onChooseFromGallery: () => void;
  onClose: () => void;
}

export const AddItemModal: React.FC<AddItemModalProps> = ({
  visible,
  category,
  onCategoryChange,
  onTakePhoto,
  onChooseFromGallery,
  onClose,
}) => {
  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.addModal}>
          <Text style={styles.addModalTitle}>Add item</Text>
          
          <Text style={styles.addModalLabel}>Select category</Text>
          <View style={styles.categoryButtons}>
            {(['shirt', 'pants', 'shoes'] as const).map((cat) => (
              <TouchableOpacity
                key={cat}
                style={[styles.categoryButton, category === cat && styles.categoryButtonActive]}
                onPress={() => onCategoryChange(cat)}
              >
                <Text style={[styles.categoryButtonText, category === cat && styles.categoryButtonTextActive]}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          
          <TouchableOpacity style={styles.uploadButton} onPress={onTakePhoto}>
            <Text style={styles.uploadButtonText}>Take photo</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.uploadButton} onPress={onChooseFromGallery}>
            <Text style={styles.uploadButtonText}>Choose from gallery</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={onClose}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};