<!-- markdownlint-disable MD031 MD033 MD036 MD041 -->

<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText">
</p>

# NoneBot-Plugin-MultiNCM

_✨ 网易云多选点歌 ✨_

<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
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

一个网易云多选点歌插件（也可以设置成单选，看下面），可以翻页，可以登录网易云账号点 vip 歌曲听（插件发送的是自定义音乐卡片），没了

插件获取的是音乐播放链接，不会消耗会员每月下载次数

### 效果图

<details>
<summary>歌曲列表效果图（点击展开）</summary>

![pic](https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/multincm/QQ图片20230515025601.jpg)

</details>

<details>
<summary>电台列表效果图（点击展开）</summary>

![pic](https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/multincm/QQ图片20230519034438.jpg)

</details>

<details>
<summary>歌词效果图（点击展开）</summary>

![pic](https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/multincm/QQ图片20230519034757.png)

</details>

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

|           配置项            | 必填 |      默认值       |                                                   说明                                                    |
| :-------------------------: | :--: | :---------------: | :-------------------------------------------------------------------------------------------------------: |
|        **登录相关**         |      |                   |                                                                                                           |
|        `NCM_CTCODE`         |  否  |       `86`        |                                        手机号登录用，登录手机区号                                         |
|         `NCM_PHONE`         |  否  |        无         |                                         手机号登录用，登录手机号                                          |
|         `NCM_EMAIL`         |  否  |        无         |                                           邮箱登录用，登录邮箱                                            |
|       `NCM_PASSWORD`        |  否  |        无         |                                    帐号明文密码，邮箱登录时为邮箱密码                                     |
|     `NCM_PASSWORD_HASH`     |  否  |        无         |                                  帐号密码 MD5 哈希，邮箱登录时为邮箱密码                                  |
|        **展示相关**         |      |                   |                                                                                                           |
|      `NCM_LIST_LIMIT`       |  否  |       `20`        |                                          歌曲列表每页的最大数量                                           |
|       `NCM_LIST_FONT`       |  否  |        无         |                                          渲染歌曲列表使用的字体                                           |
|     `NCM_MAX_NAME_LEN`      |  否  |       `600`       |                                  歌曲列表中歌名列的最大文本宽度（像素）                                   |
|    `NCM_MAX_ARTIST_LEN`     |  否  |       `400`       |                                  歌曲列表中歌手列的最大文本宽度（像素）                                   |
|    `NCM_LRC_EMPTY_LINE`     |  否  |    `--------`     |                                            填充歌词空行的字符                                             |
|        **功能相关**         |      |                   |                                                                                                           |
|    `NCM_MSG_CACHE_TIME`     |  否  |      `43200`      |                                    缓存 用户最近一次操作 的时长（秒）                                     |
|     `NCM_AUTO_RESOLVE`      |  否  |      `False`      |                             当用户发送音乐链接时，是否自动解析并发送音乐卡片                              |
| `NCM_RESOLVE_PLAYABLE_CARD` |  否  |      `False`      |                                   开启自动解析时，是否解析可播放的卡片                                    |
|  `NCM_ILLEGAL_CMD_FINISH`   |  否  |      `False`      |                              当用户在点歌时输入了非法指令，是否直接退出点歌                               |
|   `NCM_ILLEGAL_CMD_LIMIT`   |  否  |        `3`        | 当未启用 `NCM_ILLEGAL_CMD_FINISH` 时，用户在点歌时输入了多少次非法指令后直接退出点歌，填 `0` 以禁用此功能 |
|    `NCM_USE_PLAYWRIGHT`     |  否  |      `False`      |                               是否使用 `playwright` 绘制歌曲列表与歌词图片                                |
|    `NCM_DELETE_LIST_MSG`    |  否  |      `True`       |                                   是否在退出点歌模式后自动撤回歌曲列表                                    |
| `NCM_DELETE_LIST_MSG_DELAY` |  否  |   `[0.5, 2.0]`    |                                  自动撤回歌曲列表消息间隔时间（单位秒）                                   |
|  `NCM_UPLOAD_FOLDER_NAME`   |  否  |    `MultiNCM`     |         在群内使用上传指令时，上传到的文件夹名称，不存在时会自动创建，如果创建失败会上传到根目录          |
|     `NCM_ENABLE_RECORD`     |  否  |      `False`      |                                        是否开启发送歌曲语音的功能                                         |

## 🎉 使用

### 指令

#### 搜索指令

- 点歌 [歌曲名 / 音乐 ID]
  - 介绍：搜索歌曲。当输入音乐 ID 时会直接发送对应音乐
  - 别名：`网易云`、`wyy`
- 电台 [歌曲名 / 节目 ID]
  - 介绍：搜索电台节目。当输入电台 ID 时会直接发送对应节目
  - 别名：`声音`、`网易电台`、`wydt`、`wydj`

#### 操作指令

- 解析 [回复 音乐卡片 / 链接]
  - 介绍：获取该音乐的播放链接并使用自定义卡片发送
  - 别名：`resolve`、`parse`、`get`
- 直链 [回复 音乐卡片 / 链接]
  - 介绍：获取该音乐的下载链接
  - 别名：`direct`
- 上传 [回复 音乐卡片 / 链接]
  - 介绍：下载该音乐并上传到群文件
  - 别名：`upload`
- 歌词 [回复 音乐卡片 / 链接]
  - 介绍：获取该音乐的歌词，以图片形式发送
  - 别名：`lrc`、`lyric`、`lyrics`
- 发送语音 [回复 音乐卡片 / 链接]
  - 介绍：发送该音乐的声音
  - 别名：`record`

### Tip

- 当启用 `NCM_AUTO_RESOLVE` 时，Bot 会自动解析你发送的网易云歌曲或电台节目链接
- 点击 Bot 发送的音乐卡片会跳转到官网歌曲页
- 使用需要回复音乐卡片的指令时，如果没有回复，会自动使用你触发发送的最近一个音乐卡片的信息

## 🤔 Q & A

### Q: 我可以把插件变成单选点歌吗？

A: 可以，把配置项 `NCM_LIST_LIMIT` 设置为 `1` 即可。因为插件在检测到搜索结果仅有一个时，会将它直接发送出来。我们在这里利用了这个特性。

## 📞 联系

QQ：3076823485  
Telegram：[@lgc2333](https://t.me/lgc2333)  
吹水群：[1105946125](https://jq.qq.com/?_wv=1027&k=Z3n1MpEp)  
邮箱：<lgc2333@126.com>

## 💡 鸣谢

### [mos9527/pyncm](https://github.com/mos9527/pyncm)

项目使用的网易云 API 调用库

### [Binaryify/NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi)

项目电台相关 API 来源

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

### 0.5.0（开发中）

- 支持歌单，专辑等（开发中）
- 点歌指令可以回复一条文本消息作为搜索内容了
- 支持使用语音发送歌曲
- resolve [#14](https://github.com/lgc-NB2Dev/nonebot-plugin-multincm/issues/14)
- 重构部分代码

### 0.4.4

- 添加配置项 `NCM_ILLEGAL_CMD_LIMIT`

### 0.4.3

- 可以退出搜索模式了

### 0.4.2

- resolve [#13](https://github.com/lgc-NB2Dev/nonebot-plugin-multincm/issues/13)

### 0.4.1

- 支持了 `163cn.tv` 短链（Thanks to [@XieXiLin2](https://github.com/XieXiLin2)）
- 修复当 `NCM_RESOLVE_PLAYABLE_CARD` 为 `False` 时，Bot 依然会回复的问题
- 部分代码优化

### 0.4.0

- 项目部分重构
- 删除 `链接` 指令，新增 `直链`、`上传` 指令
- 将卡片点击后跳转的地址改为官网歌曲页，代替 `链接` 指令，同时删除了发送过音乐卡片的缓存机制
- 添加配置项 `NCM_RESOLVE_PLAYABLE_CARD`、`NCM_UPLOAD_FOLDER_NAME`

### 0.3.9

- 让 `htmlrender` 成为真正的可选依赖
- 把配置项 `NCM_MSG_CACHE_TIME` 的默认值改为 `43200`（12 小时）

### 0.3.8

- 修改及统一表格背景色

### 0.3.7

- 添加配置项 `NCM_DELETE_LIST_MSG` 和 `NCM_DELETE_LIST_MSG_DELAY`（[#5](https://github.com/lgc-NB2Dev/nonebot-plugin-multincm/issues/5)）

### 0.3.6

- 支持使用 `nonebot-plugin-htmlrender` (`playwright`) 渲染歌曲列表与歌词图片（默认不启用，如要启用需要自行安装 `nonebot-plugin-multincm[playwright]`）
- 添加配置项 `NCM_USE_PLAYWRIGHT` 与 `NCM_LRC_EMPTY_LINE`

### 0.3.5

- 🎉 NoneBot 2.0 🚀

### 0.3.4

- 修复分割线下会显示歌词翻译的问题

### 0.3.3

- 新增配置项 `NCM_ILLEGAL_CMD_FINISH`
- 在未启用 `NCM_ILLEGAL_CMD_FINISH` 时输入错误指令将会提示用户退出点歌

### 0.3.2

- 新增配置项 `NCM_MSG_CACHE_TIME`、`NCM_AUTO_RESOLVE`
- 调整登录流程到 `driver.on_startup` 中

### 0.3.1

- 修复电台相关 bug

### 0.3.0

- 支持电台节目的解析与点播

### 0.2.5

- `解析`、`歌词`、`链接` 指令可以直接根据 Bot 发送的上个音乐卡片作出回应了
- 歌词解析会合并多行空行和去掉首尾空行了
- 现在插件会定时清理自身内存中的缓存了

### 0.2.4

- 修复一个歌词解析 bug

### 0.2.3

- 微调歌曲列表排版
- 微调插件帮助文本

### 0.2.2

- 修复搜歌 `KeyError`

### 0.2.1

- 删除歌词尾部的空行与多余分割线

### 0.2.0

- 新增了三个指令 `解析`、`歌词`、`链接`
- 点歌指令支持直接输入音乐 ID
