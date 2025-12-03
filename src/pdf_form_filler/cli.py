"""
Command Line Interface for PDF Form Filler
"""
import json
import click
from .core import PDFFormFiller
from .errors import PDFFormFillerError


@click.group()
def cli():
    """PDF Form Filler - Automatically fill PDF forms"""
    pass


@cli.command()
@click.argument('input_pdf')
@click.argument('output_pdf')
@click.option('--data', '-d', help='JSON string with field data')
@click.option('--json-file', '-j', help='JSON file with field data')
@click.option('--list-fields', '-l', is_flag=True, help='List available fields and exit')
def fill(input_pdf, output_pdf, data, json_file, list_fields):
    """Fill PDF form with provided data"""
    
    try:
        # Initialize PDF filler
        filler = PDFFormFiller(input_pdf)
        
        # List fields if requested
        if list_fields:
            fields = filler.get_available_fields()
            if fields:
                click.echo("Available form fields:")
                for field in sorted(fields):
                    click.echo(f"  • {field}")
            else:
                click.echo("No form fields found in PDF")
            return
        
        # Load data
        data_dict = _load_data(data, json_file)
        if not data_dict:
            raise click.UsageError("Provide data using --data or --json-file")
        
        # Fill and save
        click.echo(f"Filling form with {len(data_dict)} fields...")
        filler.fill(data_dict)
        filler.save(output_pdf)
        
        click.echo(click.style(f"✓ Successfully filled PDF saved to: {output_pdf}", fg='green'))
        
    except PDFFormFillerError as e:
        click.echo(click.style(f"✗ Error: {e}", fg='red'), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"✗ Unexpected error: {e}", fg='red'), err=True)
        raise click.Abort()


@cli.command()
@click.argument('input_pdf')
def fields(input_pdf):
    """List all available fields in PDF form"""
    
    try:
        filler = PDFFormFiller(input_pdf)
        fields = filler.get_available_fields()
        
        if fields:
            click.echo(f"Found {len(fields)} fields in '{input_pdf}':")
            for field in sorted(fields):
                click.echo(f"  • {field}")
        else:
            click.echo(f"No form fields found in '{input_pdf}'")
            
    except PDFFormFillerError as e:
        click.echo(click.style(f"✗ Error: {e}", fg='red'), err=True)
        raise click.Abort()


def _load_data(data_str, json_file):
    """Load data from JSON string or file"""
    if data_str and json_file:
        raise click.UsageError("Use either --data or --json-file, not both")
    
    if data_str:
        try:
            return json.loads(data_str)
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON data: {e}")
    
    if json_file:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            raise click.UsageError(f"JSON file not found: {json_file}")
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON in file: {e}")
    
    return None


def main():
    """Main CLI entry point"""
    cli()


if __name__ == '__main__':
    main()
