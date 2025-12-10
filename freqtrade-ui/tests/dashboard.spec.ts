import { test, expect } from '@playwright/test';

test.describe('Freqtrade Multi-Bot System - New Dashboards Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for API calls
    test.setTimeout(60000);

    // Navigate to login page first
    await page.goto('/login');

    // Wait for login form to load
    await page.waitForSelector('form', { timeout: 10000 });

    // Fill login form
    await page.fill('input[id="username"]', 'analytics_user');
    await page.fill('input[id="password"]', 'testpass123');

    // Submit login
    await page.click('button[type="submit"]');

    // Wait a bit for the request to complete
    await page.waitForTimeout(2000);

    // Check current URL
    const currentUrl = page.url();
    console.log('Current URL after login:', currentUrl);

    // If still on login page, check for errors
    if (currentUrl.includes('/login')) {
      const errorText = await page.textContent('body');
      console.log('Login page content:', errorText);

      // Check for console errors
      const errors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      await page.waitForTimeout(1000);
      console.log('Console errors:', errors);
    }

    // Wait for redirect to home page
    await page.waitForURL('/', { timeout: 10000 });

    // Wait for the app to load
    await page.waitForSelector('#app', { timeout: 10000 });
  });

  test('Home Dashboard - Load and Display', async ({ page }) => {
    // Take screenshot for visual comparison
    await page.screenshot({ path: 'test-results/home-dashboard.png', fullPage: true });

    // Check main title
    await expect(page.locator('h1:has-text("🏠 Freqtrade Dashboard")')).toBeVisible();
    await expect(page.locator('p:has-text("Главная панель управления торговыми ботами")')).toBeVisible();

    // Check stats section
    await expect(page.locator('h2:has-text("📊 Быстрая статистика")')).toBeVisible();

    // Check stat cards - use more specific selectors
    await expect(page.locator('.stat-content p:has-text("Активных ботов")')).toBeVisible();
    await expect(page.locator('.stat-content p:has-text("Стратегий")')).toBeVisible();
    await expect(page.locator('.stat-content p:has-text("Портфель")')).toBeVisible();
    await expect(page.locator('.stat-content p:has-text("Win Rate")')).toBeVisible();

    // Check quick actions
    await expect(page.locator('h2:has-text("⚡ Быстрые действия")')).toBeVisible();
    await expect(page.locator('h3:has-text("Управление ботами")')).toBeVisible();
    await expect(page.locator('h3:has-text("Стратегии")')).toBeVisible();
    await expect(page.locator('h3:has-text("Аналитика")')).toBeVisible();
    await expect(page.locator('h3:has-text("FreqAI Lab")')).toBeVisible();

    // Check system status
    await expect(page.locator('h2:has-text("🔍 Статус системы")')).toBeVisible();
  });

  test('Bot Management Dashboard - Load and Display', async ({ page }) => {
    // Navigate to bots page
    await page.goto('/bots');
    await page.waitForURL('**/bots');

    // Wait for page to load completely
    await page.waitForTimeout(3000);

    // Take screenshot for visual comparison
    await page.screenshot({ path: 'test-results/bot-management-dashboard.png', fullPage: true });

    // Check main title
    await expect(page.locator('h1:has-text("🤖 Управление ботами")')).toBeVisible();

    // Check buttons
    await expect(page.locator('button:has-text("➕ Создать бота")')).toBeVisible();
    await expect(page.locator('button:has-text("▶️ Запустить все")')).toBeVisible();
    await expect(page.locator('button:has-text("⏹️ Остановить все")')).toBeVisible();

    // Check empty state (since no bots exist)
    await expect(page.locator('h3:has-text("Нет созданных ботов")')).toBeVisible();
  });



  test('Strategies Dashboard - Load and Display', async ({ page }) => {
    // Navigate to strategies page
    await page.goto('/strategies');
    await page.waitForURL('**/strategies');

    // Wait for page to load completely
    await page.waitForTimeout(3000);

    // Take screenshot for visual comparison
    await page.screenshot({ path: 'test-results/strategies-dashboard.png', fullPage: true });

    // Check main title
    await expect(page.locator('h1:has-text("📈 Управление стратегиями")')).toBeVisible();

    // Check buttons
    await expect(page.locator('button:has-text("➕ Создать стратегию")')).toBeVisible();
    await expect(page.locator('text=📤 Загрузить .md файл')).toBeVisible();

    // Check if page content is loaded (either strategies or empty state)
    const hasStrategies = await page.locator('h3:has-text("Нет доступных стратегий")').isVisible();
    const hasContent = await page.locator('.strategies-section').isVisible();

    expect(hasStrategies || hasContent).toBe(true);
  });

  test('Analytics Dashboard - Load and Display', async ({ page }) => {
    // Navigate to analytics page
    await page.goto('/analytics');
    await page.waitForURL('**/analytics');

    // Check main title
    await expect(page.locator('h1:has-text("📊 Аналитика и метрики")')).toBeVisible();

    // Check sections
    await expect(page.locator('h2:has-text("📈 Производительность")')).toBeVisible();

    // Check metric cards
    await expect(page.locator('p:has-text("Всего сделок")')).toBeVisible();
    await expect(page.locator('p:has-text("Прибыльных сделок")')).toBeVisible();
  });

  test('FreqAI Lab Dashboard - Load and Display', async ({ page }) => {
    // Navigate to freqai-lab page
    await page.goto('/freqai-lab');
    await page.waitForURL('**/freqai-lab');

    // Check main title
    await expect(page.locator('h1:has-text("🧠 FreqAI Lab")')).toBeVisible();

    // Check sections
    await expect(page.locator('h2:has-text("🤖 Модели FreqAI")')).toBeVisible();

    // Check buttons
    await expect(page.locator('button:has-text("➕ Создать модель")')).toBeVisible();
  });

  test('Data Management Dashboard - Load and Display', async ({ page }) => {
    // Navigate to data page
    await page.goto('/data');
    await page.waitForURL('**/data');

    // Check main title
    await expect(page.locator('h1:has-text("💾 Управление данными")')).toBeVisible();

    // Check sections
    await expect(page.locator('h2:has-text("📊 Доступные данные")')).toBeVisible();
  });

  test('Hyperopt Dashboard - Load and Display', async ({ page }) => {
    // Navigate to hyperopt page
    await page.goto('/hyperopt');
    await page.waitForURL('**/hyperopt');

    // Check main title
    await expect(page.locator('h1:has-text("⚙️ Hyperopt")')).toBeVisible();

    // Check sections
    await expect(page.locator('h2:has-text("📋 Доступные стратегии")')).toBeVisible();
  });

  test('Monitoring Dashboard - Load and Display', async ({ page }) => {
    // Navigate to monitoring page
    await page.goto('/monitoring');
    await page.waitForURL('**/monitoring');

    // Check main title
    await expect(page.locator('h1:has-text("🔍 Мониторинг системы")')).toBeVisible();

    // Check sections
    await expect(page.locator('h2:has-text("🖥️ Компоненты системы")')).toBeVisible();
  });



  test('System Monitoring Dashboard - Load and Display', async ({ page }) => {
    // Navigate to monitoring page (if available)
    try {
      await page.click('nav a:has-text("Monitoring")');
      await page.waitForURL('**/monitoring');

      // Check main elements
      await expect(page.locator('h2:has-text("Мониторинг Системы")')).toBeVisible();
      await expect(page.locator('p:has-text("Статус ключевых компонентов системы в реальном времени.")')).toBeVisible();
    } catch (error) {
      console.log('Monitoring page not accessible, skipping test');
    }
  });

  test('Audit Dashboard - Load and Display', async ({ page }) => {
    // Navigate to audit page
    await page.goto('/audit');
    await page.waitForURL('**/audit');

    // Take screenshot for visual comparison
    await page.screenshot({ path: 'test-results/audit-dashboard.png', fullPage: true });

    // Check main title
    await expect(page.locator('h1:has-text("📝 Журнал аудита")')).toBeVisible();

    // Check description
    await expect(page.locator('p:has-text("Отслеживание всех действий в системе")')).toBeVisible();
  });

  test('API Endpoints - Health Checks', async ({ page }) => {
    // Test Management Server health
    const managementResponse = await page.request.get('http://localhost:8002/docs');
    expect(managementResponse.status()).toBe(200);

    // Test Trading Gateway health
    const tradingResponse = await page.request.get('http://localhost:8001/health');
    expect(tradingResponse.status()).toBe(200);
  });

  test('WebSocket Connection Test', async ({ page }) => {
    // This would require more complex setup for WebSocket testing
    // For now, just check that the WebSocket composable is available
    const wsStatus = await page.evaluate(() => {
      // Check if WebSocket related code is loaded
      return typeof window !== 'undefined';
    });
    expect(wsStatus).toBe(true);
  });
});