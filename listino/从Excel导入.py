"""
从Excel模板直接导入商品数据（listino 专用版）
不经过CSV，避免数字被转成科学计数法
只操作 listino 文件夹内的文件，完全独立
"""
import openpyxl, json, re, os, sys, io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EXCEL_FILE = '商品数据导入模板.xlsx'

print(f'📂 正在读取 Excel 文件: {EXCEL_FILE}')

# 预先从 listino.html 中提取现有的 imageUrl 映射
existing_image_map = {}
if os.path.exists('listino.html'):
    with open('listino.html', encoding='utf-8') as _f:
        _html = _f.read()
    for _line in _html.splitlines():
        _line = _line.strip().rstrip(',')
        if _line.startswith('{"id":') or _line.startswith('{ "id":'):
            try:
                _obj = json.loads(_line)
                if _obj.get('imageUrl'):
                    existing_image_map[_obj['id']] = _obj['imageUrl']
            except Exception:
                _id_m = re.search(r'"id":"([^"]+)"', _line)
                _url_m = re.search(r'"imageUrl":"([^"]+)"', _line)
                if _id_m and _url_m and _url_m.group(1):
                    existing_image_map[_id_m.group(1)] = _url_m.group(1)
    print(f'📷 已读取现有图片映射：{len(existing_image_map)} 件商品有图片URL')

try:
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb['商品数据']
except Exception as e:
    print(f'❌ 无法打开Excel文件: {e}')
    print('请确保文件没有被Excel打开着！')
    input('按回车键退出...')
    sys.exit(1)

goods = []
row_num = 0
for row in ws.iter_rows(min_row=2):
    row_num += 1
    if row_num % 5000 == 0:
        print(f'  已读取 {row_num} 行...')

    # A=0(编号), B=1(分类), C=2(名称), D=3(规格), E=4(单价), F=5(单位), G=6(库存)
    # H=7(标签), I=8(图标), J=9(规格选项), K=10(属性), L=11(图片)
    id_cell = row[0]
    id_val = str(id_cell.value).strip() if id_cell.value is not None else ''
    if '.' in id_val:
        id_val = id_val.rstrip('0').rstrip('.')
    if not id_val or id_val == 'None' or '必填' in id_val or id_val.startswith('例：'):
        continue

    tags = []
    if row[7].value:
        tags = [t.strip() for t in str(row[7].value).split(',') if t.strip()]

    specs = []
    if row[9].value:
        specs = [s.strip() for s in str(row[9].value).split('|') if s.strip()]

    attrs = {}
    if row[10].value:
        for pair in str(row[10].value).split('|'):
            if ':' in pair:
                k, v = pair.split(':', 1)
                attrs[k.strip()] = v.strip()

    img = str(row[11].value).strip() if row[11].value else ''
    img = img.replace('/images/', 'images/')
    if not img and id_val in existing_image_map:
        img = existing_image_map[id_val]

    try:
        cat_id = int(float(row[1].value)) if row[1].value else 0
    except:
        cat_id = 0

    try:
        price = float(row[4].value) if row[4].value else 0
    except:
        price = 0

    try:
        stock = int(float(row[6].value)) if row[6].value else 999
    except:
        stock = 999

    g = {
        'id':       id_val,
        'catId':    cat_id,
        'emoji':    str(row[8].value).strip() if row[8].value else '📦',
        'name':     str(row[2].value).strip() if row[2].value else '',
        'spec':     str(row[3].value).strip() if row[3].value else '',
        'price':    price,
        'unit':     str(row[5].value).strip() if row[5].value else '',
        'stock':    stock,
        'tag':      tags,
        'attrs':    attrs,
        'specs':    specs,
        'imageUrl': img
    }
    goods.append(g)

wb.close()
print(f'✅ 读取完成：共 {len(goods)} 件商品')

# 写入 goods.json
lines = []
for i, g in enumerate(goods):
    comma = ',' if i < len(goods) - 1 else ''
    lines.append('  ' + json.dumps(g, ensure_ascii=False, separators=(',', ':')) + comma)
new_block = '[\n' + '\n'.join(lines) + '\n]'

with open('goods.json', 'w', encoding='utf-8') as f:
    f.write(new_block)
print(f'✅ 商品数据已写入 goods.json')

# listino.html 通过 fetch('goods.json') 加载数据，只需更新 goods.json 即可
print('✅ goods.json 已是最新，listino.html 会自动从 goods.json 加载')

print(f'\n🎉 导入完成！共 {len(goods)} 件商品')
input('\n按回车键退出...')
