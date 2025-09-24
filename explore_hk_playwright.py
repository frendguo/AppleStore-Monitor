#!/usr/bin/env python3
# -*- coding: UTF-8 –*-
"""
使用Playwright探索香港Apple Store的API
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def explore_hk_apple_store():
    """使用Playwright探索香港Apple Store"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 显示浏览器
        page = await browser.new_page()
        
        # 监听网络请求
        requests = []
        
        def handle_request(request):
            if 'shop' in request.url and ('fulfillment' in request.url or 'pickup' in request.url or 'availability' in request.url):
                requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                })
                print(f"捕获API请求: {request.url}")
        
        def handle_response(response):
            if 'shop' in response.url and ('fulfillment' in response.url or 'pickup' in response.url or 'availability' in response.url):
                print(f"API响应: {response.url} - 状态码: {response.status}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            print("访问香港Apple Store...")
            await page.goto('https://www.apple.com/hk/', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            print("尝试访问iPhone页面...")
            await page.goto('https://www.apple.com/hk/iphone/', wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            print("尝试访问购买页面...")
            # 查找购买链接
            try:
                buy_links = await page.query_selector_all('a[href*="buy"]')
                if buy_links:
                    print(f"找到 {len(buy_links)} 个购买链接")
                    # 点击第一个购买链接
                    await buy_links[0].click()
                    await page.wait_for_timeout(5000)
                else:
                    # 尝试直接访问购买页面
                    await page.goto('https://www.apple.com/hk/shop/buy-iphone/', wait_until='networkidle')
                    await page.wait_for_timeout(5000)
            except Exception as e:
                print(f"访问购买页面时出错: {e}")
                # 尝试直接访问
                await page.goto('https://www.apple.com/hk/shop/buy-iphone/', wait_until='networkidle')
                await page.wait_for_timeout(5000)
            
            print(f"\\n捕获到的API请求 ({len(requests)} 个):")
            for i, req in enumerate(requests):
                print(f"\\n请求 {i+1}:")
                print(f"  URL: {req['url']}")
                print(f"  方法: {req['method']}")
                print(f"  关键请求头:")
                for key, value in req['headers'].items():
                    if key.lower() in ['referer', 'user-agent', 'accept']:
                        print(f"    {key}: {value}")
                if req['post_data']:
                    print(f"  POST数据: {req['post_data']}")
            
            # 等待用户操作
            print("\\n浏览器将保持打开状态30秒，您可以手动操作来触发更多API请求...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"探索过程中出错: {e}")
        
        finally:
            await browser.close()
            
        return requests

if __name__ == '__main__':
    asyncio.run(explore_hk_apple_store())
