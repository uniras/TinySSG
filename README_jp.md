# TinySSG

## 概要

TinySSGは、ファイルベースルーティングのシンプルな静的サイトジェネレータです。
ページを簡単な構造のPythonコードで記述することで単純さと柔軟性を両立しています。

## インストール

```bash
pip install tinyssg
```

## 使い方

### ディレクトリ構成

以下のようにディレクトリを構成します。ディレクトリ名はオプション引数で変更可能です。

```text
  |-- pages        SSGの対象となるPythonファイルを配置します
  |-- libs         SSG・デプロイの対象にならないPythonファイルを配置します(ライブラリなど)
  |-- static       SSGの対象にならない静的ファイルを配置します(css, 画像など)
  |-- dist         SSGの結果が出力されるディレクトリです。このディレクトリの中身をWebサーバに配置することでWebサイトとして公開できます。
        |-- static  staticディレクトリはこのディレクトリにコピーされます
```

### ページの作成

`pages`ディレクトリ内にPythonファイルを作り、`TinySSGPage`クラスを継承したクラスを作成します。

```python
from tinyssg import TinySSGPage

class IndexPage(TinySSGPage):
    def query(self) -> any:
        return {
            'title': 'Index',
            'content': 'Hello, World!'
        }

    def template(self) -> str:
        return self.indent("""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8" />
              <title>{{ title }}</title>
            </head>
            <body>
              <h1>{{ title }}</h1>
              <p>{{ content }}</p>
            </body>
            </html>
        """, 0)
```

これをビルドするとPythonファイルと同じ名前のHTMLファイルが生成されます。
Pythonファイルに複数の`TinySSGPage`継承クラスを定義した場合は、Pythonファイル名がフォルダ名になり、その中のクラス名がHTMLファイル名になります。

`query`メソッドでテンプレートに渡すデータを返し、`template`メソッドでHTMLテンプレートを返します。
TinySSGは、これらのメソッドの返り値を使ってHTMLを生成します。

`query`メソッドが返すデータは、Python辞書形式またはPython辞書のリスト形式である必要があります。
辞書形式の場合はpythonファイル名またはクラス名のHTMLファイルが生成され、リスト形式の場合はPythonファイル名またはクラス名と同じディレクトリが作成され、デフォルトでは1からの数字.htmlのファイル名でHTMLファイルが生成されます。
`return`の際にタプルとしてリストと一緒にキー名を表す文字列を返すと、そのキーに対応する値をファイル名としてHTMLファイルが生成されます。

`TinySSG`はデフォルトでは単純にテンプレートの`{{ キー名 }}`で囲まれた部分を`query`メソッドの返り値である辞書のキーに対応する値で単純に置換するだけですが、
`render`メソッドをオーバーライドすることで、より複雑な処理を行うこともできます。Jinja2などのテンプレートエンジンを使うこともできます。

また、`translate`メソッドをオーバーライドすることで、レンダー後のテキストを最終的なHTMLに変換する処理を定義することもできます。
ここでmarkdownライブラリを使って変換する処理を記述すればテンプレートをHTMLではなくMarkdownで記述することができます。

それぞれページごとに定義することになりますが、単純なPythonクラスですので複数のページに適用したい場合は共通部分を定義したクラスを作成し、それを継承することでコードをコピーすることなく簡単に適用することができます。

### 開発用ローカルサーバの起動

```bash
python -m tinyssg dev
```

開発用ローカルサーバが起動します。`http://localhost:8000`にアクセスすることで生成されたHTMLを確認できます。

`pages`, `libs`, `static`ディレクトリ内のファイルを変更すると、自動的にサーバーを再起動して変更を反映します。

### HTMLの生成

```bash
python -m tinyssg gen
```

`dist`ディレクトリにHTMLファイルが生成されます。

### オプション(抜粋)

```text
usage: python -m tinyssg [--port PORT] [--page PAGE] [--static STATIC] [--lib LIB] [--input INPUT] [--output OUTPUT] [--wait WAIT] [--nolog] [--noreload] [--noopen] [--curdir CURDIR] [モード]

モード:

  起動モードを指定します(gen = HTMLファイルの生成, dev = 開発用ローカルサーバの起動)

オプション:
  --page PAGE, -p PAGE            ページファイルを入れるディレクトリ
  --static STATIC, -s STATIC      静的ファイルを入れるディレクトリ
  --lib LIB, -l LIB               ライブラリファイルを入れるディレクトリ
  --output OUTPUT, -o OUTPUT      出力先ディレクトリの指定
  --input INPUT, -i INPUT         SSGの対象にするファイルの指定(指定しなかった場合はディレクトリ内の全ファイルを対象にする)
  --port PORT, -P PORT            開発用サーバーのポート番号の指定
  --wait WAIT, -w WAIT            多重再起動を防ぐための待ち時間
  --nolog, -n                     開発用サーバーへのリクエストログを出力しない
  --noreload, -r                  開発用サーバーの自動再起動をしない
  --noopen, -N                    開発用サーバー起動時にブラウザを開かない
  --curdir CURDIR, -C CURDIR      カレントディレクトリの指定
```

## FAQ

### **Q.** テンプレートエンジンとしてjinja2を使うにはどうすればいいですか？

**A.** `render`メソッドをオーバーライドして、jinja2を使ってテンプレートをレンダリングするようにしてください。

lib/jinja2_page.py

```python
from tinyssg import TinySSGPage
from jinja2 import Template

class Jinja2Page(TinySSGPage):
    def render(self, src: str, data: dict) -> str:
        template = Template(src)
        return template.render(data)
```

pages/index.py

```python
from tinyssg import TinySSGPage
from lib.jinja2_page import Jinja2Page

class IndexPage(Jinja2Page):
    def query(self) -> any:
        return {
            'title': 'Index', 'content': 'Hello, World!'
        }

    def template(self) -> str:
        return self.indent("""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8" />
              <title>{{ title }}</title>
            </head>
            <body>
              <h1>{{ title }}</h1>
              <p>{{ content }}</p>
            </body>
            </html>
        """, 0)
```

### **Q.** テンプレートにMarkdownを使って記述するにはどうすればいいですか？

**A.** `translate`メソッドをオーバーライドして、Markdownライブラリを使ってHTMLに変換するようにしてください。

lib/markdown_page.py

```python
from tinyssg import TinySSGPage
import markdown

class MarkdownPage(TinySSGPage):
    def translate(self, basestr: str) -> str:
        return markdown.markdown(basestr)
```

pages/index.py

```python
from tinyssg import TinySSGPage
from lib.markdown_page import MarkdownPage

class IndexPage(MarkdownPage):
    def query(self) -> any:
        return {
            'title': 'Index', 'content': 'Hello, World!'
        }

    def template(self) -> str:
        return self.indent("""
            # {{ title }}

            {{ content }}

            This is **Markdown** template.
        """, 0)
```
