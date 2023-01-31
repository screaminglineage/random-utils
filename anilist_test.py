import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.align import Align
from rich.columns import Columns


RESULTS_PER_PAGE = 10      # no. of results per page
CONTROLS_BAR_TEXT = "Controls (n - next, p - prev, q - quit)"


media_query = '''
query ($id: Int) {
    Media (id: $id, type: ANIME) {
        id
        title {
            romaji
            english
        }
        type
        format
        status
        description
        startDate {
            year
            month
            day
        }
        endDate {
            year
            month
            day
        }
        season          # not needed for manga
        seasonYear          # not needed for manga
        episodes        # chapters and volumes instead for manga  
        source

        synonyms        # can be removed if not enough space
        
        genres
        averageScore
        
        tags {          # can be removed if not enough space
            name
        }
        relations {     # can be removed if not enough space
            nodes {
                title {
                    romaji
                }
            }
        }

        studios {
            nodes {
                name
                isAnimationStudio
            }
        } 
    }
}
'''

search_query = '''
query ($search: String, $page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
        pageInfo {
            total
            currentPage
            lastPage
            hasNextPage
            perPage
        }
        media (search: $search, type: ANIME) {
            id
            title {
                romaji
                english
            }
        }
    }
}
'''
URL = 'https://graphql.anilist.co'


def text_search(search_prompt, page, loading_text="Searching..."):
    variables = {
        'search': search_prompt,
        'page': page,
        'perPage': RESULTS_PER_PAGE
    }

    with Console().status(loading_text):
        response = requests.post(URL, json={'query': search_query, 'variables': variables})
    
    return response.json()


def id_search(media_id, loading_text="Loading..."):
    variables = {
        'id': media_id,
    }

    with Console().status(loading_text):
        response = requests.post(URL, json={'query': media_query, 'variables': variables})
    
    return response.json()


def table_prepare(table_title):
    search_data_table = Table(title=table_title)
    search_data_table.add_column("Sl. No.", justify="right")
    search_data_table.add_column("Title")

    return search_data_table


def errors_bar_prepare(error_text):
    return Panel(error_text, width=60, style="bold red")


def search_handler(search_prompt, console):
    controls_bar = Panel(CONTROLS_BAR_TEXT, width=60)

    search_data = text_search(search_prompt, 1, "Searching...")
    while True:
        page_info = search_data['data']['Page']['pageInfo']
        media_info = search_data['data']['Page']['media']
       
        if not media_info:
            panel = Panel("No Results Found. Press Enter to Search Again", width=60)
            console.clear()
            console.print(panel)
            console.show_cursor(False)
            input()
            console.show_cursor(True)
            return
            
        search_data_table = table_prepare(f"Page - {page_info['currentPage']}")
        for i, t in enumerate(media_info):
            search_data_table.add_row(f"{i+1}.", t["title"]["romaji"])
            
        console.clear()
        console.print(search_data_table, controls_bar)
        while True:
            p = input("Enter Option: ")
            console.clear()
            
            # quit
            if p.lower() == 'q':
                return None

            # next
            elif p.lower() == 'n':
                if page_info['hasNextPage']:
                    search_data = text_search(search_prompt,
                                               page_info['currentPage'] + 1,
                                               "Loading...")
                    break
                else:
                    console.print(search_data_table, controls_bar,
                                  errors_bar_prepare("No More Pages!"))

            # previous
            elif p.lower() == 'p':
                if page_info['currentPage'] > 1:
                    search_data = text_search(search_prompt,
                                               page_info['currentPage'] - 1,
                                               "Loading...")
                    break
                else:
                    console.print(search_data_table, controls_bar,
                                  errors_bar_prepare("Already at First Page!"))

            # Add more functionality
            else:
                if p.isdigit() and (1 <= int(p) <= 10):
                    return media_info[int(p) - 1]["id"]

                else:
                    console.print(search_data_table, controls_bar,
                                  errors_bar_prepare("No Other Options Supported As of Now"))


def get_studios(data):
    studios = ""
    for studio in data['studios']['nodes']:
        if studio['isAnimationStudio']:
            name = studio['name']
            if studios:
                name = f"{studios}, {name}"
            studios = name
    if not studios:
        studios = "UNKNOWN"
    return studios


def info_display_handler(media_data, console):
    media_data = media_data['data']['Media']
    """media_title = media_data['title']['romaji']
    media_studios = get_studios(media_data)
    media_episode_count = media_data['episodes']
    media_status = media_data['status']
    """

    media_title = Align.center(
        f"[bold underline]{media_data['title']['romaji']}")
    media_description = Markdown(media_data['description']) 
    description_panel = Panel.fit(
        media_description,
        title="Description",
        style="bold white", 
        width=int(0.8 * console.width))

    stats_table = Table("Stats")
    stats_table.add_row("A", "B")
    stats_panel = Panel.fit(stats_table, width=int(0.2 * console.width))

    columns = Columns([stats_panel, description_panel])


    console.print(media_title)
    console.print(columns)


def main():
    console = Console()
    info_display_handler(id_search(666), console)
    return 0

    while True:
        search = input("Search Anime: ").strip().lower()
        anime_id = search_handler(search, console) 
        if anime_id is None:
            print("Exiting")
            break

        

main()
