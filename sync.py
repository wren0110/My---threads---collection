import json
import sys

def run():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        cards = ""
        if data.get('results'):
            for row in data['results']:
                props = row.get('properties', {})
                title = props.get('标题', {}).get('title', [{'plain_text': '无标题'}])[0]['plain_text'] if props.get('标题', {}).get('title') else '无标题'
                category = props.get('分类', {}).get('select', {}).get('name', '未分类') if props.get('分类', {}).get('select') else '未分类'
                status = props.get('状态', {}).get('status', {}).get('name', '待办') if props.get('状态', {}).get('status') else '待办'
                url = props.get('来源链接', {}).get('url', '#') if props.get('来源链接', {}) else '#'
                
                thought = "暂无感想"
                if props.get('感想', {}).get('rich_text'):
                    thought = props['感想']['rich_text'][0]['plain_text']

                cover_img = ""
                if props.get('头图', {}).get('files'):
                    img_url = props['头图']['files'][0].get('file', {}).get('url', '')
                    if img_url:
                        cover_img = f'<img src="{img_url}">'

                cards += f'''
                <div class="card">
                    {cover_img}
                    <div class="content">
                        <span class="category">{category}</span>
                        <div class="status">状态：{status}</div>
                        <h3>{title}</h3>
                        <div class="thought">“{thought}”</div>
                        <a href="{url}" target="_blank" class="link-btn">查看原帖</a>
                    </div>
                </div>
                '''
        else:
            cards = "<p style='text-align:center; width:100%;'>暂无数据</p>"

        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Threads Collection</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; padding: 20px; margin: 0; }}
        h1 {{ text-align: center; color: #1c1e21; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); position: relative; }}
        .card img {{ width: 100%; height: 180px; object-fit: cover; display: block; }}
        .content {{ padding: 16px; }}
        .category {{ position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
        .status {{ font-size: 12px; color: #65676b; margin-bottom: 8px; }}
        h3 {{ margin: 0 0 10px 0; font-size: 16px; color: #1c1e21; line-height: 1.4; }}
        .thought {{ background: #f8f9fa; padding: 10px; font-size: 13px; color: #4b4b4b; margin-bottom: 15px; border-left: 3px solid #ddd; font-style: italic; }}
        .link-btn {{ display: inline-block; background: #000; color: white; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600; }}
    </style>
</head>
<body>
    <h1>My Threads Collection</h1>
    <div class="grid">
        {cards}
    </div>
</body>
</html>'''

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_template)

    except Exception as e:
        print(f'Error occurred: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run()
