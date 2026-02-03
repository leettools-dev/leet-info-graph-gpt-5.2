import { describe, expect, it } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'
import { App } from './App'


describe('App', () => {
  it('disables send when prompt is too short', () => {
    render(<App />)
    const btn = screen.getByRole('button', { name: /submit prompt/i }) as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })
})
