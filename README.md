# 公众号 AI 写作助手

一个基于 Claude API 的微信公众号全流程写作辅助工具，支持选题、大纲、正文、润色、标题一站式生成。

## 功能特色

- ① 账号设置 — 定位、读者画像、写作风格
- ② 选题灵感 — 一键生成 8 个选题
- ③ 文章大纲 — 结构化大纲含钩子设计
- ④ 正文撰写 — 基于大纲生成完整初稿
- ⑤ 润色优化 — 多维度润色目标
- ⑥ 爆款标题 — 一次生成 10 个标题

## 部署到 Vercel（推荐，免费）

### 前提条件
- [Vercel 账号](https://vercel.com)（免费注册）
- [Anthropic API Key](https://console.anthropic.com)

### 步骤一：上传项目

**方式 A：GitHub 部署（推荐）**
1. 在 GitHub 创建新仓库，上传本项目所有文件
2. 在 Vercel 控制台点击 "Add New Project"
3. 选择刚创建的 GitHub 仓库，点击 "Deploy"

**方式 B：Vercel CLI 部署**
```bash
npm install -g vercel
cd wechat-writer
vercel deploy
```

### 步骤二：配置 API Key

部署完成后，进入 Vercel 项目设置：
1. 打开 **Settings → Environment Variables**
2. 添加以下变量：
   - Name: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-xxxxxx`（你的 API Key）
3. 点击 Save，然后在 **Deployments** 里重新部署一次

### 步骤三：访问

Vercel 会提供一个 `xxx.vercel.app` 域名，直接访问即可。
也可以在 Settings → Domains 绑定自己的域名。

---

## 本地运行

安装 Python 3.8+，然后：

```bash
# 设置 API Key
export ANTHROPIC_API_KEY=sk-ant-xxxxxx

# 启动本地服务器
python3 -m http.server 3000 --directory public
```

> 注意：本地运行时，`/api/chat` 后端不会启动，AI 功能无法使用。
> 如需本地完整测试，推荐直接运行 `vercel dev`（需要安装 Vercel CLI）。

---

## 项目结构

```
wechat-writer/
├── api/
│   └── chat.py          # Python 后端（Vercel Serverless Function）
├── public/
│   └── index.html       # 前端页面
├── vercel.json          # Vercel 部署配置
├── requirements.txt     # Python 依赖（标准库，无需安装）
└── README.md
```

## 安全说明

- API Key 存储在 Vercel 环境变量中，不会暴露给前端
- 后端代理锁定了模型为 `claude-sonnet-4-20250514`，防止被恶意调用
- 如需进一步限制访问，可在 `api/chat.py` 中添加 IP 白名单或简单鉴权

## 常见问题

**Q: 部署后 AI 不响应？**
A: 检查 Vercel 环境变量中 `ANTHROPIC_API_KEY` 是否正确设置，并确保重新部署了一次。

**Q: 如何限制只有自己能用？**
A: 在 `api/chat.py` 顶部添加：
```python
SECRET = os.environ.get("ACCESS_SECRET", "")
# 然后在 do_POST 中验证请求头中的 token
```

**Q: 支持流式输出吗？**
A: 当前版本不支持，等待完整响应后显示。如需流式输出需要修改后端为 SSE。
