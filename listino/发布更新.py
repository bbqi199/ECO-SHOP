"""
一键发布脚本（listino 专用版）
自动找最新CSV → 同步商品数据到 goods.json → 推送到GitHub
"""
import csv, json, re, os, glob, subprocess, sys, io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ===== 列名映射（同时支持中文列名和意大利语列名）=====
COL_MAP = {
    '商品编号':    'Codice Prodotto',
    '所属分类ID':  'ID Categoria',
    '商品名称':    'Nome Prodotto',
    '规格描述':    'Descrizione Specifiche',
    '单价':        'Prezzo Unitario',
    '计量单位':    'Unità di Misura',
    '库存数量':    'Quantità in Magazzino',
    '商品标签':    'Tag Prodotto',
    '商品图标':    'Icona Prodotto',
    '规格选项':    'Opzioni Specifiche',
    '属性键值对':  'Proprietà Chiave-Valore',
    '商品图片URL': 'URL Immagine Prodotto',
}

def col(row, zh_name, default=''):
    """取列值，自动兼容中文/意大利语列名"""
    it_name = COL_MAP.get(zh_name, zh_name)
    return row.get(zh_name, row.get(it_name, default))

# ===== 第一步：找最新的CSV文件 =====
csv_files = glob.glob('商品数据*.csv') + glob.glob('*.csv')
csv_files = [f for f in csv_files if '模板' not in f]

if not csv_files:
    print('❌ 找不到CSV文件！请先在商品管理页导出CSV。')
    input('按回车键退出...')
    sys.exit(1)

# 按修改时间取最新的
latest_csv = max(csv_files, key=os.path.getmtime)
print(f'✅ 找到CSV文件：{latest_csv}')

# ===== 第二步：读取CSV，转换商品数据 =====
goods = []
try:
    with open(latest_csv, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            spec_str = col(row, '规格选项').strip()
            specs = [s.strip() for s in spec_str.split('|') if s.strip()] if '|' in spec_str else ([spec_str] if spec_str else [])
            img = col(row, '商品图片URL').strip().replace('/images/', 'images/')
            attrs = {}
            kv = col(row, '属性键值对').strip()
            if kv:
                for pair in kv.split('|'):
                    if ':' in pair:
                        k, v = pair.split(':', 1)
                        attrs[k.strip()] = v.strip()
            try:
                cat_id = int(col(row, '所属分类ID').strip())
            except:
                cat_id = 0

            price_str = col(row, '单价').strip()
            stock_str = col(row, '库存数量').strip()
            g = {
                'id':       col(row, '商品编号').strip(),
                'catId':    cat_id,
                'emoji':    col(row, '商品图标', '📦').strip() or '📦',
                'name':     col(row, '商品名称').strip(),
                'spec':     col(row, '规格描述').strip(),
                'price':    float(price_str) if price_str else 0,
                'unit':     col(row, '计量单位').strip(),
                'stock':    int(stock_str) if stock_str else 999,
                'tag':      [t.strip() for t in col(row, '商品标签').split(',') if t.strip()],
                'attrs':    attrs,
                'specs':    specs,
                'imageUrl': img
            }
            goods.append(g)
except Exception as e:
    print(f'❌ 读取CSV出错：{e}')
    input('按回车键退出...')
    sys.exit(1)

print(f'✅ 读取商品数据：共 {len(goods)} 件商品')

# ===== 第三步：写入 goods.json =====
if not os.path.exists('goods.json'):
    print('❌ goods.json 不存在！请确保在正确目录运行。')
    input('按回车键退出...')
    sys.exit(1)

# 写入 JSON 文件
with open('goods.json', 'w', encoding='utf-8') as f:
    json.dump(goods, f, ensure_ascii=False, indent=2)

print(f'✅ 商品数据已写入 goods.json（共 {len(goods)} 件）')

# ===== 第四步：git add、commit、push =====
# 切换到仓库根目录执行 git 命令
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(repo_root, '.git')):
    os.chdir(repo_root)
    print(f'📂 切换到仓库根目录：{repo_root}')
else:
    print('⚠️ 未找到仓库根目录，在当前目录执行 git')

now = datetime.now().strftime('%Y-%m-%d %H:%M')
commit_msg = f'更新商品数据 {now}（共{len(goods)}件）'

# 需要提交的文件（相对于仓库根目录）
listino_dir = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
files_to_add = [os.path.join(listino_dir, 'goods.json'), os.path.join(listino_dir, 'listino.html')]

try:
    # add 需要发布的文件
    for f in files_to_add:
        if os.path.exists(f):
            result = subprocess.run(['git', 'add', '-f', f], capture_output=True, text=True)
            if result.returncode != 0:
                print(f'⚠️ git add {f} 失败：{result.stderr.strip()}')
            else:
                print(f'  + {f}')
        else:
            print(f'  ⚪ {f} 不存在，跳过')

    # 检查是否有变更需要提交
    status = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
    if status.returncode == 0:
        print('⚠️ 没有需要提交的变更，跳过 commit。')
    else:
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True, text=True)
        print('✅ commit 成功')

    print('📤 推送到GitHub...')
    subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True, text=True)
    print(f'\n🎉 发布成功！约1-2分钟后线上同步。')
    print(f'   线上地址：https://bbqi199.github.io/ECO-SHOP/{listino_dir}/listino.html')
except subprocess.CalledProcessError as e:
    print(f'❌ git操作失败：{e}')
    if e.stderr:
        print(f'   详情：{e.stderr.strip()}')

input('\n按回车键退出...')
