#!/usr/bin/env python3
import yaml
import click

@click.group()
def cli():
    """Manage webcam configurations"""
    pass

@cli.command()
def list():
    """List all configured webcams"""
    with open('webcams.yaml', 'r') as f:
        webcams = yaml.safe_load(f)
    for resort, cams in webcams['webcams'].items():
        click.echo(f"\n{resort}:")
        for cam in cams:
            click.echo(f"  - {cam['name']}: {cam['description']}")

def get_valid_types():
    """Return list of valid webcam types"""
    return ['direct_image', 'wetmet', 'camstreamer', 'nest', 'api', 'mjpeg']

@cli.command()
@click.option('--resort', prompt=True)
@click.option('--name', prompt=True)
@click.option('--type', prompt=True, type=click.Choice(get_valid_types()))
@click.option('--url', prompt=True)
@click.option('--description', prompt=True)
def add(resort, name, type, url, description):
    """Add a new webcam"""
    with open('webcams.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    if resort not in config['webcams']:
        config['webcams'][resort] = []
    
    config['webcams'][resort].append({
        'name': name,
        'type': type,
        'url': url,
        'description': description
    })
    
    with open('webcams.yaml', 'w') as f:
        yaml.dump(config, f)

if __name__ == '__main__':
    cli() 