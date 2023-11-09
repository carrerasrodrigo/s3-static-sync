import click

def log(message, current_level, log_level):
    if int(current_level) >= log_level:
        click.echo(message)
