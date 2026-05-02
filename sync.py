import json, sys, re

def run():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data.get('results'):
            print('暂无数据')
            return

        cards = ""
        for row in data['results']:
            props = row.get('properties', {})

            # 1. 安全抓取（带默认值防爆破）
            title = props.get('标题', {}).get('title', [{'plain_text': '无标题'}])[0]['plain_text'] if props.get('标题', {}).get('title') else '无标题'
            category = props.get('分类', {}).get('select', {}).get('name', '未分类') if props.get('分类', {}).get('select') else '未分类'
            
            # 修复元凶1：针对 status 类型的精准提取
            status = props.get('状态', {}).get('status', {}).get('name', '待办') if props.get('状态', {}).get('status') else '待办'
            
            url = props.get('来源链接', {}).get('url', '#') if props.get('来源链接', {}) else '#'

            # 修复元凶2：针对空感想的防御
            thought = "暂无感想"
            if props.get('感想', {}).get('rich_text'):
                thought = props['感想']['rich_text'][0]['plain_text']

            # 头图提取
            cover_img = ""
            if props.get('头图', {}).get('files'):
                img_url = props['头图']['files'][0].get('file', {}).get('url', '')
                if img_url:
                    cover_img = f'<img src="{img_url}" style="width:100%; height:200px; object-fit:cover; display:block; border-bottom:1px solid #eee;">'

            cards += f'''
            <div class="card" style="background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); position: relative; border: 1px solid #e1e4e8; transition: transform 0.2s;">
                {cover_img}
                <div class="content" style="padding: 20px;">
                    <span style="position: absolute; top: 12px; right: 12px; background: rgba(0,0,0,0.7); color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px; z-index: 10;">{category}</span>
                    <span style="font-size: 12px; color: #65676b; display: block; margin-bottom: 8px;">状态：{status}</span>
                    <h3 style="margin: 0 0 12px 0; font-size: 18px; line-height: 1.4;">{title}</h3>
                    <div style="background: #f8f9fa; padding: 12px; border-left: 4px solid #ddd; font-size: 14px; font-style: italic; color: #4b4b4b; margin-bottom: 15px;">“{thought}”</div>
                    <a href="{url}" target="_blank" style="display: inline-block; background: #000; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600;">查看原帖</a>
                </div>
            </div>
            '''

        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        new_html = re.sub(r'<div class="grid" id="content">.*?</div>',
                          f'<div class="grid" id="content">\n{cards}\n</div>',
                          html, flags=re.DOTALL)

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_html)

    except Exception as e:
        print(f'Error occurred: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run()
