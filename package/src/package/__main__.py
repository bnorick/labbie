import typer

from package import deploy
from package import package

app = typer.Typer()
app.add_typer(package.app, name='build')
app.add_typer(deploy.app, name='deploy')


def build():
    package.app()


def deploy_():
    deploy.app()


if __name__ == '__main__':
    app()
