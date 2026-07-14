# WzlCli

独立的传奇资源命令行工程，当前已支持 WZL 读取、RGB565 像素解码、BMP 导出、无损写回和 Placement 修改。

## 当前能力

- WZL zlib 容器读取；
- WZL 帧、动作/方向候选和 Placement 读取；
- WZL → 16 位 RGB565 BMP；
- WZL 无损 round-trip 写回；
- 单帧和批量 Placement 修改；
- 默认密码策略：输入自动解密、输出自动加密，默认密码 `V8M2`；
- WIL/WIS/PAK 格式识别和转换接口骨架。

## 命令行

```cmd
WzlCli.exe info input.wzl
WzlCli.exe export input.wzl output --index 1
WzlCli.exe export input.wzl output --all
WzlCli.exe set-placement input.wzl output.wzl --index 2 --x 123 --y -456
WzlCli.exe set-placements input.wzl output.wzl placements.json
WzlCli.exe action-map input.wzl action-map.csv
```

## 开发测试

```cmd
set PYTHONPATH=src
python -m unittest discover -s tests -v
```

## 发布版

`dist/WzlCli.exe` 是 Nuitka 优化版，约 4 MB。它已经用真实 `cbohum4.wzl` 和参考编辑器导出的 BMP 做过像素级验证。

PAK/WIL/WIS 的具体转换编码需要参考编辑器生成的目标文件样本后接入，当前不会伪造不兼容的 PAK 文件。

Image import:

```cmd
WzlCli.exe import-images images output.wzl --output-wzx output.wzx
```

The importer accepts RGB565 BMP and PNG (PNG requires Pillow in source mode), writes zlib-compressed WZL frames, and can create a matching WZX index.

Append images to an existing resource and receive the new record numbers:

```cmd
WzlCli.exe append-images input.wzl images output.wzl --input-wzx input.wzx --output-wzx output.wzx --index-json new-indexes.json
```
