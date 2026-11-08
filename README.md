# LPG-DRL 论文主页

英文静态论文主页，页面内容来自 `paper_TAI/LPG-DRL.tex`。设计参考 [ControlScene](https://winkquan.github.io/ControlScene-Page/) 和 [Academic Project Page Template](https://github.com/eliahuhorwitz/Academic-project-page-template)。

页面包含作者与机构、摘要、方法框架、三种场景的轨迹与完整数据表、训练曲线、消融实验和临时 BibTeX。支持手机布局、键盘操作、图片放大、引用复制。关闭 JavaScript 时，正文、全部场景和数据表仍可阅读。

## 本地预览

无需 Node.js、npm 或构建流程。在本目录运行：

```bash
python3 -m http.server 4173 --bind 127.0.0.1
```

浏览器访问 <http://127.0.0.1:4173>。也可直接打开 `index.html`；引用复制取决于浏览器对本地文件的权限。

## 修改内容

| 文件 | 用途 |
| --- | --- |
| `index.html` | 论文标题、作者、摘要、方法说明、BibTeX 等正文 |
| `assets/css/site.css` | 布局、配色与响应式样式 |
| `assets/js/links.js` | 论文、代码、补充材料的公开链接 |
| `assets/js/site.js` | 场景切换、图像查看器、复制与导航交互 |
| `assets/data/results.json` | 从当前 LaTeX 提取的实验数据与源文件校验值 |
| `assets/images/sources.json` | 网页图片对应的原始图表及 SHA-256 |

按照当前约定，Paper、Code、Supplementary 均显示 **Coming soon**。发布材料后，在 `assets/js/links.js` 填入确认过的 URL 即可启用对应入口；本地 PDF 可使用 `assets/paper/文件名.pdf` 这样的相对路径。

目前引用类型为 `@unpublished`，状态为 `Manuscript in preparation`，不包含期刊、DOI 或接收信息。投稿或发表后，请同步更新页面状态和 BibTeX。

## 更新原稿图表和数据

网站运行无需 Python 依赖；以下脚本仅用于重新导出素材。图表导出需要 Pillow 和 Poppler (`pdftoppm`)；此工作环境的 `/usr/bin/python3` 已有 Pillow。

```bash
/usr/bin/python3 scripts/prepare_assets.py /home/wink/off-road-ugv/src/paper_TAI
python3 scripts/sync_results.py /home/wink/off-road-ugv/src/paper_TAI/LPG-DRL.tex
```

第一条命令将原稿 PDF 图表导出为 WebP，并生成分享预览图和素材来源记录。第二条命令从原稿的三张表中读取三种场景及消融结果，更新 `index.html` 的生成区块、图片固有尺寸及 `results.json`。脚本不修改论文原目录。

`sync_results.py` 依赖当前稿件中的标签 `tab:offroad_comparison`、`tab:scenario_ablation`、`tab:ablation_study`，会检查数据行数。修改原稿表格结构时，应同时检查脚本。

**同步脚本只更新结果表格、场景统计和图片尺寸。** 摘要、方法说明、消融柱形图及其解释、标题、作者和引用仍需在 `index.html` 中按新稿手动同步。

图像与结果的展示约定：

- Teaser 来自 `images/teaser/lpg_drl_teaser.pdf`：一条已记录轨迹叠加到单独渲染的 Gazebo 场景，两张插图为独立说明。页面保留此说明。
- 框架来自 `images/framework_redesigned/lpg_drl_framework.pdf`。
- 局部先验、奖励、训练曲线及三组轨迹均直接导出自当前稿件引用的 PDF。
- 全部九项指标按原稿呈现；最优值按列比较，包含并列值。轨迹相关指标为成功回合上的平均值。
- 实验范围为仿真，未将示例轨迹作为实机结果或整体安全性证明。

## GitHub Pages

将本目录内容提交到用于主页的 GitHub 仓库根目录，然后按 GitHub 的 [Pages 发布来源说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)，在 **Settings → Pages** 选择 **Deploy from a branch**、实际使用的分支和 **/ (root)**。

已提供 `.nojekyll`；资源使用相对路径，适合 GitHub Pages 的项目子路径。首次部署确定网址后，将 `index.html` 的 `og:image` 改成分享图的绝对 URL，并补充 `og:url` 与 canonical URL。

本次仅创建本地页面，没有推送仓库或发布网站。

## 检查

```bash
# 校验本地文件、锚点、图片尺寸和完整实验数据。
python3 scripts/check_site.py

# 可选：浏览器交互与响应式检查，需要 Playwright 和本机 Chrome。
# 先启动上面的本地预览服务。
python3 scripts/browser_check.py --url http://127.0.0.1:4173
```

字体 Inter 随页面本地托管，许可证见 `assets/fonts/OFL.txt`。页面无分析追踪、第三方脚本或外部字体请求。
