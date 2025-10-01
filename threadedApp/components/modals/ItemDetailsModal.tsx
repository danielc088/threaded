import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal } from 'react-native';
import { styles } from '../../styles/theme';
import { WardrobeItem, ItemFeatures } from '../../types';
import { ClothingImage } from '../shared/ClothingImage';

interface ItemDetailsModalProps {
  visible: boolean;
  item: WardrobeItem | null;
  features: ItemFeatures | null;
  onClose: () => void;
  onDelete: () => void;
  onCreateOutfit: () => void;
}

export const ItemDetailsModal: React.FC<ItemDetailsModalProps> = ({
  visible,
  item,
  features,
  onClose,
  onDelete,
  onCreateOutfit,
}) => {
  if (!item) return null;

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.itemModal}>
          <ScrollView>
            <ClothingImage 
              clothingId={item.clothing_id}
              style={styles.itemModalImage}
            />
            
            {features && (
              <View style={styles.descriptionSection}>
                <Text style={styles.descriptionHeader}>Description</Text>
                
                <View style={styles.featuresList}>
                  {features.uploaded_at && (
                    <View style={styles.featureRow}>
                      <Text style={styles.featureLabel}>Date added</Text>
                      <Text style={styles.featureValue}>
                        {new Date(features.uploaded_at).toLocaleDateString()}
                      </Text>
                    </View>
                  )}
                  
                  {features.dominant_color && (
                    <View style={styles.featureRow}>
                      <Text style={styles.featureLabel}>Dominant color</Text>
                      <View style={[styles.colorSwatch, { backgroundColor: features.dominant_color }]} />
                    </View>
                  )}
                  
                  {features.secondary_color && (
                    <View style={styles.featureRow}>
                      <Text style={styles.featureLabel}>Secondary color</Text>
                      <View style={[styles.colorSwatch, { backgroundColor: features.secondary_color }]} />
                    </View>
                  )}
                  
                  {features.style && (
                    <View style={styles.featureRow}>
                      <Text style={styles.featureLabel}>Style</Text>
                      <Text style={styles.featureValue}>{features.style}</Text>
                    </View>
                  )}
                  
                  {features.fit_type && features.fit_type !== 'N/A' && (
                    <View style={styles.featureRow}>
                      <Text style={styles.featureLabel}>Fit</Text>
                      <Text style={styles.featureValue}>{features.fit_type}</Text>
                    </View>
                  )}
                  
                  {features.closest_palette && (
                    <View style={styles.featureRow}>
                      <Text style={styles.featureLabel}>Palette</Text>
                      <Text style={styles.featureValue}>{features.closest_palette}</Text>
                    </View>
                  )}
                </View>
              </View>
            )}
          </ScrollView>
          
          <View style={styles.itemModalButtons}>
            <TouchableOpacity
              style={styles.createOutfitButton}
              onPress={onCreateOutfit}
            >
              <Text style={styles.createOutfitButtonText}>Create outfit</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={onDelete}
            >
              <Text style={styles.deleteButtonText}>Delete</Text>
            </TouchableOpacity>
          </View>
          
          <TouchableOpacity
            style={styles.closeModalButton}
            onPress={onClose}
          >
            <Text style={styles.closeModalButtonText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};