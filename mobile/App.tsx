import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PaperProvider } from 'react-native-paper';
import { NavigationContainer } from '@react-navigation/native';
import { getTheme } from './src/theme';
import { useStore } from './src/store/store';
import BottomTabNavigator from './src/navigation/BottomTabNavigator';
import OnboardingDialog from './src/components/OnboardingDialog';

export default function App() {
  const themeMode = useStore((s) => s.themeMode);
  const theme = getTheme(themeMode);
  const selectedProfileId = useStore((s) => s.selectedProfileId);
  const onboardingCompleted = useStore((s) => s.onboardingCompleted);
  const setOnboardingCompleted = useStore((s) => s.setOnboardingCompleted);

  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <NavigationContainer>
          <BottomTabNavigator />
        </NavigationContainer>
        <OnboardingDialog
          visible={!!selectedProfileId && !onboardingCompleted}
          onComplete={() => setOnboardingCompleted(true)}
        />
      </PaperProvider>
    </SafeAreaProvider>
  );
}
