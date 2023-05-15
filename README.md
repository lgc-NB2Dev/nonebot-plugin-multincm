<!-- markdownlint-disable MD031 MD033 MD036 MD041 -->

<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText">
</p>

# NoneBot-Plugin-MultiNCM

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
  <img src="https://img.shields.io/github/license/lgc-NB2Dev/nonebot-plugin-multincm.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-multincm">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-multincm.svg" alt="pypi">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-multincm">
  <img src="https://img.shields.io/pypi/dm/nonebot-plugin-multincm" alt="pypi download">
</a>

</div>

## 📖 介绍

一个网易云多选点歌插件，可以翻页，可以登录网易云账号点 vip 歌曲听（插件发送的是自定义音乐卡片），没了

### 歌曲列表效果图

![pic](https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/multincm/QQ图片20230515025601.jpg)

## 💿 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-multincm
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-multincm
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-multincm
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-multincm
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-multincm
```

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入

```toml
[tool.nonebot]
plugins = [
    # ...
    "nonebot_plugin_multincm"
]
```

</details>

## ⚙️ 配置

如果你安装了 [nonebot-plugin-ncm](https://github.com/kitUIN/nonebot-plugin-ncm)，本插件会与其共用同一个 Session，就可以不用填下面的账号密码了

下面配置中，手机号登录 和 邮箱登录、明文密码 和 MD5 密码哈希 各选其一填写即可

在 nonebot2 项目的 `.env` 文件中添加下表中的必填配置

|        配置项        | 必填 | 默认值 |                  说明                   |
| :------------------: | :--: | :----: | :-------------------------------------: |
|     `NCM_CTCODE`     |  否  |  `86`  |       手机号登录用，登录手机区号        |
|     `NCM_PHONE`      |  否  |   无   |        手机号登录用，登录手机号         |
|     `NCM_EMAIL`      |  否  |   无   |          邮箱登录用，登录邮箱           |
|    `NCM_PASSWORD`    |  否  |   无   |   帐号明文密码，邮箱登录时为邮箱密码    |
| `NCM_PASSWORD_HASH`  |  否  |   无   | 帐号密码 MD5 哈希，邮箱登录时为邮箱密码 |
|   `NCM_LIST_LIMIT`   |  否  |  `20`  |         歌曲列表每页的最大数量          |
|   `NCM_LIST_FONT`    |  否  |   无   |         渲染歌曲列表使用的字体          |
|  `NCM_MAX_NAME_LEN`  |  否  | `600`  | 歌曲列表中歌名列的最大文本宽度（像素）  |
| `NCM_MAX_ARTIST_LEN` |  否  | `400`  | 歌曲列表中歌手列的最大文本宽度（像素）  |

## 🎉 使用

### 指令

- 点歌 [歌曲名 / 音乐 ID]
  - 别名：`网易云`、`wyy`
- 解析 <回复 音乐卡片 / 链接>（获取该音乐的播放链接并使用自定义卡片发送）
  - 别名：`resolve`、`parse`、`get`
- 歌词 <回复 音乐卡片 / 链接>（获取该音乐的歌词）
  - 别名：`lrc`、`lyric`、`lyrics`
- 链接 <回复 音乐卡片 / 链接>（获取该音乐的网易云链接）
  - 别名：`link`

### Tip

- 点击 Bot 发送的音乐卡片可以跳转直链，可以直接下载该音乐

## 📞 联系

QQ：3076823485  
Telegram：[@lgc2333](https://t.me/lgc2333)  
吹水群：[1105946125](https://jq.qq.com/?_wv=1027&k=Z3n1MpEp)  
邮箱：<lgc2333@126.com>

## 💡 鸣谢

### [MeetWq/pil-utils](https://github.com/MeetWq/pil-utils)

超好用的 Pillow 辅助库

## 💰 赞助

感谢大家的赞助！你们的赞助将是我继续创作的动力！

- [爱发电](https://afdian.net/@lgc2333)
- <details>
    <summary>赞助二维码（点击展开）</summary>

  ![讨饭](https://raw.githubusercontent.com/lgc2333/ShigureBotMenu/master/src/imgs/sponsor.png)

  </details>

## 📝 更新日志

### 0.2.2

- 修复搜歌 `KeyError`

### 0.2.1

- 删除歌词尾部的空行与多余分割线

### 0.2.0

- 新增了三个指令 `解析`、`歌词`、`链接`
- 点歌指令支持直接输入音乐 ID
