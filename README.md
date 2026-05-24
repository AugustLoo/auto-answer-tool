# Auto Answer Tool

一个桌面自动化答题工具，通过快捷键触发，自动识别屏幕上的题目（网页/Word/图片），调用 AI 推理生成答案，并模拟键鼠自动填写。

## ✨ 功能特性

- **一键触发**：全局快捷键 `Ctrl+Shift+Q` 启动
- **紧急停止**：`Ctrl+Shift+W` 随时中断
- **多源识别**：支持网页、Word 文档、图片截图
- **全题型覆盖**：单选题、多选题、判断题、填空题、简答题
- **智能推理**：基于 DeepSeek API 的 AI 分析
- **自动填写**：模拟键盘鼠标输入答案
- **无界面设计**：后台常驻，不干扰工作

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install keyboard mss pillow pyautogui pyperclip requests
```

### 2. 配置 API 密钥
```bash
python src/main.py --config
```
输入你的 [DeepSeek API Key](https://platform.deepseek.com/api_keys)

### 3. 运行自检
```bash
python src/main.py --test
```

### 4. 启动服务
```bash
python src/main.py
```
或双击 `run.bat`

## 📁 项目结构
```
auto-answer-tool/
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── config.py          # 配置管理
│   ├── capture.py         # 屏幕截图与内容捕获
│   ├── parser.py          # 题目解析与题型识别
│   ├── reasoning.py       # AI 推理（DeepSeek API）
│   ├── autofill.py        # 自动填写（键鼠模拟）
│   └── config.json        # 配置文件
├── run.bat                # Windows 启动脚本
├── README.md              # 说明文档
├── requirements.txt       # Python 依赖
└── .gitignore             # Git 忽略文件
```

## 🔧 工作原理

```
快捷键监听 (Ctrl+Shift+Q)
    ↓
内容捕获
├── 浏览器/Word → 全选复制 → 剪贴板文本
└── 图片/其他 → 截图 → OCR 识别
    ↓
题目解析
├── 切分题目
├── 识别题型（单选/多选/判断/填空/简答）
└── 提取选项
    ↓
AI 推理
└── 调用 DeepSeek API → 返回答案 JSON
    ↓
自动填写
├── 选择题 → 按字母键
├── 填空题 → 粘贴文本
├── 判断题 → 选择正确/错误
└── 简答题 → 粘贴答案
```

## ⚙️ 配置说明

编辑 `src/config.json`：
```json
{
    "api_key": "your-deepseek-api-key",
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "model": "deepseek-chat",
    "hotkey_start": "ctrl+shift+q",
    "hotkey_stop": "ctrl+shift+w",
    "fill_delay": 0.3
}
```

## 🎯 使用场景

- **在线考试/测评**：自动完成选择题、判断题
- **作业辅助**：快速填写 Word/PDF 作业
- **问卷调查**：自动填写网页问卷
- **学习刷题**：批量处理题库练习

## ⚠️ 注意事项

1. **API 费用**：使用 DeepSeek API 会产生费用，请关注用量
2. **准确率**：AI 推理可能出错，重要考试请人工核对
3. **防检测**：部分考试系统有防作弊机制，请谨慎使用
4. **快捷键冲突**：可修改配置避免与其他软件冲突

## 📝 开发计划

- [ ] 支持更多 OCR 引擎（PaddleOCR、EasyOCR）
- [ ] 添加本地 AI 模型支持（Qwen2.5、Phi-3）
- [ ] 支持更多文档格式（PDF、PPT、Excel）
- [ ] 图形化配置界面
- [ ] 答题历史记录与统计

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License