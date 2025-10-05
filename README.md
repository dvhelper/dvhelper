<img src="https://avatars.githubusercontent.com/u/235627946?s=400" alt="logo" width="140" height="140" align="right">

# DV Helper

<img src="https://img.shields.io/badge/Licence-MIT-green.svg?style=for-the-badge&&logo=github" />  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python" />  <img src="https://img.shields.io/badge/Windows-OS-red.svg?style=for-the-badge&logo=windows" />

**DV Helper** 是一款影片信息搜索和整理工具，能够从网站抓取影片信息，下载封面图片、剧照、预告片，生成标准的NFO文件，并按照演员分类整理影片文件。

## 主要功能
- 支持按影片编号搜索详细信息
- 批量处理文件夹中的视频文件
- 自动下载并裁剪封面图片
- 下载影片剧照和预告片
- 生成符合Kodi等媒体中心标准的NFO文件
- 按演员智能分类整理影片目录
- 支持登录功能以获取更多内容

## 系统要求
- Python 3.10 或更高版本
- Windows 操作系统
- 已安装 Chrome 浏览器（用于登录功能）
- 网络连接（用于搜索和下载信息）

## 使用说明

### 命令行参数

```
dvhelper [选项] 关键词或路径

选项:
  -h, --help            显示帮助信息并退出
  -v, --version         显示版本信息并退出
  -d DEPTH, --depth DEPTH
                        文件夹搜索深度（默认：0，表示仅搜索当前目录）
  -g, --gallery         下载影片的剧照和预告片
  -l, --login           忽略已保存的Cookie强制进行新的登录操作

参数:
  keywords_or_path      搜索关键词（如影片编号）或本地视频文件夹路径
                        可以使用逗号分隔多个关键词，或指定一个包含视频文件的文件夹路径进行批量处理
```

### 使用示例

**1. 搜索单个影片**

```bash
# 搜索编号为 ABCDE-123 的影片信息并在当前目录下生成整理好的影片目录
dvhelper ABCDE-123
```

**2. 搜索多个影片**

```bash
# 使用逗号分隔多个搜索关键词，批量搜索多个影片
dvhelper ABCDE-123,FGHIJ-456
```

**3. 批量处理文件夹中的视频**

```bash
# 扫描 D:\Movies 目录及其一级子目录中的视频文件并生成整理好的影片目录
dvhelper D:\Movies -d 1
```

**4. 强制重新登录**

```bash
# 强制重新登录，忽略已保存的 Cookie 并进行新的登录操作
dvhelper ABCDE-123 -l
```

**5. 下载剧照和预告片**

```bash
# 搜索编号为 ABCDE-123 的影片信息并下载剧照和预告片
dvhelper ABCDE-123 -g
```

**6. 组合使用选项**

```bash
# 扫描 D:\Movies 目录及其一级子目录中的视频文件，下载剧照和预告片，并强制重新登录
dvhelper D:\Movies -d 1 -g -l
```

## 影片目录结构说明

处理完成后，影片文件将按照以下结构组织：

```
#整理完成#/
├── 演员名称1/
│   └── [影片编号](发行年份)/
│       ├── 影片编号.mp4       # 影片文件
│       ├── 影片编号.nfo       # 影片元数据文件
│       ├── fanart.jpg         # 原始封面图片
│       ├── poster.jpg         # 裁剪后的海报图片
│       ├── gallery_01.jpg     # 剧照文件
│       ├── gallery_02.jpg     # 更多剧照文件
│       └── 影片编号_trailer.mp4 # 预告片文件
├── 演员名称2/
│   └── [影片编号](发行年份)/
│       └── ...
└── ==多演员==/               # 多演员影片的存放目录
    └── ...
```

## 二次开发说明

要进行二次开发，首先需要克隆项目文件到本地

```bash
git clone https://github.com/dvhelper/dvhelper.git
cd dvhelper
```

然后使用如下方法安装项目依赖项

### 使用 pip 安装依赖项（推荐）

```bash
pip install -e .
dvhelper --help
```

> 此方法的优点是简单快捷，无需配置环境变量，可在任何位置直接使用`dvhelper`命令，但是会将依赖项安装到全局 Python 环境中。

### 使用 Poetry 安装依赖项

```bash
poetry install
poetry run dvhelper --help
```

> 此方法的优点是仅在当前环境中安装项目及其依赖，而不会影响全局 Python 环境，缺点是只能在项目目录下使用`dvhelper`命令。

### 编辑更新多语言文件

DV-Helper支持多语言国际化，使用gettext和Babel工具进行翻译管理。项目目前支持英文翻译，翻译文件位于`i18n`目录下。

> 要切换测试其它语言（英语），在命令行后增加`--lang`参数即可。

#### 翻译文件类型

- `.pot`文件：Portable Object Template，包含需要翻译的字符串模板文件
- `.po`文件：Portable Object，包含已翻译的字符串文件
- `.mo`文件：Machine Object，编译后的二进制翻译文件，供程序运行时使用

#### 更新翻译文件

项目提供了`i18n/make.bat`批处理文件来管理翻译流程：

1. 更新pot文件和po文件
   ```bash
   # 在项目根目录下执行
   call i18n\make.bat 1
   ```
   此命令会：
   - 从源代码中提取所有需要翻译的字符串，更新`i18n/dvhelper.pot`文件
   - 使用新的pot文件更新现有的英文po文件`i18n/en_US/LC_MESSAGES/dvhelper.po`

2. 初始化新的翻译
   ```bash
   # 在项目根目录下执行
   call i18n\make.bat 2
   ```
   此命令会：
   - 提取字符串并创建pot文件
   - 基于pot文件初始化新的po文件（如果不存在）

3. 编译mo文件
   ```bash
   # 在项目根目录下执行
   call i18n\make.bat 3
   ```
   此命令会：
   - 将po文件编译成二进制的mo文件
   - 编译后的mo文件位于`i18n/en_US/LC_MESSAGES/dvhelper.mo`

#### 编辑翻译文件

- 要编辑翻译，您需要修改`i18n/en_US/LC_MESSAGES/dvhelper.po`文件
- 可以使用任何文本编辑器或专门的PO文件编辑器（如Poedit）进行编辑
- 编辑完成后，需要执行编译命令生成mo文件，程序才能使用新的翻译

## 工作原理

1. **初始化阶段**：程序启动后会检查是否存在有效的 Cookies 文件，如果不存在则使用匿名会话。
2. **输入处理**：解析用户提供的关键词或文件夹路径。
3. **信息抓取**：连接到指定网站搜索影片信息，包括标题、演员、发行日期等。
4. **资源下载**：下载影片封面图片并进行裁剪处理。如果启用了`-g`选项，还会下载剧照和预告片。
   - 剧照会以`gallery_01.jpg`、`gallery_02.jpg`等格式保存
   - 预告片会以`影片编号_trailer.扩展名`格式保存，自动从 URL 中提取合适的扩展名
5. **文件生成**：创建标准的 NFO 文件，包含影片的完整元数据。
6. **文件整理**：按照演员名称分类创建目录，并将影片文件移动到相应目录。

## 注意事项

1. **Cookie管理**：程序会在首次登录后保存Cookie到本地，以便后续使用。Cookie文件位于程序同级目录下的`cookies.json`。
2. **登录操作**：使用`-l`参数强制重新登录时，程序会打开Chrome浏览器，用户需要手动完成登录操作。
3. **影片命名**：为了提高识别率，请确保影片文件名包含正确的影片编号。
4. **支持的格式**：程序支持多种常见视频格式，包括但不限于MP4、MKV、AVI、WMV等。
5. **性能提示**：批量处理大量视频文件时，建议适当设置搜索深度，避免处理过多无关文件。
6. **剧照和预告片下载**：使用`-g`选项时，程序会尝试下载剧照和预告片，请注意这可能会增加处理时间和网络流量。预告片格式会自动从URL中提取，支持多种常见视频格式。

## 常见问题

**Q: 为什么有些影片无法找到？**
A: 可能的原因包括：影片编号格式不正确、影片太新或太旧、网络连接问题等。请检查影片编号并重试。

**Q: 为什么需要登录？**
A: 登录后可以访问更多影片信息，特别是一些需要权限的内容。

**Q: 支持哪些影片编号格式？**
A: 支持常规格式（如ABCDE-123）、FC2格式（如FC2-123456）和特定厂商格式。

## 许可证
本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件

## 免责声明
本工具仅用于个人学习和研究目的，用户应遵守相关法律法规，不得将其用于任何违法或侵犯他人权益的活动。
