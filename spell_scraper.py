from bs4 import BeautifulSoup
import requests
import pymongo

def extract_hyperlinks(url):
    '''Searches all tables from the given URL and grabs any hyperlinks in the first column.'''

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # get all tables on the page
    tables = soup.find_all('table')
    first_column = []
    for table in tables:
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 0:
                # only want first column
                first_column.append(cells[0].find('a')['href'])

    return first_column

def parse_spell_page(url):
    """Parses the page of a spell from dnd5e.wikidot.com and returns the content in a list."""

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    paragraphs = []

    # get the name of the spell
    page_title = soup.find('div', {'class': 'page-title page-header'})
    paragraphs.append(page_title.get_text())

    page_content = soup.find('div', {'id': 'page-content'})

    # get all the details of the spell
    for p in page_content.find_all('p'):
        # if paragraph includes a newline, split them into different items
        paragraph_text = p.get_text().split('\n')
        for item in paragraph_text:
            paragraphs.append(item)

    return paragraphs

def convert_to_dict(spell):
    """Takes a list of contents from a parsed spell page from dnd5e.wikidot.com and formats
    it to a dictionary in order to input it into MongoDB."""
    spell_dict = {}
    spell_dict["Name"] = spell[0]
    spell_dict["Source"] = spell[1][8:]

    temp = spell[2].split(' ')
    # if spell is leveled
    if spell[2][0].isdigit():
        spell_dict["Level"] = spell[2][0]
        spell_dict["School"] = temp[-1].capitalize()
    # for any cantrips
    else:
        spell_dict['Level'] = '0'
        spell_dict["School"] = temp[0].capitalize()

    spell_dict["Casting Time"] = spell[3][14:]
    spell_dict["Range"] = spell[4][7:]
    spell_dict["Components"] = spell[5][12:]
    spell_dict["Duration"] = spell[6][10:]
    spell_dict["Classes"] = spell[-1][13:]

    # if spell has higher level damage
    if spell[-2].startswith("At Higher Levels"):
        spell_description = ''
        for i in range(7, len(spell)-2):
            spell_description += spell[i] + ' '
        spell_dict["Description"] = spell_description.strip()
        spell_dict["At Higher Levels"] = spell[-2][18:]
    else:
        spell_description = ''
        for i in range(7, len(spell)-1):
            spell_description += spell[i] + ' '
        spell_dict["Description"] = spell_description.strip()

    return spell_dict


if __name__ == "__main__":
    # replace CONNECTION_STRING with MongoDB Atlas URL
    client = pymongo.MongoClient(CONNECTION_STRING)
    print("Connection Successful")

    base_url = 'http://dnd5e.wikidot.com'
    table_url = 'http://dnd5e.wikidot.com/spells'

    spell_urls = extract_hyperlinks()(table_url)

    mydb = client["D&D-5E"]
    mycol = mydb["Spells"]

    for spell_url in spell_urls:
        contents = parse_spell_page(base_url + spell_url)
        data_entry = convert_to_dict(contents)
        x = mycol.insert_one(data_entry)

    client.close()