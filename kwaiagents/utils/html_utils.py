"""HTML processing functions"""
from __future__ import annotations

from requests.compat import urljoin
from bs4 import BeautifulSoup


def convert_bs_html_table_to_list(table):
    header = None

    # Extract header
    if table.find("<th>"):
        header = [th.text.strip() for th in table.find_all('th')]

    # Extract rows
    rows = []
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        rows.append([cell.text.strip() for cell in cells])

    if header:
        content_rows = rows
    else:
        header = rows[0]
        content_rows = rows[1:]
    return [header] + content_rows


def convert_bs_html_table_to_markdown(table):
    items = convert_bs_html_table_to_list(table)
    header = items[0]
    content_rows = items[1:]
    # Convert to markdown
    markdown = '| ' + ' | '.join(header) + ' |\n'
    markdown += '| ' + ' | '.join(['---'] * len(header)) + ' |\n'
    for row in content_rows:
        markdown += '| ' + ' | '.join(row) + ' |\n'

    return markdown


def convert_html_table_to_markdown(table_html):
    soup = BeautifulSoup(table_html, 'html.parser')
    table = soup.find('table')
    
    return convert_bs_html_table_to_markdown(table)




def extract_hyperlinks(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    """Extract hyperlinks from a BeautifulSoup object

    Args:
        soup (BeautifulSoup): The BeautifulSoup object
        base_url (str): The base URL

    Returns:
        List[Tuple[str, str]]: The extracted hyperlinks
    """
    return [
        (link.text, urljoin(base_url, link["href"]))
        for link in soup.find_all("a", href=True)
    ]


def format_hyperlinks(hyperlinks: list[tuple[str, str]]) -> list[str]:
    """Format hyperlinks to be displayed to the user

    Args:
        hyperlinks (List[Tuple[str, str]]): The hyperlinks to format

    Returns:
        List[str]: The formatted hyperlinks
    """
    return [f"{link_text} ({link_url})" for link_text, link_url in hyperlinks]
