import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import './utils/fixLeafletIcons';

// Force dark theme permanently — light theme removed
document.documentElement.setAttribute('data-theme', 'dark');
localStorage.setItem('busbot-theme', 'dark');


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
