<!-- markdownlint-disable MD031 MD033 MD036 MD041 -->

<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText">
</p>

# nonebot-plugin-example

_✨ NoneBot 插件简单描述 ✨_

<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<a href="https://pdm.fming.dev">
  <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm-managed">
</a>
<a href="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb">
  <img src="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb.svg" alt="wakatime">
</a>

<br />

<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/owner/nonebot-plugin-example.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-example">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-example.svg" alt="pypi">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-example">
  <img src="https://img.shields.io/pypi/dm/nonebot-plugin-example" alt="pypi download">
</a>

</div>

这是一个 nonebot2 插件项目的模板库, 你可以直接使用本模板创建你的 nonebot2 插件项目的仓库

模板库使用方法:

1. 点击仓库中的 `Use this template` 按钮, 输入仓库名与描述, 点击 `Create repository from template` 创建仓库
2. 全局替换 `owner` 为仓库所有者 ID;  
   全局替换 `nonebot-plugin-example` 为插件名;  
   全局替换 `nonebot_plugin_example` 为包名;  
   修改 python 徽标中的版本为你插件的运行所需版本;  
   替换 WakaTime 的徽标
3. 修改 `README.md` 中的插件名和插件描述, 并在下方填充相应的内容
4. 使用 `pdm` 安装工作区依赖
   ```shell
   pdm install
   pdm install --group dev
   ```

## 📖 介绍

这里是插件的详细介绍部分

## 💿 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-example
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-example
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-example
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-example
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-example
```

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入

```toml
[tool.nonebot]
plugins = [
    # ...
    "nonebot_plugin_example"
]
```

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

|  配置项  | 必填 | 默认值 |   说明   |
| :------: | :--: | :----: | :------: |
| 配置项 1 |  是  |   无   | 配置说明 |
| 配置项 2 |  否  |   无   | 配置说明 |

## 🎉 使用

### 指令表

|  指令  | 权限 | 需要@ | 范围 |   说明   |
| :----: | :--: | :---: | :--: | :------: |
| 指令 1 | 主人 |  否   | 私聊 | 指令说明 |
| 指令 2 | 群员 |  是   | 群聊 | 指令说明 |

### 效果图

如果有效果图的话

## 📞 联系

QQ：3076823485  
Telegram：[@lgc2333](https://t.me/lgc2333)  
吹水群：[1105946125](https://jq.qq.com/?_wv=1027&k=Z3n1MpEp)  
邮箱：<lgc2333@126.com>

## 💡 鸣谢

如果有要鸣谢的人的话

## 💰 赞助

感谢大家的赞助！你们的赞助将是我继续创作的动力！

- [爱发电](https://afdian.net/@lgc2333)
- <details>
    <summary>赞助二维码（点击展开）</summary>

  ![讨饭](https://raw.githubusercontent.com/lgc2333/ShigureBotMenu/master/src/imgs/sponsor.png)

  </details>

## 📝 更新日志

芝士刚刚发布的插件，还没有更新日志的说 qwq~
