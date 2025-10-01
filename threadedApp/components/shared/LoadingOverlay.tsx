import React from 'react';
import { View, Text, ActivityIndicator, Modal } from 'react-native';
import { styles, colors } from '../../styles/theme';
import { LoadingState } from '../../types';

interface LoadingOverlayProps {
  loadingState: LoadingState;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ loadingState }) => {
  if (!loadingState.isLoading) return null;

  return (
    <View style={styles.loadingOverlay}>
      <View style={styles.loadingModal}>
        <ActivityIndicator size="large" color={colors.primaryLight} />
        <Text style={styles.loadingText}>{loadingState.message}</Text>
        {loadingState.submessage && (
          <Text style={styles.loadingSubtext}>{loadingState.submessage}</Text>
        )}
      </View>
    </View>
  );
};