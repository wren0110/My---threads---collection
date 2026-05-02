import json
import sys
import re

def run():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 打印数据快照，帮我们看清结构
        if data.get('results'):
            print('--- DATA SNAPSHOT START ---')
            print(json.dumps(data['results'][0], indent=2, ensure_ascii=False))
            print('--- DATA SNAPSHOT END ---')
            
            cards = ""
            for row in data['results']:
                props = row.get('properties', {})
                # 兼容性字段提取
                title = "无标题"
                for k, v in props.items():
                    if v.get('type') == 'title' and v['title']:
                        title = v['title'][0]['plain_text']
                
                cards += f'<div class="card"><h3>{title}</h3><p>数据已抓取，等待详细排版</p></div>'
            
            with open('index.html', 'r', encoding='utf-8') as f:
                html = f.read()
            
            new_html = re.sub(r'<div class="grid" id="content">.*?</div>', 
                              f'<div class="grid" id="content">{cards}</div>', 
                              html, flags=re.DOTALL)
            
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(new_html)
        else:
            print('CHECK: Notion returned no results.')

    except Exception as e:
        print(f'Error occurred: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run()
