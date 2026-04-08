import * as React from 'react';
import { createRoot } from 'react-dom/client';

import { grey, blueGrey, teal } from '@mui/material/colors';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import App from './app';

import './index.scss';

const lightTheme = createTheme({
  palette: {
    primary: {
      main: teal[100],
    },
    info: {
      main: grey[900],
    },
  },
});

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: blueGrey[800],
    },
    info: {
      main: grey[50],
    },
  },
});

const darkBG = '#111';
const lightBG = '#eee';

const storedTheme = localStorage.getItem('budgie:theme');
let currentTheme = storedTheme ? (storedTheme === 'dark' ? darkTheme : lightTheme) : darkTheme;
const swapTheme = () => {
  if (currentTheme === lightTheme) {
    currentTheme = darkTheme;
    localStorage.setItem('budgie:theme', 'dark');
    document.body.style.backgroundColor = darkBG;
    if (document.body.parentElement) {
      document.body.parentElement.style.backgroundColor = darkBG;
    }
  } else {
    currentTheme = lightTheme;
    localStorage.setItem('budgie:theme', 'light');
    document.body.style.backgroundColor = lightBG;
    if (document.body.parentElement) {
      document.body.parentElement.style.backgroundColor = lightBG;
    }
  }
  render();
};

function render() {
  const root = createRoot(document.getElementById('react-container') as HTMLElement);
  root.render(
    <ThemeProvider theme={currentTheme}>
      <App swapTheme={swapTheme} />
    </ThemeProvider>,
  );
}

document.addEventListener('DOMContentLoaded', () => {
  if (currentTheme === darkTheme) {
    document.body.style.backgroundColor = darkBG;
    if (document.body.parentElement) {
      document.body.parentElement.style.backgroundColor = darkBG;
    }
  } else {
    document.body.style.backgroundColor = lightBG;
    if (document.body.parentElement) {
      document.body.parentElement.style.backgroundColor = lightBG;
    }
  }
  render();
});
