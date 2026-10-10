#!/usr/bin/env bash
# 绿电直连工作台 · 安装脚本（可选组件）
# 用法: bash install-workbench.sh
# 作用:
#   1) 把工作台插件复制到 DSH Web profile 的 node_modules；
#   2) 在 cordis.patch.yml 注册（insert 行——工作台必须注册才会被加载，
#      仅复制文件不会出现「🌱 工作台」页签）。
# 完成后需重启 DSH 并刷新浏览器页面（见脚本末尾提示）。
set -euo pipefail

DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
WEB_PROFILE="$DSH_HOME/profiles/web"
NODE_MODULES="$WEB_PROFILE/node_modules"
PATCH="$WEB_PROFILE/cordis.patch.yml"
PKG_NAME="green-direct-workbench-v7"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/workbench/$PKG_NAME"

if [ ! -d "$SRC_DIR" ]; then
  echo "未找到工作台包：$SRC_DIR（请在发布包根目录运行本脚本）" >&2
  exit 1
fi

mkdir -p "$NODE_MODULES"
rm -rf "$NODE_MODULES/$PKG_NAME"
cp -r "$SRC_DIR" "$NODE_MODULES/$PKG_NAME"
echo "✓ 工作台包已复制到 $NODE_MODULES/$PKG_NAME"

register_entry='- insert:
    - id: green-direct-workbench
      name: '"'"''"$PKG_NAME"''"'"'
      config:
        schema: 3'

if [ -f "$PATCH" ] && grep -q "$PKG_NAME" "$PATCH"; then
  echo "✓ $PATCH 已包含 $PKG_NAME 注册（跳过写入）"
elif [ -f "$PATCH" ]; then
  printf '\n# 绿电直连 · 项目工作台（green-direct 预设的会话可见）\n%s\n' "$register_entry" >> "$PATCH"
  echo "✓ 已注册到现有 $PATCH"
else
  mkdir -p "$WEB_PROFILE"
  printf '# dsh profile web · patch layer（由 install-workbench.sh 生成）\n%s\n' "$register_entry" > "$PATCH"
  echo "✓ 已创建并注册 $PATCH"
fi

cat <<'TIP'

完成。最后两步（缺一不可）：
1) 重启 DSH —— 插件宿主模块按路径缓存，新装插件必须重启进程才会加载；
2) 刷新浏览器页面 —— 加载新的工作台前端包。
之后在 green-direct 会话的会话视图区会出现「🌱 工作台」页签。

提示：若把引擎安装在了非默认位置（~/green-direct-agent/green-direct），
需给 DSH 进程设置环境变量 GD_HOME 指向引擎目录，否则工作台读不到项目档案。
TIP
