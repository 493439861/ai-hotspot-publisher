# AI 热点自动发布系统

自动发现 AI 热点，生成深度解读文章和配图，输出 UTF-8 编码 HTML 到本地目录，并自动发布到微信公众号草稿箱。

## 功能

- **多源热点聚合**: GitHub Trending + arXiv + Tavily 搜索（各 2/4/4 条，共 10 条）
- **内容生成**: MiniMax2.7 生成深度解读文章
- **配图生成**: 阿里云百炼 wan2.7 生成科技蓝色温暖风格配图（封面 1024x1024 + 文中 1024x1024）
- **HTML 输出**: UTF-8 编码，可直接复制到微信编辑器
- **自动发布**: 自动创建微信图文草稿箱

## 目录结构

```
ai-hotspot-publisher/
├── SKILL.md                 # Skill 定义
├── README.md                # 本文档
├── .gitignore               # Git 忽略配置
├── .env.example             # 环境变量模板
├── requirements.txt         # 依赖
├── src/
│   ├── __init__.py
│   ├── main.py              # 主入口
│   ├── config.py            # 配置管理
│   ├── hotspot_finder.py    # 热点发现 (GitHub + arXiv + Tavily)
│   ├── content_generator.py # 内容生成 (MiniMax2.7)
│   ├── image_generator.py   # 配图生成 (阿里云 wan2.7)
│   ├── html_generator.py    # HTML 生成
│   └── wechat_publisher.py  # 微信公众号发布
└── output/                  # 输出目录（运行后生成）
    └── {日期+时间}/
        ├── article.html     # HTML 格式文章 (UTF-8)
        ├── article.md       # Markdown 格式文章
        ├── cover.png        # 封面图 1024x1024
        └── article.png      # 文中插图 1024x1024
```

## 工作流程

1. **GitHub + arXiv + Tavily** → 显示 Top 10 热点候选
2. **用户选择** → 输入数字 1-10 选择热点
3. **MiniMax2.7 生成文章** → 深度解读
4. **wan2.7 生成配图** → 封面 1024x1024 + 文中 1024x1024（科技蓝色温暖风格）
5. **保存 Markdown** → output/{日期+时间}/article.md
6. **生成 HTML** → output/{日期+时间}/article.html（UTF-8 编码）
7. **创建微信草稿** → 自动发布到公众号草稿箱

## 使用方法

### 1. 配置环境变量

```bash
cd skills/ai-hotspot-publisher
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行

```bash
# 默认自动创建微信草稿
python src/main.py

# 禁用自动发布到微信
python src/main.py --no-publish
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| MINIMAX_API_KEY | 是 | MiniMax API Key（文章生成） |
| ALIYUN_BAILIAN_API_KEY | 是 | 阿里云百炼 API Key（配图生成） |
| TAVILY_API_KEY | 否 | Tavily API Key（热点搜索补充） |
| WEIXIN_APP_ID | 否 | 微信公众号 AppID（自动发布） |
| WEIXIN_APP_SECRET | 否 | 微信公众号 AppSecret（自动发布） |

## API Key 获取

| 服务 | 获取地址 |
|------|----------|
| MiniMax | https://platform.minimaxi.com/ |
| 阿里云百炼 | https://bailian.console.aliyun.com/ |
| Tavily | https://tavily.com/ |
| 微信公众平台 | https://mp.weixin.qq.com/ |

## Claude Code 指令

在 Claude Code 中直接说以下指令即可触发：

- `今日热点` - 搜索并生成文章
- `生成文章` - 搜索并生成文章
- `daily热点` - 搜索并生成文章

Claude Code 会自动执行完整流程：搜索热点 → 选择话题 → 生成文章 → 生成配图 → 发布到微信公众号草稿箱。
