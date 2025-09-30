/**
 * Integration test for mobile responsiveness and theme switching
 * Tests the complete frontend experience across devices and themes.
 */

import { test, expect } from '@playwright/test'

// Mobile device configurations to test
const mobileDevices = [
  { name: 'iPhone 12', width: 390, height: 844 },
  { name: 'Samsung Galaxy S21', width: 384, height: 854 },
  { name: 'iPad', width: 768, height: 1024 }
]

const desktopSizes = [
  { name: 'Desktop', width: 1920, height: 1080 },
  { name: 'Laptop', width: 1366, height: 768 }
]

test.describe('Mobile Responsiveness and Theme Integration', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/')
    
    // Wait for app to load
    await page.waitForSelector('.app', { timeout: 10000 })
  })

  // Test responsive layout on different screen sizes
  for (const device of [...mobileDevices, ...desktopSizes]) {
    test(`responsive layout on ${device.name}`, async ({ page }) => {
      // Set viewport size
      await page.setViewportSize({ width: device.width, height: device.height })
      
      // Check that main elements are visible and properly positioned
      const appHeader = page.locator('.app-header')
      await expect(appHeader).toBeVisible()
      
      const appMain = page.locator('.app-main')
      await expect(appMain).toBeVisible()
      
      // Check header layout on mobile vs desktop
      if (device.width < 768) {
        // Mobile: header should stack vertically or be more compact
        const headerTitle = page.locator('.app-header h1')
        const themeToggle = page.locator('.theme-toggle')
        
        await expect(headerTitle).toBeVisible()
        await expect(themeToggle).toBeVisible()
        
        // Verify elements don't overflow
        const headerBox = await appHeader.boundingBox()
        expect(headerBox.width).toBeLessThanOrEqual(device.width)
        
      } else {
        // Desktop: header should be horizontal
        const headerTitle = page.locator('.app-header h1')
        const themeToggle = page.locator('.theme-toggle')
        
        await expect(headerTitle).toBeVisible()
        await expect(themeToggle).toBeVisible()
      }
    })
  }

  test('theme switching functionality', async ({ page }) => {
    // Test initial theme (should be light by default)
    const body = page.locator('body')
    const initialClass = await body.getAttribute('class')
    
    // Find and click theme toggle
    const themeToggle = page.locator('.theme-toggle')
    await expect(themeToggle).toBeVisible()
    await themeToggle.click()
    
    // Verify theme changed
    await page.waitForTimeout(500) // Allow for theme transition
    const newClass = await body.getAttribute('class')
    expect(newClass).not.toBe(initialClass)
    
    // Verify theme toggle button updated
    const toggleText = await themeToggle.textContent()
    expect(toggleText).toContain('Light') // Should show opposite of current theme
    
    // Click again to switch back
    await themeToggle.click()
    await page.waitForTimeout(500)
    
    const finalClass = await body.getAttribute('class')
    expect(finalClass).toBe(initialClass)
  })

  test('file upload component mobile interaction', async ({ page }) => {
    // Test on mobile viewport
    await page.setViewportSize({ width: 390, height: 844 })
    
    // Check file upload component
    const uploadZone = page.locator('.upload-zone')
    await expect(uploadZone).toBeVisible()
    
    // Verify upload zone is touch-friendly on mobile
    const uploadBox = await uploadZone.boundingBox()
    expect(uploadBox.height).toBeGreaterThan(100) // Should be large enough for touch
    
    // Test file input accessibility
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeHidden() // Should be hidden but accessible
    
    const chooseFileButton = page.locator('label:has-text("Choose File")')
    await expect(chooseFileButton).toBeVisible()
    
    // Verify button is large enough for touch interaction
    const buttonBox = await chooseFileButton.boundingBox()
    expect(buttonBox.height).toBeGreaterThan(40) // Minimum touch target
    expect(buttonBox.width).toBeGreaterThan(80)
  })

  test('dashboard components mobile layout', async ({ page }) => {
    // Mock a file upload to reach dashboard
    await page.route('/api/upload', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          file_id: 'test-file-id',
          status: 'uploaded',
          message: 'File uploaded successfully'
        })
      })
    })
    
    // Mock status endpoint
    await page.route('/api/upload/test-file-id/status', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          file_id: 'test-file-id',
          status: 'completed',
          progress: 100,
          message: 'Processing complete'
        })
      })
    })
    
    // Simulate file upload
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'test.mp4',
      mimeType: 'video/mp4',
      buffer: Buffer.from('fake video content')
    })
    
    // Wait for dashboard to appear
    await page.waitForSelector('.dashboard', { timeout: 5000 })
    
    // Test mobile viewport
    await page.setViewportSize({ width: 390, height: 844 })
    
    // Verify dashboard elements are mobile-friendly
    const dashboard = page.locator('.dashboard')
    await expect(dashboard).toBeVisible()
    
    // Check that content doesn't overflow
    const dashboardBox = await dashboard.boundingBox()
    expect(dashboardBox.width).toBeLessThanOrEqual(390)
    
    // Verify progress bar is visible
    const progressBar = page.locator('.progress-bar')
    await expect(progressBar).toBeVisible()
  })

  test('theme persistence across page reloads', async ({ page }) => {
    // Switch to dark theme
    const themeToggle = page.locator('.theme-toggle')
    await themeToggle.click()
    await page.waitForTimeout(500)
    
    // Verify dark theme is active
    const bodyClass = await page.locator('body').getAttribute('class')
    expect(bodyClass).toContain('dark')
    
    // Reload page
    await page.reload()
    await page.waitForSelector('.app')
    
    // Verify theme persisted
    const reloadedBodyClass = await page.locator('body').getAttribute('class')
    expect(reloadedBodyClass).toContain('dark')
    
    // Verify toggle shows correct state
    const toggleAfterReload = page.locator('.theme-toggle')
    const toggleText = await toggleAfterReload.textContent()
    expect(toggleText).toContain('Light') // Should show opposite of current theme
  })

  test('touch interactions and gestures', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 })
    
    // Test touch interactions on upload zone
    const uploadZone = page.locator('.upload-zone')
    
    // Simulate touch events
    await uploadZone.hover()
    await expect(uploadZone).toHaveClass(/drag-active|hover/, { timeout: 1000 })
    
    // Test theme toggle touch
    const themeToggle = page.locator('.theme-toggle')
    await themeToggle.tap()
    await page.waitForTimeout(500)
    
    // Verify theme changed
    const bodyClass = await page.locator('body').getAttribute('class')
    expect(bodyClass).toMatch(/(light|dark)/)
  })

  test('accessibility on mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    
    // Test that all interactive elements have proper accessibility
    const themeToggle = page.locator('.theme-toggle')
    const ariaLabel = await themeToggle.getAttribute('aria-label')
    expect(ariaLabel).toMatch(/Switch to (dark|light) theme/)
    
    // Test file input accessibility
    const fileInput = page.locator('input[type="file"]')
    const accept = await fileInput.getAttribute('accept')
    expect(accept).toContain('.mp4') // Should specify accepted formats
    
    // Test keyboard navigation
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    
    // Verify focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement.tagName)
    expect(['BUTTON', 'INPUT', 'LABEL']).toContain(focusedElement)
  })

  test('performance on mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    
    // Measure page load time
    const startTime = Date.now()
    await page.goto('/')
    await page.waitForSelector('.app')
    const loadTime = Date.now() - startTime
    
    // Should load within reasonable time on mobile
    expect(loadTime).toBeLessThan(5000) // 5 seconds max
    
    // Test theme switching performance
    const themeStartTime = Date.now()
    await page.locator('.theme-toggle').click()
    await page.waitForTimeout(100) // Wait for transition
    const themeTime = Date.now() - themeStartTime
    
    // Theme switching should be fast
    expect(themeTime).toBeLessThan(1000) // 1 second max
  })

  test('viewport meta tag and mobile optimization', async ({ page }) => {
    // Check that viewport meta tag exists for proper mobile rendering
    const viewportMeta = await page.locator('meta[name="viewport"]').getAttribute('content')
    expect(viewportMeta).toContain('width=device-width')
    expect(viewportMeta).toContain('initial-scale=1')
    
    // Check that theme-color meta tag updates with theme
    const themeToggle = page.locator('.theme-toggle')
    
    // Check initial theme color
    let themeColorMeta = await page.locator('meta[name="theme-color"]').getAttribute('content')
    const initialThemeColor = themeColorMeta
    
    // Switch theme
    await themeToggle.click()
    await page.waitForTimeout(500)
    
    // Check theme color updated
    themeColorMeta = await page.locator('meta[name="theme-color"]').getAttribute('content')
    expect(themeColorMeta).not.toBe(initialThemeColor)
  })
})

// Helper function to simulate file upload
async function simulateFileUpload(page, fileName = 'test.mp4') {
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles({
    name: fileName,
    mimeType: 'video/mp4',
    buffer: Buffer.from('fake video content for testing')
  })
}
