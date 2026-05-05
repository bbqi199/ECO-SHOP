"""
一键发布脚本
功能：推送所有改动到 GitHub（即使没有改动也强制推送）
用法：双击运行，或在命令行执行 python 发布更新.py
"""
import subprocess, sys, os
from datetime import datetime

# 修复Windows控制台中文输出
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 确保在正确目录（脚本所在目录）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("🚀 开始发布...\n", flush=True)

try:
    # 第一步：git add 所有改动
    print("📥 git add...", flush=True)
    subprocess.run(['git', 'add', '-A'], check=True)

    # 第二步：检查是否有改动
    result = subprocess.run(['git', 'diff', '--cached', '--quiet'])
    has_changes = result.returncode != 0

    if has_changes:
        # 有改动：正常提交
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f'更新 {now}'
        print(f"📝 git commit: {commit_msg}", flush=True)
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    else:
        # 没有改动：强制创建一个提交（空提交）
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f'强制更新 {now}'
        print("⚡ 没有检测到改动，创建空提交以强制推送...", flush=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', commit_msg], check=True)

    # 第三步：推送到 GitHub
    print("📤 推送到 GitHub...", flush=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)

    print("\n🎉 发布成功！", flush=True)
    print("   线上地址：https://bbqi199.github.io/ECO-SHOP/", flush=True)

except subprocess.CalledProcessError as e:
    print(f"\n❌ 发布失败：{e}", flush=True)

except Exception as e:
    print(f"\n❌ 未知错误：{e}", flush=True)

input('\n按回车键退出...')
