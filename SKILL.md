---
name: ai-hotspot-publisher
description: AI热点自动发现生成文章和配图。使用GitHub+ Tavily采集AI热点，MiniMax2.7生成深度解读文章，阿里云wan2.7生成科技蓝色温暖风格配图（封面1024x1024+文中1024x1024），输出UTF8编码HTML格式到本地output/{日期+时间}目录，并将文章发布到公众号后台草稿箱。触发词：今日热点、生成文章、daily热点。
---

# AI 热点自动发布 Skill

每日自动发现 AI 热点，生成深度解读文章和配图，输出 UTF-8 编码 HTML 到本地目录，并将文章发布到公众号后台草稿箱。

## 功能

- 多源热点聚合（GitHub Trending + Tavily 搜索）
- MiniMax2.7 生成深度解读文章（标题 + 摘要 + 正文）
- 阿里云百炼 wan2.7 生成配图（封面 1024x1024 + 文中 1024x1024，科技蓝色温暖风格）
- 输出 HTML 格式文章到 output/{日期+时间}/ 目录
- 将 HTML 格式文章发布到公众号后台草稿箱，正文和标题采用 UTF-8 编码

## 工作流程

1. GitHub + Tavily 搜索 AI 热点，显示 Top 5 候选
2. 用户选择要写作的热点
3. MiniMax2.7 生成深度解读文章（Markdown 格式）
4. 阿里云 wan2.7 生成封面图和文中插图（科技蓝色温暖风格）
5. 保存 Markdown 到 output/{日期+时间}/article.md
6. 生成 HTML 到 output/{日期+时间}/article.html（UTF-8 编码）
7. 将 HTML 文章发布到微信公众号后台草稿箱
8. 提示用户去微信公众号后台检查文章

## 触发方式

在 Claude Code 中直接说：
- "今日热点"
- "生成文章"
- "daily热点"

## 前置配置

需要配置以下环境变量：

```bash
# MiniMax API Key (用于文章生成)
MINIMAX_API_KEY=eyJxxx

# 阿里云百炼 API Key (用于 wan2.7 配图)
ALIYUN_BAILIAN_API_KEY=sk-xxx
```

## 输出格式

- 字数：500 字以内
- 风格：综合模式（标题 + 摘要，新闻简报型 + 内容深度分析）
- 配图：封面图 1024x1024 + 文中插图 1024x1024，科技蓝色温暖风格
- 布局：摘要 → 文中插图 → 正文
- HTML：UTF-8 编码，可直接复制到微信编辑器使用
- 自动发布：将 HTML 格式文章发布到微信公众号草稿箱，正文和标题采用 UTF-8 编码
