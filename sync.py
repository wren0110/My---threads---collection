import json, sys, re, os, urllib.request

def get_val(props, keywords, default=""):
    for k, val in props.items():
        if any(kw in k for kw in keywords):
            ptype = val.get('type')
            if not ptype: continue
            
            if ptype == 'title' and val['title']: return val['title'][0]['plain_text']
            if ptype == 'select' and val['select']: return val['select']['name']
            if ptype == 'multi_select' and val['multi_select']: return ", ".join([x['name'] for x in val['multi_select']])
            if ptype == 'status' and val['status']: return val['status']['name']
            if ptype == 'url' and val['url']: return val['url']
            if ptype == 'rich_text' and val['rich_text']: return val['rich_text'][0]['plain_text']
    return default

def linkify(text):
    """智能识别文本中的URL，并转换为新标签页打开的超链接"""
    url_pattern = re.compile(r'(https?://[^\s]+)')
    return url_pattern.sub(r'<a href="\1" target="_blank" style="color: #1877f2; text-decoration: underline; word-break: break-all;">\1</a>', text)

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

        total_items = 0
        status_stats = {}

        for row in data['results']:
            props = row.get('properties', {})
            
            title = get_val(props, ['标题', 'Name'], '无标题')
            carrier = get_val(props, ['内容载体', '载体'], '未分类')
            domain = get_val(props, ['应用场景', '场景'], '无场景')
            status = get_val(props, ['行动状态', '状态'], '待办')
            location = get_val(props, ['获取途径', '位置', '地点'], '无位置信息')
            source_url = get_val(props, ['来源链接', '链接'], '#')
            thought = get_val(props, ['感想'], '暂无感想')
            remark = get_val(props, ['备注'], '')
            
            # 智能识别链接
            location_html = linkify(location)
            remark_html = linkify(remark)

            total_items += 1
            status_stats[status] = status_stats.get(status, 0) + 1

            if carrier and carrier != '未分类': carriers.add(carrier)
            if domain and domain != '无场景': domains.add(domain)

            notion_url = row.get('url', '#')

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
                        pass
                elif file_info['type'] == 'external':
                    cover_img_html = f'<img src="{file_info["external"]["url"]}">'

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
                    <h3 class="card-title">{title}</h3>
                    <div class="thought">“{thought}”</div>
                    <div class="details">
                        {f'<p>📍 {location_html}</p>' if location != '无位置信息' else ''}
                        {f'<p class="card-remark">📝 {remark_html}</p>' if remark else ''}
                    </div>
                    <div class="action-buttons">
                        {notion_btn}
                        <a href="{source_url}" target="_blank" class="btn btn-outline">Threads 原帖</a>
                    </div>
                </div>
            </div>
            '''

        dashboard_html = f'''
        <div class="stat-card total" onclick="toggleStatusFilter(this, null)" style="cursor: pointer;">
            <span class="stat-num">{total_items}</span>
            <span class="stat-label">总灵感数</span>
        </div>
        '''
        for s_name, s_count in status_stats.items():
            dashboard_html += f'''
            <div class="stat-card" data-status-btn="{s_name}" onclick="toggleStatusFilter(this, '{s_name}')" style="cursor: pointer;">
                <span class="stat-num">{s_count}</span>
                <span class="stat-label">{s_name}</span>
            </div>
            '''

        carrier_btns = "".join([f'<button class="filter-btn" onclick="toggleFilter(this, \'carrier\', \'{c}\')">{c}</button>' for c in carriers])
        domain_btns = "".join([f'<button class="filter-btn" onclick="toggleFilter(this, \'domain\', \'{d}\')">{d}</button>' for d in domains])

        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Threads Collection</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; padding: 20px; margin: 0; color: #1c1e21; }}
        h1 {{ text-align: center; margin-bottom: 25px; font-weight: 800; letter-spacing: -0.5px; }}
        
        .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; max-width: 1200px; margin: 0 auto 25px auto; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); text-align: center; display: flex; flex-direction: column; justify-content: center; border-bottom: 3px solid #ddd; transition: all 0.2s; }}
        .stat-card:hover {{ background: #f8f9fa; transform: translateY(-2px); }}
        .stat-card.active {{ border-bottom: 3px solid #1877f2; background: #ebf5ff; }}
        .stat-card.total.active {{ border-bottom-color: #000; background: #f0f2f5; }}
        .stat-num {{ font-size: 24px; font-weight: 800; color: #1c1e21; }}
        .stat-label {{ font-size: 12px; color: #65676b; margin-top: 4px; font-weight: 600; }}
        
        .controls-panel {{ max-width: 1200px; margin: 0 auto 30px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        .search-wrapper {{ margin-bottom: 15px; }}
        .search-input {{ width: 100%; padding: 12px 16px; border-radius: 8px; border: 1px solid #e4e6eb; font-size: 14px; box-sizing: border-box; transition: 0.2s; outline: none; }}
        .search-input:focus {{ border-color: #000; box-shadow: 0 0 0 2px rgba(0,0,0,0.05); }}
        
        .filter-group {{ margin-bottom: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }}
        .filter-group strong {{ font-size: 13px; color: #65676b; width: 75px; }}
        .controls-panel button {{ background: #f0f2f5; border: none; padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; color: #050505; transition: 0.2s; }}
        .controls-panel button:hover {{ background: #e4e6eb; }}
        .controls-panel button.active {{ background: #000; color: white; }}
        .reset-btn {{ background: #ebf5ff !important; color: #1877f2 !important; }}
        .reset-btn:hover {{ background: #e1f0ff !important; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; }}
        .card img {{ width: 100%; height: 180px; object-fit: cover; display: block; border-bottom: 1px solid #f0f2f5; }}
        .content {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
        
        .tags-row {{ margin-bottom: 12px; }}
        .tag {{ padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; margin-right: 5px; }}
        .carrier-tag {{ background: #e3f2fd; color: #1565c0; }}
        .domain-tag {{ background: #fce4ec; color: #c2185b; }}
        
        .status {{ font-size: 11px; color: #65676b; margin-bottom: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        h3 {{ margin: 0 0 10px 0; font-size: 17px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; }}
        .thought {{ background: #f8f9fa; padding: 12px; font-size: 13px; color: #4b4b4b; margin-bottom: 15px; border-left: 3px solid #ddd; font-style: italic; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; transition: max-height 0.3s; }}
        .card:hover .thought, .card:hover h3 {{ -webkit-line-clamp: unset; overflow: visible; }}
        
        .details {{ margin-bottom: 15px; flex-grow: 1; }}
        .details p {{ margin: 5px 0; font-size: 12px; color: #666; line-height: 1.5; }}
        
        .action-buttons {{ display: flex; gap: 10px; margin-top: auto; }}
        .btn {{ flex: 1; text-align: center; padding: 10px 0; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; transition: 0.2s; }}
        .btn:hover {{ opacity: 0.8; }}
        .btn-primary {{ background: #000; color: white; border: 1px solid #000; }}
        .btn-outline {{ background: white; color: #000; border: 1px solid #e4e6eb; }}
    </style>
</head>
<body>
    <h1>My Threads Collection</h1>
    
    <div class="dashboard">
        {dashboard_html}
    </div>
    
    <div class="controls-panel">
        <div class="search-wrapper">
            <input type="text" id="searchInput" class="search-input" placeholder="输入关键字，实时检索标题、感想或备注内容..." oninput="applyAllFilters()">
        </div>
        <div class="filter-group">
            <strong>功能控制：</strong>
            <button class="reset-btn" onclick="resetFilters()">重置所有过滤</button>
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
        let activeCarrier = null;
        let activeDomain = null;
        let activeStatus = null;

        function toggleStatusFilter(btn, value) {{
            const allStatCards = document.querySelectorAll('.stat-card');
            
            if (activeStatus === value) {{
                activeStatus = null;
                btn.classList.remove('active');
            }} else {{
                allStatCards.forEach(c => c.classList.remove('active'));
                activeStatus = value;
                btn.classList.add('active');
            }}
            applyAllFilters();
        }}

        function toggleFilter(btn, type, value) {{
            const siblings = btn.parentNode.querySelectorAll('button');
            
            if (type === 'carrier') {{
                if (activeCarrier === value) {{
                    activeCarrier = null;
                    btn.classList.remove('active');
                }} else {{
                    siblings.forEach(s => s.classList.remove('active'));
                    activeCarrier = value;
                    btn.classList.add('active');
                }}
            }} else if (type === 'domain') {{
                if (activeDomain === value) {{
                    activeDomain = null;
                    btn.classList.remove('active');
                }} else {{
                    siblings.forEach(s => s.classList.remove('active'));
                    activeDomain = value;
                    btn.classList.add('active');
                }}
            }}
            applyAllFilters();
        }}

        function resetFilters() {{
            activeCarrier = null;
            activeDomain = null;
            activeStatus = null;
            document.getElementById('searchInput').value = '';
            document.querySelectorAll('.controls-panel button').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.stat-card').forEach(c => c.classList.remove('active'));
            applyAllFilters();
        }}

        function applyAllFilters() {{
            const searchTxt = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.card');
            
            cards.forEach(card => {{
                const cVal = card.getAttribute('data-carrier');
                const dVal = card.getAttribute('data-domain');
                const sVal = card.getAttribute('data-status');
                
                const titleTxt = card.querySelector('.card-title').innerText.toLowerCase();
                const thoughtTxt = card.querySelector('.thought').innerText.toLowerCase();
                const remarkEl = card.querySelector('.card-remark');
                const remarkTxt = remarkEl ? remarkEl.innerText.toLowerCase() : '';
                
                const matchCarrier = !activeCarrier || cVal === activeCarrier;
                const matchDomain = !activeDomain || dVal === activeDomain;
                const matchStatus = !activeStatus || sVal === activeStatus;
                const matchSearch = !searchTxt || titleTxt.includes(searchTxt) || thoughtTxt.includes(searchTxt) || remarkTxt.includes(searchTxt);
                
                if (matchCarrier && matchDomain && matchStatus && matchSearch) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
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
