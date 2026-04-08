import { MD3DarkTheme, MD3LightTheme } from 'react-native-paper';

export const darkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    background: '#1c2836',
    surface: '#2f3a49',
    primary: '#4fc3f7',
    error: '#ef5350',
  },
};

export const lightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    background: '#f5f5f5',
    surface: '#ffffff',
    primary: '#0288d1',
    error: '#d32f2f',
  },
};

export type ThemeMode = 'dark' | 'light';

export function getTheme(mode: ThemeMode) {
  return mode === 'dark' ? darkTheme : lightTheme;
}

// Keep backward-compatible default export
export const appTheme = darkTheme;
