#!/usr/bin/env python3
import re
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright, Page
from login import login

# .env loading is handled by login module import


def get_balance(page: Page) -> dict:
    """
    마이페이지에서 예치금 잔액과 구매가능 금액을 조회합니다.
    
    Args:
        page: 로그인된 Playwright Page 객체
    
    Returns:
        dict: {
            'deposit_balance': int,  # 예치금 잔액 (원)
            'available_amount': int  # 구매가능 금액 (원)
        }
    """
    # Navigate to My Page
    # [수정] timeout을 0으로 해서 느려도 에러 안 나게 변경
    page.goto("https://www.dhlottery.co.kr/mypage/home", timeout=0, wait_until="domcontentloaded")
    
    # [수정] networkidle은 깃허브에서 자주 멈춤 -> 특정 요소가 뜰 때까지 기다리는 걸로 변경
    # page.wait_for_load_state("networkidle", timeout=30000) (삭제)
    
    # "예치금(#totalAmt)" 숫자가 화면에 보일 때까지 최대 10초 대기
    page.wait_for_selector("#totalAmt", state="visible", timeout=10000)
    
    # Get deposit balance (예치금 잔액)
    # Selector: #totalAmt (contains only number like "35,000")
    deposit_el = page.locator("#totalAmt")
    deposit_text = deposit_el.inner_text().strip()
    
    # Get available amount (구매가능)
    # Selector: #divCrntEntrsAmt (contains number with unit like "20,000원")
    available_el = page.locator("#divCrntEntrsAmt")
    available_text = available_el.inner_text().strip()
    
    # Parse amounts (remove non-digits)
    # 텍스트가 비어있을 경우 0으로 처리하는 방어 로직 살짝 추가 (int 에러 방지)
    deposit_str = re.sub(r'[^0-9]', '', deposit_text)
    available_str = re.sub(r'[^0-9]', '', available_text)
    
    deposit_balance = int(deposit_str) if deposit_str else 0
    available_amount = int(available_str) if available_str else 0
    
    return {
        'deposit_balance': deposit_balance,
        'available_amount': available_amount
    }


def run(playwright: Playwright) -> dict:
    """로그인 후 잔액 정보를 조회합니다."""
    # Create browser, context, and page
    # [수정] headless=True는 깃허브 기본값이니 유지
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    try:
        # Perform login
        login(page)
        
        # Get balance information
        balance_info = get_balance(page)
        
        # Print results in a clean format
        print(f"💰 예치금 잔액: {balance_info['deposit_balance']:,}원")
        print(f"🛒 구매가능: {balance_info['available_amount']:,}원")
        
        return balance_info
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
