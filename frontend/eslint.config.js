import js from '@eslint/js'
import tsParser from '@typescript-eslint/parser'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import jsxA11y from 'eslint-plugin-jsx-a11y'

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true }
      },
      globals: {
        document: 'readonly',
        window: 'readonly',
        fetch: 'readonly',
        URL: 'readonly',
        Blob: 'readonly',
        HTMLButtonElement: 'readonly'
      }
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      'jsx-a11y': jsxA11y
    },
    rules: {
      ...jsxA11y.configs.recommended.rules
    }
  }
]
