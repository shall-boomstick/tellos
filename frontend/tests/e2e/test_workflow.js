/**
 * End-to-end tests for SawtFeel application workflow.
 * Tests complete user journeys using videos/aggression.mp4 as test data.
 */

import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

// Test configuration
const TEST_VIDEO_PATH = path.join(process.cwd(), '../videos/aggression.mp4');
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('SawtFeel E2E Workflow Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto(BASE_URL);
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('Complete workflow: Upload → Process → Analyze → Playback', async ({ page }) => {
    // Verify initial page load
    await expect(page.locator('h1')).toContainText('SawtFeel');
    await expect(page.locator('.welcome-section')).toBeVisible();
    
    // Check if test video exists
    if (!fs.existsSync(TEST_VIDEO_PATH)) {
      test.skip('Test video not found: videos/aggression.mp4');
    }

    // Step 1: Upload video file
    await test.step('Upload video file', async () => {
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(TEST_VIDEO_PATH);
      
      // Wait for upload to complete
      await expect(page.locator('.upload-progress')).toBeVisible();
      await expect(page.locator('.upload-progress')).toBeHidden({ timeout: 30000 });
      
      // Verify navigation to dashboard
      await expect(page.locator('.dashboard')).toBeVisible();
      await expect(page.locator('.file-info')).toContainText('aggression.mp4');
    });

    // Step 2: Monitor processing progress
    await test.step('Monitor processing progress', async () => {
      // Check initial processing status
      await expect(page.locator('.processing-status')).toBeVisible();
      await expect(page.locator('.progress-bar')).toBeVisible();
      
      // Wait for each processing stage
      await expect(page.locator('.status-extracting')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('.status-transcribing')).toBeVisible({ timeout: 30000 });
      await expect(page.locator('.status-analyzing')).toBeVisible({ timeout: 45000 });
      
      // Wait for processing completion (2-minute limit as per requirements)
      await expect(page.locator('.status-completed')).toBeVisible({ timeout: 120000 });
      await expect(page.locator('.processing-complete')).toBeVisible();
    });

    // Step 3: Verify results display
    await test.step('Verify analysis results', async () => {
      // Check audio player is visible
      await expect(page.locator('.audio-player')).toBeVisible();
      await expect(page.locator('.play-button')).toBeVisible();
      
      // Check emotion gauge is displayed
      await expect(page.locator('.emotion-gauge')).toBeVisible();
      await expect(page.locator('.current-emotion')).toBeVisible();
      await expect(page.locator('.confidence-score')).toBeVisible();
      
      // Verify emotion is detected (should show aggression/anger for test video)
      const emotionText = await page.locator('.current-emotion').textContent();
      expect(['Anger', 'Aggression', 'Negative']).toContain(emotionText);
      
      // Check transcript is displayed
      await expect(page.locator('.transcript')).toBeVisible();
      await expect(page.locator('.transcript-text')).not.toBeEmpty();
      
      // Verify Arabic text is present (RTL direction)
      const transcript = page.locator('.transcript-container');
      await expect(transcript).toHaveAttribute('dir', 'rtl');
    });

    // Step 4: Test playback functionality
    await test.step('Test audio playback and synchronization', async () => {
      // Start playback
      await page.locator('.play-button').click();
      await expect(page.locator('.pause-button')).toBeVisible();
      
      // Verify progress updates
      await page.waitForTimeout(2000); // Let it play for 2 seconds
      const progressBefore = await page.locator('.progress-slider').getAttribute('value');
      
      await page.waitForTimeout(2000); // Wait another 2 seconds
      const progressAfter = await page.locator('.progress-slider').getAttribute('value');
      
      expect(parseFloat(progressAfter)).toBeGreaterThan(parseFloat(progressBefore));
      
      // Test pause functionality
      await page.locator('.pause-button').click();
      await expect(page.locator('.play-button')).toBeVisible();
      
      // Test scrubbing (seeking)
      await page.locator('.progress-slider').fill('10'); // Seek to 10 seconds
      await page.waitForTimeout(500);
      
      const currentTime = await page.locator('.current-time').textContent();
      expect(currentTime).toContain('0:10');
    });

    // Step 5: Test real-time emotion and transcript updates
    await test.step('Test real-time synchronization', async () => {
      // Start playback
      await page.locator('.play-button').click();
      
      // Monitor emotion updates during playback
      const initialEmotion = await page.locator('.current-emotion').textContent();
      
      // Let it play for a few seconds
      await page.waitForTimeout(5000);
      
      // Check if emotion timeline shows segments
      await expect(page.locator('.emotion-timeline')).toBeVisible();
      const timelineSegments = page.locator('.timeline-segment');
      await expect(timelineSegments).toHaveCount.greaterThan(0);
      
      // Check transcript word highlighting
      await expect(page.locator('.current-word')).toBeVisible();
      
      // Pause and verify highlighting stops
      await page.locator('.pause-button').click();
      await page.waitForTimeout(1000);
    });

    // Step 6: Test mobile responsiveness
    await test.step('Test mobile responsiveness', async () => {
      // Switch to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Verify mobile layout
      await expect(page.locator('.app')).toHaveClass(/mobile/);
      await expect(page.locator('.audio-player')).toBeVisible();
      await expect(page.locator('.emotion-gauge')).toBeVisible();
      
      // Test mobile controls
      await page.locator('.play-button').tap();
      await expect(page.locator('.pause-button')).toBeVisible();
      
      // Test mobile scrubbing
      const progressSlider = page.locator('.progress-slider');
      await progressSlider.tap();
      
      // Reset to desktop viewport
      await page.setViewportSize({ width: 1280, height: 720 });
    });
  });

  test('Theme switching functionality', async ({ page }) => {
    // Test light to dark theme
    await test.step('Switch to dark theme', async () => {
      await expect(page.locator('body')).toHaveClass(/light/);
      
      await page.locator('.theme-toggle').click();
      await expect(page.locator('body')).toHaveClass(/dark/);
      
      // Verify dark theme colors
      const backgroundColor = await page.locator('body').evaluate(
        el => getComputedStyle(el).backgroundColor
      );
      expect(backgroundColor).toContain('rgb(15, 23, 42)'); // Dark background
    });

    // Test dark to light theme
    await test.step('Switch back to light theme', async () => {
      await page.locator('.theme-toggle').click();
      await expect(page.locator('body')).toHaveClass(/light/);
      
      // Verify light theme colors
      const backgroundColor = await page.locator('body').evaluate(
        el => getComputedStyle(el).backgroundColor
      );
      expect(backgroundColor).toContain('rgb(255, 255, 255)'); // Light background
    });

    // Test theme persistence
    await test.step('Test theme persistence', async () => {
      await page.locator('.theme-toggle').click(); // Switch to dark
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      // Should remember dark theme
      await expect(page.locator('body')).toHaveClass(/dark/);
    });
  });

  test('Error handling and edge cases', async ({ page }) => {
    // Test invalid file upload
    await test.step('Test invalid file upload', async () => {
      // Create a temporary text file
      const invalidFile = path.join(process.cwd(), 'temp_invalid.txt');
      fs.writeFileSync(invalidFile, 'This is not a video file');
      
      try {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(invalidFile);
        
        // Should show error message
        await expect(page.locator('.error-message')).toBeVisible();
        await expect(page.locator('.error-message')).toContainText(/unsupported file type/i);
      } finally {
        // Clean up temp file
        if (fs.existsSync(invalidFile)) {
          fs.unlinkSync(invalidFile);
        }
      }
    });

    // Test large file upload
    await test.step('Test large file rejection', async () => {
      // This would require a large file, so we'll test the UI validation
      const fileInput = page.locator('input[type="file"]');
      
      // Mock file size validation by checking the client-side validation
      await page.evaluate(() => {
        const input = document.querySelector('input[type="file"]');
        const mockLargeFile = new File(['x'.repeat(200 * 1024 * 1024)], 'large.mp4', {
          type: 'video/mp4'
        });
        
        // Simulate file size check
        const event = new Event('change', { bubbles: true });
        Object.defineProperty(event, 'target', {
          value: { files: [mockLargeFile] },
          enumerable: true
        });
        
        input.dispatchEvent(event);
      });
      
      // Should show file size error
      await expect(page.locator('.error-message')).toContainText(/file too large/i);
    });

    // Test network error handling
    await test.step('Test network error handling', async () => {
      // Intercept upload request and return error
      await page.route('**/api/upload', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' })
        });
      });
      
      if (fs.existsSync(TEST_VIDEO_PATH)) {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_VIDEO_PATH);
        
        // Should show network error
        await expect(page.locator('.error-message')).toBeVisible();
        await expect(page.locator('.error-message')).toContainText(/server error/i);
      }
    });
  });

  test('WebSocket real-time updates', async ({ page }) => {
    if (!fs.existsSync(TEST_VIDEO_PATH)) {
      test.skip('Test video not found: videos/aggression.mp4');
    }

    await test.step('Test WebSocket connection and updates', async () => {
      // Upload file
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(TEST_VIDEO_PATH);
      
      // Monitor WebSocket messages
      const wsMessages = [];
      page.on('websocket', ws => {
        ws.on('framesent', event => {
          wsMessages.push({ type: 'sent', data: event.payload });
        });
        ws.on('framereceived', event => {
          wsMessages.push({ type: 'received', data: event.payload });
        });
      });
      
      // Wait for processing to start
      await expect(page.locator('.processing-status')).toBeVisible();
      
      // Wait a bit for WebSocket messages
      await page.waitForTimeout(5000);
      
      // Verify WebSocket communication occurred
      expect(wsMessages.length).toBeGreaterThan(0);
      
      // Check for specific message types
      const receivedMessages = wsMessages.filter(msg => msg.type === 'received');
      const messageTypes = receivedMessages.map(msg => {
        try {
          return JSON.parse(msg.data).type;
        } catch {
          return 'unknown';
        }
      });
      
      expect(messageTypes).toContain('progress_update');
    });
  });

  test('Performance requirements validation', async ({ page }) => {
    if (!fs.existsSync(TEST_VIDEO_PATH)) {
      test.skip('Test video not found: videos/aggression.mp4');
    }

    await test.step('Validate processing time requirements', async () => {
      const startTime = Date.now();
      
      // Upload file
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(TEST_VIDEO_PATH);
      
      // Wait for processing completion
      await expect(page.locator('.status-completed')).toBeVisible({ timeout: 120000 });
      
      const endTime = Date.now();
      const processingTime = (endTime - startTime) / 1000; // Convert to seconds
      
      // Should complete within 2 minutes (120 seconds) as per requirements
      expect(processingTime).toBeLessThan(120);
      
      console.log(`Processing completed in ${processingTime} seconds`);
    });

    await test.step('Validate audio extraction latency', async () => {
      // This would be tested by monitoring the extraction phase
      await expect(page.locator('.status-extracting')).toBeVisible();
      
      const extractionStart = Date.now();
      await expect(page.locator('.status-transcribing')).toBeVisible({ timeout: 10000 });
      const extractionTime = (Date.now() - extractionStart) / 1000;
      
      // Audio extraction should be fast (< 10 seconds for test video)
      expect(extractionTime).toBeLessThan(10);
      
      console.log(`Audio extraction completed in ${extractionTime} seconds`);
    });
  });

  test('Accessibility compliance', async ({ page }) => {
    await test.step('Test keyboard navigation', async () => {
      // Test tab navigation
      await page.keyboard.press('Tab');
      await expect(page.locator(':focus')).toBeVisible();
      
      // Test file upload with keyboard
      await page.keyboard.press('Enter'); // Should trigger file dialog
      
      // Test theme toggle with keyboard
      const themeToggle = page.locator('.theme-toggle');
      await themeToggle.focus();
      await page.keyboard.press('Enter');
      
      // Verify theme changed
      await expect(page.locator('body')).toHaveClass(/dark/);
    });

    await test.step('Test ARIA labels and roles', async () => {
      // Check for proper ARIA labels
      await expect(page.locator('[role="button"]')).toHaveCount.greaterThan(0);
      await expect(page.locator('[aria-label]')).toHaveCount.greaterThan(0);
      
      // Check for proper heading structure
      await expect(page.locator('h1')).toHaveCount(1);
      await expect(page.locator('h2, h3, h4, h5, h6')).toHaveCount.greaterThan(0);
    });

    await test.step('Test screen reader compatibility', async () => {
      // Check for proper semantic HTML
      await expect(page.locator('main')).toBeVisible();
      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('footer')).toBeVisible();
      
      // Check for alt text on images
      const images = page.locator('img');
      const imageCount = await images.count();
      
      for (let i = 0; i < imageCount; i++) {
        const img = images.nth(i);
        await expect(img).toHaveAttribute('alt');
      }
    });
  });

  test('Data validation and security', async ({ page }) => {
    await test.step('Test XSS prevention', async () => {
      // This would involve testing that user input is properly sanitized
      // For now, we'll check that the application doesn't execute script content
      
      const maliciousInput = '<script>alert("xss")</script>';
      
      // If there were text inputs, we'd test them here
      // For file upload, we verify that filenames are sanitized
      
      const scriptTags = page.locator('script:not([src]):not([type="application/json"])');
      const scriptCount = await scriptTags.count();
      
      // Verify no inline scripts were injected
      for (let i = 0; i < scriptCount; i++) {
        const scriptContent = await scriptTags.nth(i).textContent();
        expect(scriptContent).not.toContain('alert');
      }
    });

    await test.step('Test file upload validation', async () => {
      // Test file type validation
      const textFile = path.join(process.cwd(), 'temp_test.txt');
      fs.writeFileSync(textFile, 'test content');
      
      try {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(textFile);
        
        await expect(page.locator('.error-message')).toContainText(/unsupported file type/i);
      } finally {
        if (fs.existsSync(textFile)) {
          fs.unlinkSync(textFile);
        }
      }
    });
  });
});

// Utility functions for E2E tests
test.describe('Test Utilities', () => {
  test('Verify test video exists and is valid', async ({ page }) => {
    const videoExists = fs.existsSync(TEST_VIDEO_PATH);
    const videoStats = videoExists ? fs.statSync(TEST_VIDEO_PATH) : null;
    
    console.log('Test video path:', TEST_VIDEO_PATH);
    console.log('Video exists:', videoExists);
    console.log('Video size:', videoStats ? `${videoStats.size} bytes` : 'N/A');
    
    if (videoExists) {
      expect(videoStats.size).toBeGreaterThan(1000); // At least 1KB
      expect(TEST_VIDEO_PATH).toMatch(/\.mp4$/i);
    } else {
      console.warn('Test video not found. Some E2E tests will be skipped.');
    }
  });

  test('Verify API endpoints are accessible', async ({ page }) => {
    // Test health endpoint
    const response = await page.request.get(`${API_URL}/health`);
    expect(response.status()).toBe(200);
    
    const healthData = await response.json();
    expect(healthData.status).toBe('healthy');
    
    // Test upload endpoint availability
    const uploadResponse = await page.request.post(`${API_URL}/api/upload`, {
      multipart: {
        file: {
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('test')
        }
      }
    });
    
    // Should return error for invalid file type, but endpoint should be accessible
    expect([400, 422]).toContain(uploadResponse.status());
  });
});
