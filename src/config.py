"""配置管理模块"""
import json
import os

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "api_key": "",
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "model": "deepseek-chat",
    "hotkey_start": "ctrl+shift+q",
    "hotkey_stop": "ctrl+shift+w",
    "fill_delay": 0.3,
}


def load_config():
    """加载配置文件，不存在则创建默认配置"""
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # 合并缺失的默认键
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
    return cfg


def save_config(cfg):
    """保存配置到文件"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


def get_api_key():
    """获取API密钥"""
    cfg = load_config()
    return cfg.get("api_key", "")


def set_api_key(key):
    """设置API密钥"""
    cfg = load_config()
    cfg["api_key"] = key
    save_config(cfg)