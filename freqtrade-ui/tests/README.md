# Playwright E2E Testing

This directory contains end-to-end tests for the Freqtrade Multi-Bot System dashboards using Playwright.

## Test Structure

### Dashboard Tests (`tests/dashboard.spec.ts`)
- **Home Dashboard**: Main overview page with statistics and quick actions
- **Bot Management**: Bot creation, control, and monitoring
- **Strategies**: Strategy management and backtesting
- **Analytics**: Performance metrics and trading analysis
- **FreqAI Lab**: Machine learning models and predictions
- **Data Management**: Historical data import/export
- **Hyperopt**: Parameter optimization
- **Monitoring**: System component status
- **Audit**: Action logging and tracking

### Visual Testing
- Screenshots are automatically captured for each dashboard
- Baseline screenshots stored in `test-results/baseline/`
- Visual regression testing can be enabled by comparing screenshots

## Running Tests

### Local Development
```bash
# Install dependencies
cd freqtrade-ui
npm install

# Install Playwright browsers
npx playwright install

# Run all tests
npx playwright test

# Run specific test
npx playwright test --grep "Home Dashboard"

# Run in headed mode (visible browser)
npx playwright test --headed

# Generate HTML report
npx playwright show-report
```

### CI/CD Integration
Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

The CI/CD pipeline includes:
1. **Lint and Format**: Code quality checks
2. **Unit Tests**: Backend unit tests
3. **Integration Tests**: API integration tests
4. **Performance Tests**: Load and performance validation
5. **E2E Tests**: Playwright browser tests
6. **Docker Build**: Container image creation
7. **Security Scan**: Vulnerability scanning
8. **Deployment**: Staging/Production deployment

## Test Configuration

### Playwright Config (`playwright.config.ts`)
- **Browser**: Chromium (headless by default)
- **Timeout**: 60 seconds per test
- **Viewport**: 1280x720
- **Base URL**: http://localhost:5176

### Test Setup
- Automatic login with test credentials
- Service startup verification
- Screenshot capture for visual testing
- API health checks

## Visual Regression Testing

### Setup Baseline Screenshots
```bash
# Run tests to generate baseline screenshots
npx playwright test

# Move screenshots to baseline directory
mkdir -p test-results/baseline
cp test-results/*.png test-results/baseline/
```

### Compare Screenshots
```bash
# Use pixelmatch or similar tool for visual comparison
# Example implementation in test:
await expect(page).toHaveScreenshot('dashboard.png');
```

## Debugging Tests

### Common Issues
1. **Timeout errors**: Increase timeout in `playwright.config.ts`
2. **Element not found**: Check selectors match actual DOM
3. **API failures**: Ensure backend services are running
4. **Screenshot differences**: Update baseline images

### Debug Mode
```bash
# Run with debug flags
DEBUG=pw:api npx playwright test --debug

# Use Playwright Inspector
npx playwright test --headed --debug
```

## Test Results

### Local Results
- Test results stored in `test-results/`
- HTML report: `playwright-report/index.html`
- Screenshots: `test-results/*.png`

### CI/CD Results
- Test artifacts uploaded to GitHub Actions
- HTML reports available in workflow runs
- Screenshots attached to failed tests

## Best Practices

1. **Selector Strategy**: Use data attributes or semantic selectors
2. **Wait Strategies**: Prefer `waitFor` over fixed `sleep`
3. **Test Isolation**: Each test should be independent
4. **Visual Testing**: Capture screenshots for UI validation
5. **API Mocking**: Use for external dependencies when needed

## Maintenance

- Update test selectors when UI changes
- Refresh baseline screenshots after UI updates
- Add new tests for new features
- Monitor test flakiness and fix unstable tests</content>
<parameter name="filePath">jules_freqtrade_project/freqtrade-ui/tests/README.md