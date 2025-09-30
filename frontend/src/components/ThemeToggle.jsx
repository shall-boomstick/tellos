import React from 'react'

const ThemeToggle = ({ theme, onToggle }) => {
  return (
    <button
      className="theme-toggle btn btn-secondary"
      onClick={onToggle}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
    >
      {theme === 'light' ? '🌙' : '☀️'}
      <span className="theme-text">
        {theme === 'light' ? 'Dark' : 'Light'}
      </span>
    </button>
  )
}

export default ThemeToggle
