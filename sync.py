import json, sys, re, os, urllib.request

def get_val(props, keywords, default=""):
    """升级版万能钥匙：支持模糊搜索和多选类型"""
    for k, val in props.items():
        if any(kw in k for kw in keywords):
            ptype = val.get('type')
            if not ptype: continue
            
            if ptype == 'title' and val['title']: return val['title'][0]['plain_text']
            if ptype == 'select' and val['select']: return val['select']['name']
            # 修复：兼容被误设为多选的情况
            if ptype == 'multi_select' and val['multi_select']: return ", ".join([x['name'] for x in val['multi_select']])
            if ptype == 'status' and val['status']: return val['status']['name']
            if ptype == 'url' and val['url']: return val['url']
            if ptype == 'rich_text' and val['rich_text']: return val['rich_text'][0]['plain_text']
    return default

def run():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data.get('results'):
            print('暂无数据')
            return

        os.makedirs('images', exist_ok=True)

        cards = ""
        carriers = set()
        domains = set()

        for row in data['results']:
            props = row.get('properties', {})
            
            # 使用更宽容的关键词阵列来抓取数据
            title = get_val(props, ['标题', 'Name'], '无标题')
            carrier = get_val(props, ['内容载体', '载体'], '未分类')
            domain = get_val(props, ['应用场景', '场景'], '无场景')
            status = get_val(props, ['行动状态', '状态'], '待办')
            location = get_val(props, ['获取途径', '位置', '地点'], '无位置信息')
            source_url = get_val(props, ['来源链接', '链接'], '#')
            thought = get_val(props, ['感想'], '暂无感想')
            remark = get_val(props, ['备注'], '')
            
            if carrier and carrier != '未分类': carriers.add(carrier)
            if domain and domain != '无场景': domains.add(domain)

            notion_url = row.get('url', '#')

            # 抓取并固化图片
            cover_img_html = ""
            if '头图' in props and props['头图'].get('files') and len(props['头图']['files']) > 0:
                file_info = props['头图']['files'][0]
                if file_info['type'] == 'file':
                    img_url = file_info['file']['url']
                    img_filename = f"images/{row['id']}.jpg"
                    try:
                        urllib.request.urlretrieve(img_url, img_filename)
                        cover_img_html = f'<img src="{img_filename}">'
                    except Exception as e:
                        print(f"图片下载失败: {e}")
                elif file_info['type'] == 'external':
                    cover_img_html = f'<img src="{file_info["external"]["url"]}">'

            # 智能判断：只有“书影音”才显示去 Notion 阅读的按钮
            notion_btn = f'<a href="{notion_url}" target="_blank" class="btn btn-primary">去 Notion 阅读</a>' if '书影音' in carrier else ''

            cards += f'''
            <div class="card" data-carrier="{carrier}" data-domain="{domain}" data-status="{status}">
                {cover_img_html}
                <div class="content">
                    <div class="tags-row">
                        <span class="tag carrier-tag">{carrier}</span>
                        <span class="tag domain-tag">{domain}</span>
                    </div>
                    <div class="status">状态：{status}</div>
                    <h3>{title}</h3>
                    <div class="thought">“{thought}”</div>
                    <div class="details">
                        {f'<p>📍 {location}</p>' if location != '无位置信息' else ''}
                        {f'<p>📝 {remark}</p>' if remark else ''}
                    </div>
                    <div class="action-buttons">
                        {notion_btn}
                        <a href="{source_url}" target="_blank" class="btn btn-outline">Threads 原帖</a>
                    </div>
                </div>
            </div>
            '''

        carrier_btns = "".join([f'<button onclick="filterCards(\'carrier\', \'{c}\')">{c}</button>' for c in carriers])
        domain_btns = "".join([f'<button onclick="filterCards(\'domain\', \'{d}\')">{d}</button>' for d in domains])

        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Threads Collection</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; padding: 20px; margin: 0; color: #1c1e21; }}
        h1 {{ text-align: center; margin-bottom: 20px; }}
        
        .filters {{ max-width: 1200px; margin: 0 auto 30px auto; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        .filter-group {{ margin-bottom: 10px; }}
        .filter-group strong {{ display: inline-block; width: 80px; font-size: 14px; }}
        .filters button {{ background: #eee; border: none; padding: 6px 12px; border-radius: 20px; margin-right: 8px; cursor: pointer; font-size: 13px; transition: 0.2s; }}
        .filters button:hover, .filters button.active {{ background: #000; color: white; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; }}
        .card img {{ width: 100%; height: 180px; object-fit: cover; display: block; border-bottom: 1px solid #eee; }}
        .content {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
        
        .tags-row {{ margin-bottom: 10px; }}
        .tag {{ padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; margin-right: 5px; }}
        .carrier-tag {{ background: #e3f2fd; color: #1565c0; }}
        .domain-tag {{ background: #fce4ec; color: #c2185b; }}
        
        .status {{ font-size: 12px; color: #65676b; margin-bottom: 10px; font-weight: 600; }}
        h3 {{ margin: 0 0 10px 0; font-size: 18px; line-height: 1.4; }}
        .thought {{ background: #f8f9fa; padding: 12px; font-size: 13px; color: #4b4b4b; margin-bottom: 15px; border-left: 3px solid #ddd; font-style: italic; }}
        .details {{ margin-bottom: 15px; flex-grow: 1; }}
        .details p {{ margin: 5px 0; font-size: 12px; color: #666; line-height: 1.5; }}
        
        .action-buttons {{ display: flex; gap: 10px; margin-top: auto; }}
        .btn {{ flex: 1; text-align: center; padding: 10px 0; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; transition: 0.2s; }}
        .btn:hover {{ opacity: 0.8; }}
        .btn-primary {{ background: #000; color: white; border: 1px solid #000; }}
        .btn-outline {{ background: white; color: #000; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>My Threads Collection</h1>
    
    <div class="filters">
        <div class="filter-group">
            <strong>复原全部：</strong>
            <button onclick="resetFilters()">显示所有</button>
        </div>
        <div class="filter-group">
            <strong>内容载体：</strong>
            {carrier_btns}
        </div>
        <div class="filter-group">
            <strong>应用场景：</strong>
            {domain_btns}
        </div>
    </div>

    <div class="grid" id="cardContainer">
        {cards}
    </div>

    <script>
        function filterCards(type, value) {{
            const cards = document.querySelectorAll('.card');
            cards.forEach(card => {{
                if (card.getAttribute('data-' + type) === value) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}

        function resetFilters() {{
            const cards = document.querySelectorAll('.card');
            cards.forEach(card => card.style.display = 'flex');
        }}
    </script>
</body>
</html>'''

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_template)

    except Exception as e:
        print(f'Error occurred: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run()
