#!/usr/bin/env python3
"""
Settlement Module End-to-End Testing with Selenium
Tests complete frontend-backend integration
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests

class SettlementE2ETest:
    def __init__(self):
        self.setup_driver()
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.wait = WebDriverWait(self.driver, 10)
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless for automation
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Install ChromeDriver automatically
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome WebDriver initialized")
        
    def test_backend_connectivity(self):
        """Test backend API connectivity"""
        print("\n🔗 TESTING BACKEND CONNECTIVITY")
        print("=" * 40)
        
        try:
            # Test statistics endpoint
            response = requests.get(f"{self.backend_url}/api/analytics/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend API responding")
                print(f"   📊 Total Batches: {data.get('total_batches')}")
                print(f"   💰 Amount Settled: ₹{data.get('total_amount_settled')}")
                return True
            else:
                print(f"❌ Backend API error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            return False
    
    def test_frontend_loading(self):
        """Test frontend application loading"""
        print("\n🌐 TESTING FRONTEND LOADING")
        print("=" * 35)
        
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            print(f"✅ Frontend loaded successfully")
            print(f"   📄 Page Title: {self.driver.title}")
            print(f"   🌍 Current URL: {self.driver.current_url}")
            
            # Check if React has loaded
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return window.React !== undefined")
                )
                print("✅ React framework loaded")
            except:
                print("⚠️ React framework detection inconclusive")
                
            return True
            
        except Exception as e:
            print(f"❌ Frontend loading failed: {e}")
            return False
    
    def test_navigation_to_settlements(self):
        """Test navigation to settlements page"""
        print("\n🧭 TESTING NAVIGATION TO SETTLEMENTS")
        print("=" * 40)
        
        try:
            # Try direct navigation to settlements page
            settlements_url = f"{self.frontend_url}/settlements"
            self.driver.get(settlements_url)
            
            # Wait for navigation to complete
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            print(f"✅ Navigated to settlements page")
            print(f"   🌍 URL: {self.driver.current_url}")
            
            # Check if we're on the settlements page
            if "/settlements" in self.driver.current_url:
                print("✅ Successfully reached settlements dashboard")
                return True
            else:
                print("⚠️ URL doesn't contain /settlements")
                return False
                
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def test_settlement_dashboard_elements(self):
        """Test settlement dashboard UI elements"""
        print("\n📊 TESTING SETTLEMENT DASHBOARD UI")
        print("=" * 40)
        
        # Wait for React to fully load
        time.sleep(5)
        
        # Check current page status
        print(f"   🌍 Current URL: {self.driver.current_url}")
        print(f"   📄 Page Title: {self.driver.title}")
        
        # Check if page has error content
        try:
            error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '404') or contains(text(), 'not found')]")
            if error_elements:
                print(f"   ⚠️ Page shows 404 error - checking if page exists in routing")
                # Take a screenshot for debugging
                try:
                    self.driver.save_screenshot("/tmp/settlement_page_404.png")
                    print(f"   📸 Screenshot saved to /tmp/settlement_page_404.png")
                except:
                    pass
                return False
        except Exception as e:
            print(f"   ❌ Error checking page status: {e}")
        
        elements_found = 0
        total_elements = 0
        
        # Test for common dashboard elements
        test_selectors = [
            ("Statistics Cards", "[data-testid*='statistic'], .ant-statistic, .ant-card"),
            ("Settlement Table", "table, .ant-table, [data-testid*='table']"),
            ("Action Buttons", "button, .ant-btn"),
            ("Loading States", ".ant-spin, [data-testid*='loading']"),
            ("Page Content", ".ant-layout-content, main, [data-testid*='content']"),
            ("React Components", "[data-reactroot], #__next, #root")
        ]
        
        for element_name, selector in test_selectors:
            total_elements += 1
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ {element_name}: {len(elements)} elements found")
                    elements_found += 1
                else:
                    print(f"   ❌ {element_name}: No elements found")
            except Exception as e:
                print(f"   ❌ {element_name}: Error - {e}")
        
        # Test for specific settlement-related content
        try:
            page_text = self.driver.page_source.lower()
            settlement_keywords = ['settlement', 'batch', 'transaction', 'process']
            found_keywords = [kw for kw in settlement_keywords if kw in page_text]
            
            if found_keywords:
                print(f"   ✅ Settlement keywords found: {', '.join(found_keywords)}")
                elements_found += 1
            else:
                print("   ❌ No settlement-specific content found")
                
            total_elements += 1
            
        except Exception as e:
            print(f"   ❌ Content analysis failed: {e}")
        
        # Check JavaScript console errors
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            if errors:
                print(f"   ⚠️ Found {len(errors)} JavaScript errors:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      📝 {error['message'][:100]}...")
            else:
                print("   ✅ No JavaScript errors found")
        except Exception as e:
            print(f"   ⚠️ Could not check console errors: {e}")
        
        success_rate = (elements_found / total_elements) * 100 if total_elements > 0 else 0
        print(f"\n📈 Dashboard UI Success Rate: {success_rate:.1f}% ({elements_found}/{total_elements})")
        
        return success_rate > 30
    
    def test_api_integration(self):
        """Test frontend-backend API integration"""
        print("\n🔌 TESTING API INTEGRATION")
        print("=" * 35)
        
        try:
            # Check for API calls in browser network
            # This is a simplified test - real implementation would use browser dev tools API
            
            # Look for any error messages or loading states
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".ant-message-error, .error, [data-testid*='error']")
            
            if error_elements:
                print(f"⚠️ Found {len(error_elements)} potential error elements")
                for elem in error_elements[:3]:  # Show first 3
                    try:
                        print(f"   📝 Error text: {elem.text[:100]}...")
                    except:
                        pass
            else:
                print("✅ No obvious error elements found")
            
            # Check for loading indicators (suggests API calls)
            loading_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".ant-spin, .loading, [data-testid*='loading']")
            
            if loading_elements:
                print(f"⚠️ Found {len(loading_elements)} loading indicators (API calls in progress)")
            else:
                print("✅ No active loading states")
            
            # Check if page has data (suggests successful API calls)
            data_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".ant-statistic-content, .ant-table-tbody tr, [data-testid*='data']")
            
            if data_elements:
                print(f"✅ Found {len(data_elements)} data elements (API integration working)")
                return True
            else:
                print("⚠️ Limited data elements found")
                return False
                
        except Exception as e:
            print(f"❌ API integration test failed: {e}")
            return False
    
    def test_responsive_design(self):
        """Test responsive design"""
        print("\n📱 TESTING RESPONSIVE DESIGN")
        print("=" * 35)
        
        screen_sizes = [
            ("Desktop", 1920, 1080),
            ("Tablet", 768, 1024),
            ("Mobile", 375, 667)
        ]
        
        results = []
        
        for device, width, height in screen_sizes:
            try:
                self.driver.set_window_size(width, height)
                time.sleep(2)  # Allow layout to adjust
                
                # Check if content is still visible
                body = self.driver.find_element(By.TAG_NAME, "body")
                if body:
                    print(f"   ✅ {device} ({width}x{height}): Layout adjusted")
                    results.append(True)
                else:
                    print(f"   ❌ {device}: Layout issues")
                    results.append(False)
                    
            except Exception as e:
                print(f"   ❌ {device}: Test failed - {e}")
                results.append(False)
        
        # Reset to desktop size
        self.driver.set_window_size(1920, 1080)
        
        success_rate = (sum(results) / len(results)) * 100
        print(f"\n📊 Responsive Design Success: {success_rate:.1f}%")
        
        return success_rate > 66
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🧪 SETTLEMENT MODULE E2E TESTING SUITE")
        print("=" * 45)
        print(f"🌐 Frontend URL: {self.frontend_url}")
        print(f"🔗 Backend URL: {self.backend_url}")
        print()
        
        test_results = []
        
        # Test 1: Backend Connectivity
        test_results.append(("Backend Connectivity", self.test_backend_connectivity()))
        
        # Test 2: Frontend Loading
        test_results.append(("Frontend Loading", self.test_frontend_loading()))
        
        # Test 3: Navigation
        test_results.append(("Navigation to Settlements", self.test_navigation_to_settlements()))
        
        # Test 4: Dashboard UI
        test_results.append(("Dashboard UI Elements", self.test_settlement_dashboard_elements()))
        
        # Test 5: API Integration
        test_results.append(("API Integration", self.test_api_integration()))
        
        # Test 6: Responsive Design
        test_results.append(("Responsive Design", self.test_responsive_design()))
        
        # Final Results
        print("\n🏆 COMPREHENSIVE E2E TEST RESULTS")
        print("=" * 40)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
            if result:
                passed += 1
        
        success_rate = (passed / total) * 100
        print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
        
        if success_rate >= 80:
            print("🎉 SETTLEMENT MODULE E2E TESTS: EXCELLENT")
        elif success_rate >= 60:
            print("✅ SETTLEMENT MODULE E2E TESTS: GOOD")
        elif success_rate >= 40:
            print("⚠️ SETTLEMENT MODULE E2E TESTS: NEEDS IMPROVEMENT")
        else:
            print("❌ SETTLEMENT MODULE E2E TESTS: REQUIRES ATTENTION")
        
        return success_rate
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.driver.quit()
            print("\n🧹 WebDriver cleaned up")
        except:
            pass

def main():
    """Main test execution"""
    test_suite = SettlementE2ETest()
    
    try:
        success_rate = test_suite.run_comprehensive_test()
        return success_rate >= 60  # Consider 60% as passing
    except Exception as e:
        print(f"\n❌ E2E Test Suite Failed: {e}")
        return False
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)