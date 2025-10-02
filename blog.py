import html
import shutil
from PIL import Image
from pathlib import Path
from threading import Thread
from datetime import datetime
from pygments import highlight
from argparse import ArgumentParser
from watchdog.observers import Observer
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from watchdog.events import FileSystemEventHandler
from mistletoe import Document, HtmlRenderer, span_token, block_token
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

try:
    import colorama
    colorama.just_fix_windows_console()
    COLOR_RESET = colorama.Style.RESET_ALL
    COLOR_ERROR = colorama.Fore.RED + colorama.Style.BRIGHT
except ImportError:
    COLOR_RESET = ''
    COLOR_ERROR = ''

image_extensions = [e for e, h in Image.registered_extensions().items() if h in Image.OPEN]

source_dir   = Path(__file__).parent
content_dir  = source_dir / 'content'
article_dir  = content_dir / 'articles'
static_dir   = content_dir / 'static'
build_dir    = source_dir / 'build'

index_path       = build_dir / 'index.html'
index_template_path   = content_dir / 'templates' / 'index.html'
article_template_path = content_dir / 'templates' / 'article.html'
article_link_template_path = content_dir / 'templates' / 'article-link.html'


def info(*args, **kwargs):
    print(f'[{datetime.now()}]:', *args, **kwargs)


def error(*args, **kwargs):
    print(COLOR_ERROR + 'error' + COLOR_RESET + ':', *args, **kwargs)


class MyHtmlRenderer(HtmlRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pygments_formatter = HtmlFormatter(cssclass="code-highlight")
        self.requires_pygments = False
        self.heading_counter = 0
        self.headings = []

    def get_index(self):
        return ''
        # if not self.headings:
        #     return ''
        # items = [f'<li><a href="#{i+1}">{h}</a></li>' for i, h in enumerate(self.headings)]
        # return f'<details><summary>Contents</summary><ul>\n\t{"\n\t".join(items)}\n</ul></details>'

    def render_heading(self, token: block_token.Heading) -> str:
        if token.level != 1:
            raise RuntimeError('Headings can only be level 1')
        template = '<h1 id="{id}">{inner}</h1>'
        heading = self.render_inner(token)
        self.heading_counter += 1
        self.headings.append(heading)
        return template.format(id=self.heading_counter, inner=heading)

    def render_block_code(self, token: block_token.BlockCode) -> str:
        inner = token.content
        if token.language:
            text = highlight(
                inner,
                get_lexer_by_name(html.escape(token.language), stripall=True),
                self.pygments_formatter
            )
            self.requires_pygments = True
        else:
            text = '<pre><code>{inner}</code></pre>'.format(inner=inner)
        return text

    def render_image(self, token: span_token.Image) -> str:
        template = '<div class="img"><img src="{}"></img><small>{}</small></div>'
        return template.format(Path(token.src).with_suffix('.webp'), self.render_inner(token))

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


def render(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace(f'{{{k}}}', v)
    return text


def create_article(url: str):
    d = article_dir / url
    if d.exists():
        error(f'"{url}" already exists.')
        return
    d.mkdir()
    i = d / 'index.md'
    now = datetime.now()
    dt = '{month} {day}, {year}'.format(month=now.strftime('%b'), day=now.day, year=now.year)
    i.open('w', errors='ignore').write(
        f"---\ntitle: Title\ndescription: Description\ndate: {dt}\n---\nlang: 'en'\n\n"
    )
    info(f'Created "{i.relative_to(content_dir)}"')


def parse_article(url: str) -> (str, dict):
    p = article_dir / url / 'index.md'
    text = p.read_text(errors='ignore')
    if not text.startswith('---\n') or text.count('---\n') < 2:
        raise RuntimeError(f'{p.relative_to(source_dir)}: Markdown attribute list is required.')
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
    article_template = article_template_path.read_text(errors='ignore')
    article_link_template = article_link_template_path.read_text(errors='ignore')
    article_ids = sorted(
        map(lambda p: p.name, filter(Path.is_dir, article_dir.iterdir())),
        key=lambda i: -datetime.strptime(parse_article(i)[0]['date'], '%b %d, %Y').timestamp()
    )
    for i in article_ids:
        info(f'Rendering "{i}" ...')
        try:
            od = build_dir / i
            od.mkdir(exist_ok=True)
            for a in filter(lambda p: 'index.md' not in p.parts, (article_dir / i).iterdir()):
                if a.suffix in image_extensions:
                    Image.open(str(a)).save((od / a.name).with_suffix('.webp'))
                else:
                    shutil.copyfile(a, od / a.name)
            attrs, text = parse_article(i)
            article_links += render(article_link_template, attrs)
            renderer = MyHtmlRenderer()
            text = renderer.render(Document(text))
            ctx = attrs | {'content': text, 'pygments': '', 'index': renderer.get_index()}
            if renderer.requires_pygments:
                ctx['pygments'] = '<link rel="stylesheet" type="text/css" href="/pygments.css">'
            (od / 'index.html').open('w', errors='ignore').write(render(article_template, ctx))
        except Exception as e:
            error(str(e))

    index_path.open('w', errors='ignore').write(
        render(index_template_path.read_text(errors='ignore'), {'articles': article_links})
    )


class FileChangedEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.event_type in ['modified', 'deleted', 'moved']:
            build()


def serve():
    addr = ('127.0.0.1', 8000)
    server = ThreadingHTTPServer(addr, create_request_handler(str(build_dir)))
    server_thread = Thread(target=lambda s: s.serve_forever(), args=(server,))
    server_thread.start()

    observer = Observer()
    observer.schedule(FileChangedEventHandler(), content_dir, recursive=True)
    observer.start()

    info(f'Running local web server on address http://{addr[0]}:{addr[1]}')
    try:
        input()
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        server.shutdown()
        server_thread.join()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-s', dest='serve', action='store_true', help='Run a local web server.')
    parser.add_argument('-n', dest='url', help='Create new article with given URL.')
    args = parser.parse_args()

    if args.url:
        create_article(args.url)
        quit()

    build()

    if args.serve:
        serve()
