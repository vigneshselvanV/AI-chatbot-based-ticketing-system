import { useState, useEffect } from 'react';

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem(
      'busbot-theme'
    );
    if (saved) return saved === 'dark';
    return window.matchMedia(
      '(prefers-color-scheme: dark)'
    ).matches;
  });

  useEffect(() => {
    const theme = isDark ? 'dark' : 'light';
    document.documentElement
      .setAttribute('data-theme', theme);
    localStorage.setItem('busbot-theme', theme);
  }, [isDark]);

  // Set theme immediately on mount
  useEffect(() => {
    const saved = localStorage.getItem(
      'busbot-theme'
    );
    const theme = saved || (
      window.matchMedia(
        '(prefers-color-scheme: dark)'
      ).matches ? 'dark' : 'light'
    );
    document.documentElement
      .setAttribute('data-theme', theme);
  }, []);

  return (
    <button
      className="theme-toggle-btn"
      onClick={() => setIsDark(d => !d)}
      title={isDark
        ? 'Switch to Light Mode ☀️'
        : 'Switch to Dark Mode 🌙'
      }
      aria-label="Toggle theme"
    >
      <div className={`toggle-track ${
        isDark ? 'is-dark' : 'is-light'
      }`}>
        <span className="t-icon t-sun">☀️</span>
        <span className="t-icon t-moon">🌙</span>
        <div className={`toggle-thumb ${
          isDark ? 'thumb-right' : 'thumb-left'
        }`} />
      </div>
    </button>
  );
}
