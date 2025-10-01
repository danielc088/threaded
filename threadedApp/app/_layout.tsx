import { Stack } from "expo-router";
import { useFonts } from 'expo-font';
import { 
  NotoSerifGurmukhi_300Light,
  NotoSerifGurmukhi_600SemiBold,
  NotoSerifGurmukhi_800ExtraBold,
  NotoSerifGurmukhi_900Black
} from '@expo-google-fonts/noto-serif-gurmukhi';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path, G } from 'react-native-svg';

SplashScreen.preventAutoHideAsync();

// Custom Spool Icon Component
const SpoolIcon = () => (
  <Svg width="32" height="32" viewBox="0 0 512 512">
    <G>
      <G>
        <Path 
          d="M495.304,172.522h-27.826c-36.824,0-66.783,29.959-66.783,66.783v66.783c0,18.412-14.979,33.391-33.391,33.391h-33.391
			V105.739h16.696c27.618,0,50.087-22.469,50.087-50.087V16.696C400.696,7.475,393.22,0,384,0H16.696C7.475,0,0,7.475,0,16.696
			v38.956c0,27.618,22.469,50.087,50.087,50.087h16.696v300.522H50.087C22.469,406.261,0,428.73,0,456.348v38.956
			C0,504.525,7.475,512,16.696,512H384c9.22,0,16.696-7.475,16.696-16.696v-38.956c0-27.618-22.469-50.087-50.087-50.087h-16.696
			V372.87h33.391c36.824,0,66.783-29.959,66.783-66.783v-66.783c0-18.412,14.979-33.391,33.391-33.391h27.826
			c9.22,0,16.696-7.475,16.696-16.696S504.525,172.522,495.304,172.522z M350.609,439.652c9.206,0,16.696,7.49,16.696,16.696v22.261
			H33.391v-22.261c0-9.206,7.49-16.696,16.696-16.696C60.668,439.652,338.679,439.652,350.609,439.652z M300.522,172.522v33.391
			H100.174v-33.391H300.522z M100.174,139.13v-33.391h200.348v33.391H100.174z M300.522,239.304v33.391H100.174v-33.391H300.522z
			 M300.522,306.087v33.391H100.174v-33.391H300.522z M300.522,372.87v33.391H100.174V372.87H300.522z M50.087,72.348
			c-9.206,0-16.696-7.49-16.696-16.696V33.391h333.913v22.261c0,9.206-7.49,16.696-16.696,16.696
			C338.68,72.348,60.712,72.348,50.087,72.348z"
          fill="#059669"
        />
      </G>
    </G>
  </Svg>
);

export default function RootLayout() {
  const [loaded, error] = useFonts({
    'NotoSerifGurmukhi-Light': NotoSerifGurmukhi_300Light,
    'NotoSerifGurmukhi-SemiBold': NotoSerifGurmukhi_600SemiBold,
    'NotoSerifGurmukhi-ExtraBold': NotoSerifGurmukhi_800ExtraBold,
    'NotoSerifGurmukhi-Black': NotoSerifGurmukhi_900Black,
  });

  useEffect(() => {
    if (loaded || error) {
      SplashScreen.hideAsync();
    }
  }, [loaded, error]);

  if (!loaded && !error) {
    return null;
  }

  return (
    <Stack>
      <Stack.Screen 
        name="index" 
        options={{ 
          headerTitle: () => (
            <View style={headerStyles.container}>
              <SpoolIcon/>
              <Text style={headerStyles.title}>threaded</Text>
            </View>
          ),
          headerShown: true,
        }} 
      />
    </Stack>
  );
}

const headerStyles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 42,
    fontFamily: 'NotoSerifGurmukhi-Black',
    color: '#059669',
  },
});