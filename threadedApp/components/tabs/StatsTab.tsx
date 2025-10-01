import React from 'react';
import { View, Text, ScrollView } from 'react-native';
import { styles } from '../../styles/theme';
import { Stats } from '../../types';

interface StatsTabProps {
  stats: Stats | null;
}

export const StatsTab: React.FC<StatsTabProps> = ({ stats }) => {
  const shirtCount = stats?.wardrobe_items?.shirt || 0;
  const pantsCount = stats?.wardrobe_items?.pants || 0;
  const shoesCount = stats?.wardrobe_items?.shoes || 0;
  const totalCombinations = shirtCount * pantsCount * shoesCount;

  return (
    <View style={styles.tabContent}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>stats</Text>
      </View>
      
      <ScrollView style={styles.statsContent}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Items in wardrobe</Text>
          <Text style={styles.statValue}>{stats?.total_items || 0}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Total outfit combinations</Text>
          <Text style={styles.statValue}>{totalCombinations}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Outfits rated</Text>
          <Text style={styles.statValue}>{stats?.total_ratings || 0}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Ratings until next update</Text>
          <Text style={styles.statValue}>
            {stats ? 5 - (stats.total_ratings % 5) : 5}
          </Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Current model</Text>
          <Text style={styles.statValue}>
            {stats?.active_model || 'No model yet'}
          </Text>
        </View>
        
        <View style={styles.projectCredit}>
          <Text style={styles.projectCreditText}>a project by daniel cao</Text>
        </View>
      </ScrollView>
    </View>
  );
};