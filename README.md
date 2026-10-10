# 绿电直连智能体 · 发布包

面向业主交付的绿电直连（并网/离网）容量配置智能体：LLM 大脑（DSH agent preset）驱动固定的 Python 优化引擎，引导用户走完「项目画像 → 数据体检 → 参数确认 → 容量求解 → 校验交付」五个阶段，产出经独立校验的容量配置方案、全中文 Excel 成果工作簿与 Word 业主交付报告。

## 组成

| 部分 | 说明 | 必需 |
|---|---|---|
| `agent.cordis.yml` | 智能体大脑（DSH agent preset）：五阶段流程协议、话术规范、铁律 | 是 |
| `green-direct/` | 优化引擎（Python）：线性规划建模求解、数据体检、结果校验、Excel/Word 交付物生成 | 是 |
| `workbench/green-direct-workbench-v7/` | 项目工作台（DSH Web 插件）：结构化操作画布，可直接改参数、按按钮推进阶段 | 否（缺省时自动纯对话模式） |
| `checklists/` | 收资清单模板：智能体版（机器可读，填写后智能体自动读取并开始分析）+ 完整版（业主说明用） | 否（常规对话流程不需要） |

引擎内置两套相互独立的求解引擎（对用户仅以「天枢 / 天璇」呈现，不暴露实现细节）：

- **天枢（default）**：主引擎，成熟稳定，速度与精度均衡——**需要求解器组件与许可**
- **天璇（alternate）**：备选引擎，独立方法实现，**免许可、开箱即用**的保底引擎
- **双擎互证（dual）**：两引擎各自求解同一模型并交叉核对最优目标值，一致方可采信——需要天枢

未安装天枢组件或许可无效时：默认模式**自动降级**为天璇完成求解并在结果中明示；双擎互证模式会给出明确报错提示，不会静默降级。可随时运行 `./agent_tools/gd doctor` 自检环境状态。

## 环境要求

- [DeepSeek Harness（DSH）](https://github.com/deepseek-ai/DeepSeek-Harness)：智能体宿主（本包的 preset 与工作台插件均在其机制上运行）
- Python ≥ 3.13（conda 或 venv 均可）
- 磁盘约 1 GB（Python 环境）

## 安装（约 10 分钟）

```bash
# 0) 克隆/解压本包到任意目录，以下假设安装到 ~/green-direct-agent
cp -r green-direct-agent ~/green-direct-agent && cd ~/green-direct-agent

# 1) 创建 Python 环境（conda 示例；venv 亦可，保证 <环境>/bin/python 存在即可）
conda create -p ~/.venvs/mindopt-py313 python=3.13 -y
conda activate ~/.venvs/mindopt-py313
pip install -r requirements.txt

#    （可选，启用天枢与双擎互证）安装求解器组件：
pip install mindoptpy
#    并配置许可文件（见下节「求解器许可」）——不装也完全可用（自动天璇）。

# 2) 自检
cd green-direct && ./agent_tools/gd doctor && cd ..

# 3) 安装大脑（preset）：把包内 agent.cordis.yml 挂到 DSH 的 preset 目录，
#    并把其中的 __GD_DIRECT_HOME__ 占位符替换为引擎绝对路径
mkdir -p ~/.dsh/.agent-presets/green-direct
sed "s|__GD_DIRECT_HOME__|$HOME/green-direct-agent/green-direct|g" \
    agent.cordis.yml > ~/.dsh/.agent-presets/green-direct/agent.cordis.yml

# 4)（可选）安装工作台插件：复制 + 注册，一步完成（可重复执行，幂等）
bash install-workbench.sh
#    关键原理：工作台必须在 DSH Web profile 的 cordis.patch.yml 中注册才会被
#    加载——仅把文件复制进 node_modules 是不会出现「🌱 工作台」页签的。
#    安装后必须：重启 DSH（插件宿主模块按路径缓存）→ 刷新浏览器页面。
```

然后**新建 DSH 会话**，agent preset 选择 `green-direct`：
- 常规方式：对智能体说「开始」，走五阶段问答流程；
- **清单方式（推荐）**：把 `checklists/绿电直连项目收资清单_智能体版.xlsx` 填好后，对智能体说"我已填好收资清单"并给出文件路径——智能体自动读取、校验、生成项目配置并开始数据体检；填了 = 业主拍板，留空 = 智能体给推荐值草案。工作台未安装时智能体自动全程纯对话，功能不受影响。

## 求解器许可（重要）

天枢引擎使用的求解器组件需许可文件；**天璇引擎免许可**，本项目全部功能（含校验、Excel 工作簿、Word 报告）在天璇模式下完整可用。

- **获取**：注册 MindOpt 官方账号申请许可——免费授权的申请入口、有效期与可解问题规模限制以官方页面为准：<https://opt.aliyun.com/doc/latest/cn/html/installation/license.html>（"3.5 许可证设置"与官方首页）。本项目并网模型约 8–10 万变量，若免费授权规模不满足，需申请科研/商用授权。
- **放置**：许可文件放到 `~/mindopt/mindopt.lic`，或用环境变量 `MINDOPT_LICENSE_PATH` 指定路径（宿主进程需能读到该变量）。
- **自检**：`./agent_tools/gd doctor` 会报告组件与许可状态，并给出未就绪项的处置建议。
- **无许可的行为**：默认模式自动改用天璇并在结果载荷中明示（`engine_fallback_note`）；显式选择双擎互证时返回明确的业务错误，指引配置许可或改用天璇。

## 依赖清单

运行时（`requirements.txt`）：`pandas>=2.2`、`numpy>=1.26`、`scipy>=1.11`、`openpyxl>=3.1`、`python-docx>=1.1`。
可选（天枢/双擎）：`mindoptpy>=2.3`（另需求解器许可）。

## 自定义

- Python 环境不在默认位置时：`export GD_ENV=/path/to/env`（要求 `<env>/bin/python` 存在）。
- 引擎目录移动后：更新 preset 中的 `__GD_DIRECT_HOME__` 路径即可；`agent_tools/gd` 自身按脚本位置自定位。
- 工作台找不到引擎档案时：`export GD_HOME=<引擎绝对路径>`。

## 数据与隐私

所有项目数据、求解结果、校验报告与交付物都留在本机（引擎目录 `projects/` 与输出目录内），除 LLM 对话本身外无任何外发通道。`.gitignore` 已阻止许可文件（`*.lic`）与项目档案入库，请勿手动添加。

## 目录结构

```text
├── agent.cordis.yml        # 大脑 preset（安装时替换一次路径占位符）
├── requirements.txt
├── install-workbench.sh    # 工作台安装脚本（复制 + 注册，幂等）
├── workbench/              # 工作台插件（可选）
└── green-direct/           # 优化引擎
    ├── agent_tools/gd      # 引擎统一入口（template/inspect/solve/validate/report/doctor）
    ├── src/green_direct/   # 建模、求解、校验、Excel/Word 交付物
    ├── config/             # 默认参数与示例配置
    └── data/examples/      # 示例负荷/资源与电价数据
```

## FAQ

- **看不到「🌱 工作台」页签**：按顺序检查 ① 是否运行过 `install-workbench.sh`（仅复制文件不注册不会加载）；② `~/.dsh/profiles/web/cordis.patch.yml` 是否含 `green-direct-workbench-v7` 的 insert 行；③ 是否**重启了 DSH**——插件宿主模块按路径缓存，不重启不加载；④ 是否刷新了浏览器页面。
- **工作台与对话不互通（按钮无反应/工作台不更新）**：互通依赖工作台的宿主半（注册 workbench_open / workbench_update 工具）——它随 cordis.patch.yml 注册与 DSH 重启一起生效；确认完成上述①~④后再试。若工作台读不到项目档案，给 DSH 进程设置 `GD_HOME=<引擎绝对路径>`。
- **升级工作台代码后不生效**：插件宿主模块按路径缓存——源码变更需**换包名**（如 -v8）并同步修改 cordis.patch.yml 注册名，或直接重启 DSH。
- **doctor 全绿但求解报"许可未就绪"**：DSH 宿主进程启动早于许可配置时可能读不到 `MINDOPT_LICENSE_PATH`，重启 DSH 或改用文件默认位置 `~/mindopt/mindopt.lic`。
- **想强制只用天璇**：参数确认阶段选天璇，或 `./agent_tools/gd solve ... --solver alternate`。
- **安装后 preset 未出现在会话**：确认文件在 `~/.dsh/.agent-presets/green-direct/agent.cordis.yml`，且 YAML 内的路径占位符已全部替换（`grep __GD_DIRECT_HOME__` 应无输出）。
