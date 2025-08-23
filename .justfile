project := `uv version | awk '{print $1}'`
version := `uv version | awk '{print $2}'`

install:
    @echo {{version}} {{project}}
    uv tool install -U dist/{{project}}-{{version}}-py3-none-any.whl

clean:
    find . -name __pycache__ -exec rm -rf {} \; -prune
    rm -f kill start stop uwsgi.ini

