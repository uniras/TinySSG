# TinySSG

## 概要

TinySSGは、ファイルベースルーティングのシンプルな静的サイトジェネレータです。
ページを簡単な構造のTinySSGPageクラスを継承したPythonコードで記述することで単純さと柔軟性を両立しています。

## インストール

```bash
pip install tinyssg
```

## 使い方

### ディレクトリ構成

以下のようにディレクトリを構成します。ディレクトリ名はオプション引数で変更可能です。

```text
--- proect
    |-- pages        SSGの対象となるPythonファイルを配置します
    |-- libs         SSG・デプロイの対象にならないPythonファイルを配置します(ライブラリなど)
    |-- static       SSGの対象にならない静的ファイルを配置します(css, 画像など)
    |-- dist         SSGの結果が出力されるディレクトリです。このディレクトリの中身をWebサーバに配置することでWebサイトとして公開できます。
         |-- static  staticディレクトリはこのディレクトリにコピーされます
```

pages, libs, staticディレクトリは、開発サーバー起動時に監視され、ファイルが変更されると自動的にサーバーを再起動します。

### ページの作成

`Page`ディレクトリ内にPythonファイルを作り、`TinySSGPage`クラスを継承したクラスを作成します。

```python
from tinyssg import TinySSGPage

class IndexPage(TinySSGPage):
    def query(self):
        return {
            'title': 'Index',
            'content': 'Hello, World!'
        }

    def template(self):
        return '''
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
</html>'''
```

`query`メソッドでテンプレートに渡すデータを返し、`template`メソッドでHTMLテンプレートを返します。
TinySSGは、これらのメソッドの返り値を使ってHTMLを生成します。

`query`メソッドが返すデータは、Python辞書形式またはPython辞書のリスト形式である必要があります。
辞書形式の場合はpythonファイル名のHTMLファイルが生成され、リスト形式の場合はPythonファイル名と同じディレクトリが作成され、デフォルトでは1からの数字.htmlのファイル名でHTMLファイルが生成されます。
`return`の際にタプルとしてリストと一緒にキー名を表す文字列を返すと、そのキーに対応する値をファイル名としてHTMLファイルが生成されます。

`TinySSG`はデフォルトでは単純にテンプレートの`{{ キー名 }}`で囲まれた部分を`query`メソッドの返り値である辞書のキーに対応する値で単純に置換するだけですが、
`render`メソッドをオーバーライドすることで、より複雑な処理を行うこともできます。Jinja2などのテンプレートエンジンを使うこともできます。

また、`translate`メソッドをオーバーライドすることで、レンダー後のテキストを最終的なHTMLに変換する処理を定義することもできます。
ここでmarkdownライブラリを使って変換する処理を記述すればテンプレートをHTMLではなくMarkdownで記述することができます。

それぞれページごとに定義することになりますが、単純なPythonクラスですので複数のページに適用したい場合は共通部分を定義したクラスを作成し、それを継承することでコードをコピーすることなく簡単に適用することができます。

### HTMLの生成

```bash
python -m tinyssg gen
```
