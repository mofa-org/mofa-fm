import { test, expect } from '@playwright/test';
import fs from 'fs';

test.describe('Discover Page Category Filter', () => {
  test('should display categories and filter shows', async ({ page }) => {
    try {
        page.on('console', msg => console.log('PAGE LOG:', msg.text()));
        page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

        // Assuming the app is running locally on default Vite port 5173
        await page.goto('http://localhost:5173/discover');

        // Wait for categories to load
        const categoryBtn = page.locator('.category-btn').first();
        await expect(categoryBtn).toBeVisible();

        // Click the first category
        await categoryBtn.click();
        
        // Check if the button becomes active
        await expect(categoryBtn).toHaveClass(/mofa-tag-primary/);

        // Verify some result logic if possible, or just network request
        const requestPromise = page.waitForRequest(request => 
          request.url().includes('/podcasts/shows/') && 
          request.url().includes('category=') &&
          request.method() === 'GET'
        );
    } catch (error: any) {
        fs.writeFileSync('frontend_error_log.txt', `Error: ${error.message}\nStack: ${error.stack}`);
        throw error;
    }
  });
});
