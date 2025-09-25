# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个用于监控 Apple Store 线下直营店货源情况的 Python 项目。基于 iPhone-Pickup-Monitor 项目的灵感开发，主要功能包括多货源同时监控和多种消息通知（钉钉、Telegram、Bark）。

## 核心架构

### 主要文件结构
- `monitor.py` - 主程序文件，包含 `AppleStoreMonitor` 类和 `Utils` 工具类
- `products.json` - 产品信息数据库，包含 Apple Watch、AirPods、iPhone 等产品的型号和 SKU 信息
- `apple_store_monitor_configs.json` - 运行时配置文件，存储监控产品、地区、通知设置等
- `requirements.txt` - Python 依赖包（仅包含 requests==2.26.0）

### 核心组件

#### AppleStoreMonitor 类
- `config()` - 静态方法，用于交互式配置监控产品、地区和通知设置
- `start()` - 实例方法，启动监控循环，定期扫描 Apple Store API
- 使用 Apple 官方 API：`https://www.apple.com.cn/shop/fulfillment-messages`

#### Utils 类
- `send_message()` - 统一消息发送接口，支持多种通知方式
- `send_dingtalk_message()` - 钉钉群机器人通知
- `send_telegram_message()` - Telegram Bot 通知
- `send_bark_message()` - Bark 推送通知（iOS）

## 常用命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置监控
```bash
python monitor.py config
```
此命令启动交互式配置，包括：
- 选择监控产品（从 products.json 中选择）
- 选择监控地区（通过 Apple API 动态获取）
- 排除特定直营店
- 配置通知方式（钉钉/Telegram/Bark）
- 设置扫描间隔和异常通知

### 启动监控
```bash
# 前台启动
python monitor.py start

# 后台启动（推荐用于服务器部署）
nohup python -u monitor.py start > monitor.log 2>&1 &
```

## 配置文件说明

### products.json 结构
三层嵌套结构：`产品类别 -> 产品系列 -> SKU 代码: 产品描述`
- 添加新产品时需要获取正确的 Apple SKU 代码
- 支持 Apple Watch、AirPods、iPhone 等产品线

### apple_store_monitor_configs.json 结构
- `selected_products` - 监控的产品 SKU 列表
- `selected_area` - 监控地区（省市区格式）
- `exclude_stores` - 排除的直营店 ID 列表
- `notification_configs` - 各种通知方式的配置
- `scan_interval` - 扫描间隔（秒）
- `alert_exception` - 是否在异常时发送通知

## 开发注意事项

### API 限制和最佳实践
- 使用随机化扫描间隔（scan_interval/2 到 scan_interval*2）避免被限流
- 异常通知仅在 6:00-23:00 时间段发送
- 每小时发送一次心跳通知确认程序正常运行

### 通知机制
程序会在以下情况发送通知：
1. 启动时 - 确认配置信息
2. 检测到有货 - 主要功能
3. 整点心跳 - 确认程序运行状态
4. 程序异常 - 可选的异常告警

### 扩展开发
- 添加新产品：更新 `products.json` 文件
- 添加新通知方式：在 `Utils` 类中添加对应的 `send_xxx_message()` 方法
- 修改监控逻辑：主要在 `AppleStoreMonitor.start()` 方法中