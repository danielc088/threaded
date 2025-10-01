import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Animated } from 'react-native';
import { MaterialCommunityIcons, Ionicons, Feather } from '@expo/vector-icons';
import { styles } from '../styles/theme';
import { Stats, Tab, LoadingState } from '../types';
import { getStats } from '../services/api';
import { WardrobeTab } from '../components/tabs/WardrobeTab';
import { OutfitsTab } from '../components/tabs/OutfitsTab';
import { StatsTab } from '../components/tabs/StatsTab';
import { LoadingOverlay } from '../components/shared/LoadingOverlay';

export default function App() {
  const [currentTab, setCurrentTab] = useState<Tab>('wardrobe');
  const [stats, setStats] = useState<Stats | null>(null);
  const [autoGenerateItem, setAutoGenerateItem] = useState<{type: string, id: string} | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: false, message: '' });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async (): Promise<void> => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.log('Error loading stats:', error);
    }
  };

  const renderTab = () => {
    switch (currentTab) {
      case 'wardrobe':
        return (
          <WardrobeTab 
            loadStats={loadStats} 
            setCurrentTab={setCurrentTab} 
            setAutoGenerateItem={setAutoGenerateItem} 
            setLoadingState={setLoadingState} 
          />
        );
      case 'outfits':
        return (
          <OutfitsTab 
            loadStats={loadStats} 
            autoGenerateItem={autoGenerateItem} 
            setAutoGenerateItem={setAutoGenerateItem} 
            setLoadingState={setLoadingState} 
          />
        );
      case 'stats':
        return <StatsTab stats={stats} />;
      default:
        return (
          <WardrobeTab 
            loadStats={loadStats} 
            setCurrentTab={setCurrentTab} 
            setAutoGenerateItem={setAutoGenerateItem} 
            setLoadingState={setLoadingState} 
          />
        );
    }
  };

  return (
    <View style={styles.container}>
      {renderTab()}
      
      <LoadingOverlay loadingState={loadingState} />
      
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tabButton, currentTab === 'wardrobe' && styles.tabButtonActive]}
          onPress={() => setCurrentTab('wardrobe')}
          activeOpacity={0.7}
        >
          <MaterialCommunityIcons 
            name="wardrobe-outline" 
            size={20} 
            color={currentTab === 'wardrobe' ? '#065f46' : '#9ca3af'} 
            style={styles.tabButtonIcon}
          />
          <Text style={[styles.tabButtonText, currentTab === 'wardrobe' && styles.tabButtonTextActive]}>
            wardrobe
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabButton, currentTab === 'outfits' && styles.tabButtonActive]}
          onPress={() => setCurrentTab('outfits')}
          activeOpacity={0.7}
        >
          <Ionicons 
            name="shirt-outline" 
            size={20} 
            color={currentTab === 'outfits' ? '#065f46' : '#9ca3af'} 
            style={styles.tabButtonIcon}
          />
          <Text style={[styles.tabButtonText, currentTab === 'outfits' && styles.tabButtonTextActive]}>
            outfits
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabButton, currentTab === 'stats' && styles.tabButtonActive]}
          onPress={() => setCurrentTab('stats')}
          activeOpacity={0.7}
        >
          <Feather 
            name="settings" 
            size={20} 
            color={currentTab === 'stats' ? '#065f46' : '#9ca3af'} 
            style={styles.tabButtonIcon}
          />
          <Text style={[styles.tabButtonText, currentTab === 'stats' && styles.tabButtonTextActive]}>
            stats
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}