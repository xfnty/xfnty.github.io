import html
import shutil
from pathlib import Path
from threading import Thread
from datetime import datetime
from argparse import ArgumentParser
from mistletoe import Document, HtmlRenderer, span_token
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

try:
    import colorama
    colorama.just_fix_windows_console()
    COLOR_RESET = colorama.Style.RESET_ALL
    COLOR_ERROR = colorama.Fore.RED + colorama.Style.BRIGHT
except ImportError:
    COLOR_RESET = ''
    COLOR_ERROR = ''


source_dir   = Path(__file__).parent
article_dir  = source_dir / 'articles'
static_dir   = source_dir / 'static'
build_dir    = source_dir / 'build'

index_path       = build_dir / 'index.html'
index_template_path   = source_dir / 'templates' / 'index.html'
article_template_path = source_dir / 'templates' / 'article.html'
article_link_template_path = source_dir / 'templates' / 'article-link.html'


class MyHtmlRenderer(HtmlRenderer):
    def render_image(self, token: span_token.Image) -> str:
        template = '<div class="img"><img src="{}" alt="{}"></img><small>{}</small></div>'
        title = html.escape(token.title) if token.title else ''
        return template.format(token.src, self.render_to_plain(token), title)

    def render_link(self, token: span_token.Link) -> str:
        template = '<a target="_blank" href="{target}">{inner}</a>'
        return template.format(target=self.escape_url(token.target), inner=self.render_inner(token))

    def render_auto_link(self, token: span_token.AutoLink) -> str:
        template = '<a target="_blank" href="{target}">{inner}</a>'
        target = 'mailto:{}'.format(token.target) if token.mailto else self.escape_url(token.target)
        return template.format(target=target, inner=self.render_inner(token))

def create_request_handler(directory: Path):
    class handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
    return handler


def error(*args, **kwargs):
    print(COLOR_ERROR + 'error' + COLOR_RESET + ':', *args, **kwargs)
    exit(1)


def render(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace(f'{{{k}}}', v)
    return text


def create_article(url: str):
    d = article_dir / url
    d.mkdir()
    i = d / 'index.md'
    now = datetime.now()
    dt = '{month} {day}, {year}'.format(month=now.strftime('%b'), day=now.day, year=now.year)
    i.open('w').write(f"---\ntitle: Title\ndescription: Description\ndate: {dt}\n---\n\n")


def parse_article(url: str) -> (str, dict):
    p = article_dir / url / 'index.md'
    text = p.read_text()
    if not text.startswith('---\n') or text.count('---\n') < 2:
        error(f'{p.relative_to(source_dir)}: Markdown attribute list is required.')
    text = text.replace('---\n', '', 1)
    attr_text = text[:text.index('---\n')].strip()
    text = text[text.index('---\n')+4:].strip()
    pairs = (list(map(str.strip, l.split(': '))) for l in attr_text.split('\n'))
    attrs = {e[0]: e[1] for e in pairs}
    return attrs | {'url': f'/{url}', 'name': url}, text


def build():
    build_dir.mkdir(exist_ok=True)
    shutil.copytree(static_dir, build_dir, dirs_exist_ok=True)

    article_links = ''
    article_template = article_template_path.read_text()
    article_link_template = article_link_template_path.read_text()
    renderer = MyHtmlRenderer()
    for i in map(lambda p: p.name, filter(Path.is_dir, article_dir.iterdir())):
        od = build_dir / i
        od.mkdir(exist_ok=True)
        for a in filter(lambda p: 'index.md' not in p.parts, (article_dir / i).iterdir()):
            shutil.copyfile(a, od / a.name)
        attrs, text = parse_article(i)
        article_links += render(article_link_template, attrs)
        text = renderer.render(Document(text))
        (od / 'index.html').open('w').write(render(article_template, attrs | {'content': text}))

    index_path.open('w').write(render(index_template_path.read_text(), {'articles': article_links}))


def serve():
    addr = ('127.0.0.1', 8000)
    server = ThreadingHTTPServer(addr, create_request_handler(str(build_dir)))
    server_thread = Thread(target=lambda s: s.serve_forever(), args=(server,))
    server_thread.start()
    print(f'Running local web server on address http://{addr[0]}:{addr[1]}')
    try:
        input('Press ENTER or CTRL+C to exit\n')
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server_thread.join()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-s', dest='serve', action='store_true', help='Run a local web server.')
    parser.add_argument('-n', dest='url', help='Create new article with given URL.')
    args = parser.parse_args()

    if args.url:
        create_article(args.url)

    build()

    if args.serve:
        serve()
